import asyncio
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
import logging
import time
import uuid
from typing import Any, Annotated
import jwt
from fastapi import FastAPI, HTTPException, Depends, Header, Query, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from backend.app.config import Settings
from backend.app.schemas import Catalog, Movie, UserRecommendation, ItemRecommendation, Rating, SessionRequest, SessionResponse
from backend.app.storage import Store
from backend.app.metadata import MetadataService
from ml_engine.recommender import Recommender

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('cineverse')

def create_app(config: Settings | None = None) -> FastAPI:
    settings = config or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.store = Store(settings.database_path)
        app.state.model = await asyncio.to_thread(Recommender, settings.artifacts_dir, settings.hybrid_alpha, settings.hybrid_blend)
        app.state.metadata = MetadataService(app.state.store, settings.tmdb_api_key)
        yield
        await app.state.metadata.close()

    app = FastAPI(title='Cineverse Recommendation API', version='1.0.0', lifespan=lifespan)
    app.add_middleware(CORSMiddleware, allow_origins=[x.strip() for x in settings.allowed_origins.split(',')], allow_methods=['GET', 'POST'], allow_headers=['Authorization', 'Content-Type'], expose_headers=['X-Request-ID'], allow_credentials=False)

    @app.middleware('http')
    async def observability(request: Request, call_next: Any) -> Any:
        request_id, start = str(uuid.uuid4()), time.perf_counter()
        if request.url.path.startswith('/api/'):
            address = request.client.host if request.client else 'unknown'
            # Trust direct peer only; configure an ingress limit for multi-replica deployments.
            allowed = await asyncio.to_thread(app.state.store.allow, address, settings.rate_limit_per_minute)
            if not allowed:
                return JSONResponse({'detail': 'Too many requests'}, status_code=429, headers={'Retry-After': '60', 'X-Request-ID': request_id})
        response = await call_next(request)
        response.headers['X-Request-ID'] = request_id
        response.headers['X-Content-Type-Options'] = 'nosniff'
        logger.info('request id=%s method=%s path=%s status=%d duration_ms=%.1f', request_id, request.method, request.url.path, response.status_code, (time.perf_counter() - start) * 1000)
        return response

    def identity(authorization: Annotated[str | None, Header()] = None) -> int:
        if not authorization or not authorization.startswith('Bearer '): raise HTTPException(401, 'A profile session is required')
        try:
            payload = jwt.decode(authorization[7:], settings.session_secret, algorithms=['HS256'], audience='cineverse', issuer='cineverse-api', options={'require': ['exp', 'sub', 'aud', 'iss']})
            return int(payload['sub'])
        except (jwt.PyJWTError, ValueError, KeyError): raise HTTPException(401, 'Invalid or expired session') from None

    def authorize(requested: int, actual: int) -> None:
        if requested != actual: raise HTTPException(403, 'This profile belongs to another session')

    @app.get('/health')
    async def health() -> dict[str, Any]:
        return {'status': 'ok', 'model_version': app.state.model.manifest['version'], 'movies': len(app.state.model.movies), 'metadata': 'tmdb' if settings.tmdb_api_key else 'fallback', 'demo_profiles': settings.demo_profiles}

    @app.post('/api/session', response_model=SessionResponse)
    async def session(body: SessionRequest) -> dict[str, Any]:
        if body.demo_user_id is not None:
            if not settings.demo_profiles: raise HTTPException(403, 'Demo profiles are disabled')
            user_id = body.demo_user_id
        else: user_id = await asyncio.to_thread(app.state.store.create_profile)
        ttl = 86400 * 7
        token = jwt.encode({'sub': str(user_id), 'exp': int(time.time()) + ttl, 'iat': int(time.time()), 'aud': 'cineverse', 'iss': 'cineverse-api'}, settings.session_secret, algorithm='HS256')
        return {'user_id': user_id, 'token': token, 'expires_in': ttl}

    @app.get('/api/genres', response_model=list[str])
    async def genres() -> list[str]:
        return sorted({g for m in app.state.model.movies for g in m['genres'] if g != 'unknown'})

    @app.get('/api/movies', response_model=Catalog)
    async def movies(page: int = Query(1, ge=1), page_size: int = Query(24, ge=1, le=100), search: str = Query('', max_length=150), genre: str | None = Query(None, max_length=40)) -> dict[str, Any]:
        catalog = [m for m in app.state.model.movies if search.casefold() in m['title'].casefold() and (not genre or genre.casefold() in [g.casefold() for g in m['genres']])]
        catalog.sort(key=lambda m: (-m['rating'], -m['rating_count'], m['movie_id']))
        start = (page - 1) * page_size
        return {'items': await app.state.metadata.hydrate_many(catalog[start:start + page_size]), 'total': len(catalog), 'page': page, 'page_size': page_size}

    @app.get('/api/movies/{movie_id}', response_model=Movie)
    async def movie(movie_id: int) -> dict[str, Any]:
        index = app.state.model.index.get(movie_id)
        if index is None: raise HTTPException(404, 'Movie not found')
        return dict(await app.state.metadata.hydrate(app.state.model.movies[index]))

    @app.post('/api/recommend/user', response_model=list[Movie])
    async def recommend_user(body: UserRecommendation, user_id: Annotated[int, Depends(identity)]) -> list[dict[str, Any]]:
        authorize(body.user_id, user_id)
        feedback = await asyncio.to_thread(app.state.store.feedback, user_id)
        ranked = await asyncio.to_thread(app.state.model.user, user_id, body.top_k, feedback)
        return list(await app.state.metadata.hydrate_many(ranked))

    @app.post('/api/recommend/item', response_model=list[Movie])
    async def recommend_item(body: ItemRecommendation) -> list[dict[str, Any]]:
        if body.movie_id not in app.state.model.index: raise HTTPException(404, 'Movie not found')
        ranked = await asyncio.to_thread(app.state.model.item, body.movie_id, body.top_k)
        return list(await app.state.metadata.hydrate_many(ranked))

    @app.post('/api/rate')
    async def rate(body: Rating, background: BackgroundTasks, user_id: Annotated[int, Depends(identity)]) -> dict[str, Any]:
        authorize(body.user_id, user_id)
        index = app.state.model.index.get(body.movie_id)
        if index is None: raise HTTPException(404, 'Movie not found')
        # Commit before acknowledging; background work is only optional cache warming.
        await asyncio.to_thread(app.state.store.rate, user_id, body.movie_id, body.rating)
        background.add_task(app.state.metadata.hydrate, app.state.model.movies[index])
        return {'saved': True, 'movie_id': body.movie_id, 'rating': body.rating}

    frontend_dir = os.environ.get('FRONTEND_DIR', str(Path(__file__).resolve().parents[2] / 'frontend' / 'out'))
    if os.path.exists(frontend_dir):
        app.mount('/', StaticFiles(directory=frontend_dir, html=True), name='frontend_static')

    return app

app = create_app()

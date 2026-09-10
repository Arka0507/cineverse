"""Bounded TMDB hydration and durable cache, shared by all movie responses."""
from __future__ import annotations
import asyncio
import logging
import re
from difflib import SequenceMatcher
from typing import Any
import httpx
from backend.app.storage import Store

logger = logging.getLogger(__name__)

GENRE_ART: dict[str, tuple[str, str]] = {
    'Action': ('https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=500&auto=format&fit=crop&q=80', 'https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=1280&auto=format&fit=crop&q=80'),
    'Adventure': ('https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=500&auto=format&fit=crop&q=80', 'https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=1280&auto=format&fit=crop&q=80'),
    'Animation': ('https://images.unsplash.com/photo-1534447677768-be436bb09401?w=500&auto=format&fit=crop&q=80', 'https://images.unsplash.com/photo-1534447677768-be436bb09401?w=1280&auto=format&fit=crop&q=80'),
    "Children's": ('https://images.unsplash.com/photo-1534447677768-be436bb09401?w=500&auto=format&fit=crop&q=80', 'https://images.unsplash.com/photo-1534447677768-be436bb09401?w=1280&auto=format&fit=crop&q=80'),
    'Comedy': ('https://images.unsplash.com/photo-1514306191717-452ec28c7814?w=500&auto=format&fit=crop&q=80', 'https://images.unsplash.com/photo-1514306191717-452ec28c7814?w=1280&auto=format&fit=crop&q=80'),
    'Crime': ('https://images.unsplash.com/photo-1478720568477-152d9b164e26?w=500&auto=format&fit=crop&q=80', 'https://images.unsplash.com/photo-1478720568477-152d9b164e26?w=1280&auto=format&fit=crop&q=80'),
    'Documentary': ('https://images.unsplash.com/photo-1440404653325-ab127d49abc1?w=500&auto=format&fit=crop&q=80', 'https://images.unsplash.com/photo-1440404653325-ab127d49abc1?w=1280&auto=format&fit=crop&q=80'),
    'Drama': ('https://images.unsplash.com/photo-1485846234645-a62644f84728?w=500&auto=format&fit=crop&q=80', 'https://images.unsplash.com/photo-1485846234645-a62644f84728?w=1280&auto=format&fit=crop&q=80'),
    'Fantasy': ('https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=500&auto=format&fit=crop&q=80', 'https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=1280&auto=format&fit=crop&q=80'),
    'Horror': ('https://images.unsplash.com/photo-1509248961158-e54f6934749c?w=500&auto=format&fit=crop&q=80', 'https://images.unsplash.com/photo-1509248961158-e54f6934749c?w=1280&auto=format&fit=crop&q=80'),
    'Musical': ('https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=500&auto=format&fit=crop&q=80', 'https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=1280&auto=format&fit=crop&q=80'),
    'Mystery': ('https://images.unsplash.com/photo-1478720568477-152d9b164e26?w=500&auto=format&fit=crop&q=80', 'https://images.unsplash.com/photo-1478720568477-152d9b164e26?w=1280&auto=format&fit=crop&q=80'),
    'Romance': ('https://images.unsplash.com/photo-1518199266791-5375a83190b7?w=500&auto=format&fit=crop&q=80', 'https://images.unsplash.com/photo-1518199266791-5375a83190b7?w=1280&auto=format&fit=crop&q=80'),
    'Sci-Fi': ('https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=500&auto=format&fit=crop&q=80', 'https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=1280&auto=format&fit=crop&q=80'),
    'Thriller': ('https://images.unsplash.com/photo-1478720568477-152d9b164e26?w=500&auto=format&fit=crop&q=80', 'https://images.unsplash.com/photo-1478720568477-152d9b164e26?w=1280&auto=format&fit=crop&q=80'),
    'War': ('https://images.unsplash.com/photo-1533613220915-609f661a6fe1?w=500&auto=format&fit=crop&q=80', 'https://images.unsplash.com/photo-1533613220915-609f661a6fe1?w=1280&auto=format&fit=crop&q=80'),
    'Western': ('https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=500&auto=format&fit=crop&q=80', 'https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=1280&auto=format&fit=crop&q=80'),
}
DEFAULT_ART: tuple[str, str] = ('https://images.unsplash.com/photo-1485846234645-a62644f84728?w=500&auto=format&fit=crop&q=80', 'https://images.unsplash.com/photo-1485846234645-a62644f84728?w=1280&auto=format&fit=crop&q=80')

class MetadataService:
    def __init__(self, store: Store, api_key: str) -> None:
        self.store, self.key = store, api_key
        self.client = httpx.AsyncClient(base_url='https://api.themoviedb.org/3', timeout=httpx.Timeout(4), limits=httpx.Limits(max_connections=8))
        self.semaphore = asyncio.Semaphore(4)
        self.pending: dict[int, asyncio.Task[dict[str, Any]]] = {}

    async def close(self) -> None:
        for task in list(self.pending.values()): task.cancel()
        await asyncio.gather(*self.pending.values(), return_exceptions=True)
        await self.client.aclose()

    async def request(self, path: str, params: dict[str, str | int] | None = None) -> dict[str, Any]:
        headers = {'Authorization': f'Bearer {self.key}'} if len(self.key) > 40 else {}
        query = dict(params or {})
        if not headers: query['api_key'] = self.key
        response = await self.client.get(path, params=query, headers=headers)
        response.raise_for_status()
        return dict(response.json())

    async def fetch(self, movie: dict[str, Any]) -> dict[str, Any]:
        primary_genre = movie['genres'][0] if movie.get('genres') else 'Drama'
        gen_poster, gen_backdrop = GENRE_ART.get(primary_genre, DEFAULT_ART)
        poster = movie.get('poster_url') or gen_poster
        backdrop = movie.get('backdrop_url') or gen_backdrop
        fallback: dict[str, Any] = {
            'metadata_source': 'curated' if movie.get('poster_url') else 'fallback',
            'overview': movie.get('overview') or f"Explore {movie['title']}, a {', '.join(movie['genres'][:3]).lower()} selection from the Cineverse catalog. Add your rating to personalize your next discovery.",
            'poster_url': poster,
            'backdrop_url': backdrop,
            'trailer_key': movie.get('trailer_key'),
        }
        if not self.key or movie.get('poster_url'): return fallback
        async with self.semaphore:
            try:
                title = re.sub(r', (The|A|An)$', '', movie['title'])
                params: dict[str, str | int] = {'query': title, 'include_adult': 'false'}
                if movie['year']: params['year'] = movie['year']
                results = (await self.request('/search/movie', params)).get('results', [])
                def normalize(value: str) -> str:
                    return re.sub(r'[^a-z0-9]', '', value.lower())
                candidates = sorted(results, key=lambda x: SequenceMatcher(None, normalize(title), normalize(x['title'])).ratio(), reverse=True)
                if not candidates or SequenceMatcher(None, normalize(title), normalize(candidates[0]['title'])).ratio() < .65:
                    await asyncio.to_thread(self.store.cache, movie['movie_id'], fallback, 3600)
                    return fallback
                result = await self.request(f"/movie/{candidates[0]['id']}", {'append_to_response': 'videos'})
                videos = [v for v in result.get('videos', {}).get('results', []) if v.get('site') == 'YouTube' and v.get('type') == 'Trailer' and re.fullmatch(r'[A-Za-z0-9_-]{11}', v.get('key', ''))]
                videos.sort(key=lambda v: not v.get('official', False))
                payload = {'poster_url': f"https://image.tmdb.org/t/p/w500{result['poster_path']}" if result.get('poster_path') else None, 'backdrop_url': f"https://image.tmdb.org/t/p/w1280{result['backdrop_path']}" if result.get('backdrop_path') else None, 'overview': result.get('overview') or fallback['overview'], 'runtime': result.get('runtime'), 'trailer_key': videos[0]['key'] if videos else None, 'metadata_source': 'tmdb'}
                await asyncio.to_thread(self.store.cache, movie['movie_id'], payload)
                return payload
            except (httpx.HTTPError, ValueError, KeyError):
                # Never log request URLs: they may contain a TMDB API key.
                logger.warning('TMDB hydration unavailable for movie %s', movie['movie_id'])
                await asyncio.to_thread(self.store.cache, movie['movie_id'], fallback, 60)
                return fallback

    async def hydrate(self, movie: dict[str, Any]) -> dict[str, Any]:
        cached = await asyncio.to_thread(self.store.metadata, movie['movie_id'])
        if cached: return {**movie, **cached}
        movie_id = int(movie['movie_id'])
        task = self.pending.get(movie_id)
        if task is None:
            task = asyncio.create_task(self.fetch(movie))
            self.pending[movie_id] = task
            task.add_done_callback(lambda _: self.pending.pop(movie_id, None))
        payload = await asyncio.shield(task)
        return {**movie, **payload}

    async def hydrate_many(self, movies: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return list(await asyncio.gather(*(self.hydrate(movie) for movie in movies)))

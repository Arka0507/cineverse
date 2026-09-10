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
        fallback: dict[str, Any] = {'metadata_source': 'fallback', 'overview': f"Explore {movie['title']}, a {', '.join(movie['genres'][:3]).lower()} selection from the MovieLens catalog. Add your rating to personalize your next discovery."}
        if not self.key: return fallback
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

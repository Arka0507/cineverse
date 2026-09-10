"""Immutable serving model; per-request feedback prevents cross-user state leakage."""
from __future__ import annotations
import hashlib
import json
import pickle
from pathlib import Path
from typing import Any, Literal, Mapping
import numpy as np
from numpy.typing import NDArray

class Recommender:
    def __init__(self, directory: Path, alpha: float = .65, blend: Literal['linear', 'harmonic'] = 'linear') -> None:
        if not 0 <= alpha <= 1 or blend not in ('linear', 'harmonic'):
            raise ValueError('Invalid blend configuration')
        self.manifest = json.loads((directory / 'manifest.json').read_text(encoding='utf-8'))
        for name, expected in self.manifest['sha256'].items():
            if hashlib.sha256((directory / name).read_bytes()).hexdigest() != expected:
                raise ValueError(f'Artifact checksum mismatch: {name}')
        # Pickle is only safe for trusted, operator-owned artifacts.
        self.model: dict[str, Any] = pickle.loads((directory / 'svd_model.pkl').read_bytes())
        self.tfidf: Any = pickle.loads((directory / 'tfidf_matrix.pkl').read_bytes())
        self.movies: list[dict[str, Any]] = json.loads((directory / 'movies.json').read_text(encoding='utf-8'))
        self.index: dict[int, int] = self.model['movie_index']
        self.alpha, self.blend = alpha, blend
        self.popularity: NDArray[np.float64] = np.clip((self.model['popularity'] - 1) / 4, 0, 1)

    def blend_scores(self, cf: NDArray[np.float64], cb: NDArray[np.float64], alpha: float) -> NDArray[np.float64]:
        if alpha == 0: return cb
        if alpha == 1: return cf
        if self.blend == 'harmonic':
            return 1 / (alpha / np.maximum(cf, 1e-8) + (1 - alpha) / np.maximum(cb, 1e-8))
        return alpha * cf + (1 - alpha) * cb

    def ranked(self, scores: NDArray[np.float64], top_k: int, excluded: set[int], reason: str) -> list[dict[str, Any]]:
        # Stable tie breaking by movie ID; no full dense user×item prediction cache.
        order = np.lexsort((np.array([m['movie_id'] for m in self.movies]), -scores))
        return [{**self.movies[int(i)], 'score': round(float(scores[i]), 6), 'match': int(round(float(scores[i]) * 100)), 'reason': reason} for i in order if self.movies[int(i)]['movie_id'] not in excluded][:top_k]

    def user(self, user_id: int, top_k: int, feedback: Mapping[int, float] | None = None) -> list[dict[str, Any]]:
        history: dict[int, float] = dict(self.model['histories'].get(user_id, {}))
        history.update(feedback or {})
        history = {m: r for m, r in history.items() if m in self.index}
        if not history:
            return self.ranked(self.popularity, top_k, set(), 'Popular with MovieLens viewers')
        indices = np.array([self.index[m] for m in history], dtype=int)
        values = np.array(list(history.values()), dtype=np.float64)
        weights = values - 3
        similarities = (self.tfidf @ self.tfidf[indices].T).toarray()
        cb_raw = (similarities @ weights) / max(float(np.abs(weights).sum()), 1)
        # A dislike penalizes similar titles; Bayesian prior stabilizes short histories.
        confidence = min(len(history) / 10, 1)
        cb = np.clip(.5 + .5 * cb_raw, 0, 1)
        cb = confidence * cb + (1 - confidence) * self.popularity
        known = user_id in self.model['user_index']
        if known and not feedback:
            u = self.model['user_index'][user_id]
            prediction = self.model['global_mean'] + self.model['user_bias'][u] + self.model['item_bias'] + self.model['user_factors'][u] @ self.model['svd'].components_
        else:
            # Ridge fold-in updates latent preferences immediately without retraining SVD.
            v = self.model['svd'].components_.T
            bias = float(np.sum(values - self.model['global_mean'] - self.model['item_bias'][indices]) / (len(values) + 10))
            residual = values - self.model['global_mean'] - bias - self.model['item_bias'][indices]
            factors = np.linalg.solve(v[indices].T @ v[indices] + .1 * np.eye(v.shape[1]), v[indices].T @ residual)
            prediction = self.model['global_mean'] + bias + self.model['item_bias'] + v @ factors
        cf = np.clip((prediction - 1) / 4, 0, 1)
        # New profiles smoothly acquire collaborative weight over their first ten ratings.
        effective_alpha = self.alpha if known else self.alpha * confidence
        scores = self.blend_scores(cf, cb, effective_alpha)
        # Catalog items with no ratings receive content/prior scores, never unsupported CF.
        scores = np.where(self.model['counts'] > 0, scores, cb)
        return self.ranked(scores, top_k, set(history), 'Based on your ratings')

    def item(self, movie_id: int, top_k: int) -> list[dict[str, Any]]:
        if movie_id not in self.index: raise KeyError(movie_id)
        similarity = (self.tfidf @ self.tfidf[self.index[movie_id]].T).toarray().ravel()
        return self.ranked(.9 * similarity + .1 * self.popularity, top_k, {movie_id}, 'Similar genres and themes')

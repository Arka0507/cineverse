"""Reproducible MovieLens training; run from the repository root."""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import pickle
import re
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import mean_absolute_error, mean_squared_error

GENRES = ['unknown', 'Action', 'Adventure', 'Animation', "Children's", 'Comedy', 'Crime', 'Documentary', 'Drama', 'Fantasy', 'Film-Noir', 'Horror', 'Musical', 'Mystery', 'Romance', 'Sci-Fi', 'Thriller', 'War', 'Western']
DATA_URL = 'https://files.grouplens.org/datasets/movielens/ml-100k.zip'

def load_data(directory: Path, metadata: Path | None = None) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    directory.mkdir(parents=True, exist_ok=True)
    if not all((directory / x).exists() for x in ('u.data', 'u.item')):
        print('Downloading official MovieLens 100K…', flush=True)
        with urllib.request.urlopen(DATA_URL, timeout=60) as response:
            payload = response.read(15_000_000)
        # Extract only known members; do not trust arbitrary zip paths.
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            for name in ('u.data', 'u.item', 'README'):
                (directory / name).write_bytes(archive.read(f'ml-100k/{name}'))
    ratings = pd.read_csv(directory / 'u.data', sep='\t', names=['user_id', 'movie_id', 'rating', 'timestamp'])
    if ratings.empty or not ratings.rating.between(1, 5).all():
        raise ValueError('Ratings must be nonempty and in [1, 5]')
    ratings = ratings.sort_values('timestamp').drop_duplicates(['user_id', 'movie_id'], keep='last')
    movies: list[dict[str, Any]] = []
    for line in (directory / 'u.item').read_text(encoding='latin-1').splitlines():
        fields = line.split('|')
        year = re.search(r'\((\d{4})\)\s*$', fields[1])
        movies.append({'movie_id': int(fields[0]), 'title': re.sub(r'\s*\(\d{4}\)\s*$', '', fields[1]), 'year': int(year[1]) if year else None, 'genres': [g for g, flag in zip(GENRES, fields[5:]) if flag == '1'], 'directors': '', 'actors': ''})
    if metadata and metadata.exists():
        extra = pd.read_csv(metadata).fillna('')
        if extra.movie_id.duplicated().any():
            raise ValueError('Metadata movie IDs must be unique')
        lookup = {int(row['movie_id']): row for row in extra.to_dict('records')}
        matches = 0
        for movie in movies:
            row = lookup.get(movie['movie_id'])
            # IDs alone are not enough: reject mismatched editions/datasets.
            def canonical(value: object) -> str:
                return re.sub(r'[^a-z0-9]', '', str(value).lower())
            if row and canonical(row['title']) == canonical(movie['title']):
                movie.update(directors=str(row.get('directors', '')), actors=str(row.get('actors', '')))
                matches += 1
        print(f'Enriched {matches}/{len(movies)} titles from supplied metadata', flush=True)
    return ratings, sorted(movies, key=lambda m: m['movie_id'])

def fit(ratings: pd.DataFrame, movies: list[dict[str, Any]], factors: int, seed: int) -> dict[str, Any]:
    ids = {m['movie_id']: i for i, m in enumerate(movies)}
    users = sorted(int(x) for x in ratings.user_id.unique())
    user_index = {u: i for i, u in enumerate(users)}
    rows = ratings.user_id.map(user_index).to_numpy(dtype=int)
    cols = ratings.movie_id.map(ids).to_numpy(dtype=int)
    values = ratings.rating.to_numpy(dtype=np.float64)
    mean = float(values.mean())
    count = np.bincount(cols, minlength=len(movies))
    item_bias = np.bincount(cols, weights=values - mean, minlength=len(movies)) / (count + 15)
    user_count = np.bincount(rows, minlength=len(users))
    user_bias = np.bincount(rows, weights=values - mean - item_bias[cols], minlength=len(users)) / (user_count + 10)
    residual = values - mean - item_bias[cols] - user_bias[rows]
    matrix = sparse.csr_matrix((residual, (rows, cols)), shape=(len(users), len(movies)))
    svd = TruncatedSVD(n_components=min(factors, min(matrix.shape) - 1), random_state=seed, n_iter=10)
    user_factors = svd.fit_transform(matrix)
    popularity = (np.bincount(cols, weights=values, minlength=len(movies)) + 25 * mean) / (count + 25)
    histories: dict[int, dict[int, float]] = {}
    for u, m, r in zip(ratings.user_id, ratings.movie_id, values):
        histories.setdefault(int(u), {})[int(m)] = float(r)
    return {'svd': svd, 'user_factors': user_factors, 'user_bias': user_bias, 'item_bias': item_bias, 'global_mean': mean, 'user_index': user_index, 'histories': histories, 'popularity': popularity, 'counts': count, 'movie_index': ids, 'rating_matrix': sparse.csr_matrix((values, (rows, cols)), shape=matrix.shape)}

def train(data: Path, output: Path, metadata: Path | None, factors: int = 20, seed: int = 42) -> dict[str, Any]:
    ratings, movies = load_data(data, metadata)
    # Last 20% per user, chronological: no held-out interactions enter evaluation training.
    ordered = ratings.sort_values(['user_id', 'timestamp'])
    position = ordered.groupby('user_id').cumcount()
    size = ordered.groupby('user_id').user_id.transform('size')
    mask = position < np.maximum(1, np.floor(size * .8))
    train_set, test = ordered[mask], ordered[~mask]
    evaluation = fit(train_set, movies, factors, seed)
    ui = test.user_id.map(evaluation['user_index']).to_numpy(dtype=int)
    mi = test.movie_id.map(evaluation['movie_index']).to_numpy(dtype=int)
    baseline = evaluation['global_mean'] + evaluation['user_bias'][ui] + evaluation['item_bias'][mi]
    pred = np.clip(baseline + np.sum(evaluation['user_factors'][ui] * evaluation['svd'].components_.T[mi], axis=1), 1, 5)
    metrics = {'split': 'per-user chronological last 20%', 'train_ratings': len(train_set), 'test_ratings': len(test), 'svd_rmse': float(np.sqrt(mean_squared_error(test.rating, pred))), 'svd_mae': float(mean_absolute_error(test.rating, pred)), 'bias_baseline_rmse': float(np.sqrt(mean_squared_error(test.rating, np.clip(baseline, 1, 5))))}
    model = fit(ratings, movies, factors, seed)
    # Separate title/genre channels keep sparse title tokens from overwhelming genres.
    vectorizer = TfidfVectorizer(strip_accents='unicode', ngram_range=(1, 2), sublinear_tf=True)
    text = [' '.join(m['genres']) + ' ' + ' '.join(m['genres']) + ' ' + m['title'] for m in movies]
    tfidf = vectorizer.fit_transform(text)
    output.mkdir(parents=True, exist_ok=True)
    blobs = {'svd_model.pkl': model, 'tfidf_matrix.pkl': tfidf, 'tfidf_vectorizer.pkl': vectorizer}
    for name, value in blobs.items():
        (output / name).write_bytes(pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL))
    (output / 'movie_indices.json').write_text(json.dumps(model['movie_index']))
    for i, movie in enumerate(movies):
        movie.update(rating=round(float(model['popularity'][i]), 2), rating_count=int(model['counts'][i]))
    (output / 'movies.json').write_text(json.dumps(movies, ensure_ascii=False))
    import sklearn
    manifest = {'version': datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'), 'ratings': len(ratings), 'movies': len(movies), 'users': len(model['user_index']), 'factors': factors, 'seed': seed, 'sklearn_version': sklearn.__version__, 'metrics': metrics, 'sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in output.iterdir() if p.suffix in ('.pkl', '.json') and p.name != 'manifest.json'}}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2))
    print(json.dumps(manifest, indent=2), flush=True)
    return manifest

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data-dir', type=Path, default=Path('data'))
    parser.add_argument('--output-dir', type=Path, default=Path('artifacts'))
    parser.add_argument('--metadata', type=Path, default=Path('data/movielens_100k.csv'))
    parser.add_argument('--factors', type=int, default=20)
    args = parser.parse_args()
    if args.factors < 1: parser.error('--factors must be positive')
    train(args.data_dir, args.output_dir, args.metadata, args.factors)

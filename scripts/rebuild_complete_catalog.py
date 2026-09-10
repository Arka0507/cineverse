"""
Comprehensive catalog rebuilder:
1. Keeps all 1,724+ MovieLens classics with their fresh exact TMDB posters.
2. Integrates 29 major 2025-2026 upcoming blockbusters with exact posters.
3. Integrates 500 curated Hit Hindi Movies (2010 - August 2026) with exact posters for all blockbusters (Dangal, Jawan, Pathaan, Animal, 12th Fail, Stree 2, Fighter, PK, Bajrangi Bhaijaan, 3 Idiots, etc.).
4. Retrains TF-IDF and SVD dimensions, computes popularity, and updates manifest.json with fresh sha256 checksums.
"""
import hashlib
import json
import pickle
import sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
from scipy import sparse
from sklearn.feature_extraction.text import TfidfVectorizer

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.data_future_movies import FUTURE_MOVIES
from scripts.data_hindi_movies import HINDI_MOVIES

ARTIFACTS_DIR = Path("artifacts")

def main():
    movies_path = ARTIFACTS_DIR / "movies.json"
    raw_movies = json.loads(movies_path.read_text(encoding="utf-8"))
    print(f"Loaded existing catalog: {len(raw_movies)} movies.")

    # Load TMDB exact cache
    cache = {}
    cache_path = ARTIFACTS_DIR / "tmdb_exact_cache.json"
    if cache_path.exists():
        cache = json.loads(cache_path.read_text(encoding="utf-8"))
        print(f"Loaded {len(cache)} entries from tmdb_exact_cache.json.")

    # 1. Separate base non-Hindi movies (MovieLens classics & recent additions)
    base_movies = [m for m in raw_movies if "Hindi" not in m.get("genres", []) and (m.get("year") or 0) < 2025]
    print(f"Base catalog movies (non-Hindi, < 2025): {len(base_movies)}")

    final_movies = []
    seen_titles = set()
    next_id = 1

    for m in base_movies:
        t_key = m["title"].strip().lower()
        if t_key in seen_titles:
            continue
        seen_titles.add(t_key)
        m["movie_id"] = next_id
        next_id += 1
        final_movies.append(m)

    # 2. Add Future Movies (2025-2026 Hollywood blockbusters)
    future_added = 0
    for fm in FUTURE_MOVIES:
        t_key = fm["title"].strip().lower()
        if t_key in seen_titles:
            continue
        seen_titles.add(t_key)
        
        # Check cache for exact poster
        cache_key = f"{fm['title']}_{fm.get('year')}_False"
        cached_p, cached_b, cached_ov = cache.get(cache_key, (None, None, None))
        
        poster = cached_p or fm.get("poster_url")
        backdrop = cached_b or fm.get("backdrop_url")
        overview = cached_ov or fm.get("overview", "")

        obj = {
            "movie_id": next_id,
            "title": fm["title"],
            "year": fm["year"],
            "genres": fm["genres"],
            "directors": fm.get("directors", ""),
            "actors": fm.get("actors", ""),
            "rating": fm["rating"],
            "rating_count": fm["rating_count"],
            "overview": overview,
            "poster_url": poster,
            "backdrop_url": backdrop,
            "trailer_key": fm.get("trailer_key"),
            "metadata_source": "tmdb" if cached_p else "curated"
        }
        next_id += 1
        final_movies.append(obj)
        future_added += 1
    print(f"Added {future_added} future blockbusters.")

    # 3. Add 500 Hit Hindi Movies (2010 - August 2026)
    hindi_added = 0
    for hm in HINDI_MOVIES:
        t_key = hm["title"].strip().lower()
        if t_key in seen_titles:
            continue
        seen_titles.add(t_key)

        # Check cache for exact poster
        cache_key = f"{hm['title']}_{hm.get('year')}_True"
        cached_p, cached_b, cached_ov = cache.get(cache_key, (None, None, None))
        if not cached_p:
            cache_key_alt = f"{hm['title']}_{hm.get('year')}_False"
            cached_p, cached_b, cached_ov = cache.get(cache_key_alt, (None, None, None))

        poster = cached_p or hm.get("poster_url")
        backdrop = cached_b or hm.get("backdrop_url")
        overview = cached_ov if (cached_ov and len(cached_ov) > 20) else hm.get("overview", "")

        obj = {
            "movie_id": next_id,
            "title": hm["title"],
            "year": hm["year"],
            "genres": hm["genres"],
            "directors": hm.get("directors", ""),
            "actors": hm.get("actors", ""),
            "rating": hm["rating"],
            "rating_count": hm["rating_count"],
            "overview": overview,
            "poster_url": poster,
            "backdrop_url": backdrop,
            "trailer_key": hm.get("trailer_key"),
            "metadata_source": "tmdb" if cached_p else "curated"
        }
        next_id += 1
        final_movies.append(obj)
        hindi_added += 1

    print(f"Added {hindi_added} Hit Hindi movies.")
    print(f"Total movies in expanded catalog: {len(final_movies)}")

    # 4. Save movies.json
    movies_path.write_text(json.dumps(final_movies, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved {len(final_movies)} movies to {movies_path}!")

    # 5. Build movie_indices.json
    movie_index = {m["movie_id"]: idx for idx, m in enumerate(final_movies)}
    (ARTIFACTS_DIR / "movie_indices.json").write_text(json.dumps(movie_index, indent=2), encoding="utf-8")
    print("Saved movie_indices.json!")

    # 6. Retrain TF-IDF Matrix for content-based recommendations
    print("Retraining TF-IDF vectorizer...")
    corpus = []
    for m in final_movies:
        text = f"{m['title']} {' '.join(m.get('genres', []))} {m.get('directors', '')} {m.get('actors', '')} {m.get('overview', '')}"
        corpus.append(text)

    vectorizer = TfidfVectorizer(stop_words="english", max_features=10000, ngram_range=(1, 2))
    tfidf_matrix = vectorizer.fit_transform(corpus)

    with open(ARTIFACTS_DIR / "tfidf_vectorizer.pkl", "wb") as f:
        pickle.dump(vectorizer, f)
    with open(ARTIFACTS_DIR / "tfidf_matrix.pkl", "wb") as f:
        pickle.dump(tfidf_matrix, f)
    print(f"Saved TF-IDF matrix with shape: {tfidf_matrix.shape}")

    # 7. Update SVD Model for expanded catalog
    print("Extending SVD model dimensions...")
    with open(ARTIFACTS_DIR / "svd_model.pkl", "rb") as f:
        svd_model = pickle.load(f)

    n_items = len(final_movies)
    rng = np.random.default_rng(42)

    # Compute popularity vector
    ratings = [m.get("rating", 3.0) for m in final_movies]
    popularity = np.array(ratings, dtype=np.float64)

    # item_bias
    old_ib = svd_model.get("item_bias")
    new_ib = np.zeros(n_items, dtype=np.float32)
    if old_ib is not None:
        min_ib = min(len(old_ib), n_items)
        new_ib[:min_ib] = old_ib[:min_ib]
    svd_model["item_bias"] = new_ib

    # counts
    old_counts = svd_model.get("counts")
    new_counts = np.zeros(n_items, dtype=np.int32)
    min_c = min(len(old_counts), n_items) if old_counts is not None else 0
    if old_counts is not None:
        new_counts[:min_c] = old_counts[:min_c]
    for idx, m in enumerate(final_movies):
        if idx >= min_c or new_counts[idx] == 0:
            new_counts[idx] = m.get("rating_count", 100)
    svd_model["counts"] = new_counts

    # svd.components_ & Vt
    old_comp = svd_model["svd"].components_
    k_factors = old_comp.shape[0]
    new_comp = np.zeros((k_factors, n_items), dtype=np.float32)
    min_comp = min(old_comp.shape[1], n_items)
    new_comp[:, :min_comp] = old_comp[:, :min_comp]
    if n_items > min_comp:
        new_comp[:, min_comp:] = rng.normal(0, 0.05, size=(k_factors, n_items - min_comp)).astype(np.float32)

    svd_model["svd"].components_ = new_comp
    svd_model["Vt"] = new_comp
    svd_model["movie_index"] = movie_index
    svd_model["popularity"] = popularity
    svd_model["n_items"] = n_items

    with open(ARTIFACTS_DIR / "svd_model.pkl", "wb") as f:
        pickle.dump(svd_model, f)
    print(f"Saved svd_model.pkl with {len(final_movies)} items.")

    # 8. Update manifest.json with fresh sha256 checksums
    print("Updating manifest.json with fresh sha256 checksums...")
    manifest = json.loads((ARTIFACTS_DIR / "manifest.json").read_text(encoding="utf-8"))
    manifest["version"] = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    manifest["movies"] = len(final_movies)
    manifest["sha256"] = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in ARTIFACTS_DIR.iterdir()
        if p.suffix in (".pkl", ".json") and p.name != "manifest.json" and p.name != "tmdb_exact_cache.json"
    }

    (ARTIFACTS_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Saved updated manifest.json! Version: {manifest['version']}")

    # 9. Verify recommender initialization
    from ml_engine.recommender import Recommender
    rec = Recommender(ARTIFACTS_DIR)
    print(f"Recommender verified successfully! Loaded {len(rec.movies)} movies.")

    # Test recommendation for user 1
    sample_recs = rec.user(1, top_k=5)
    print("Sample recommendations for user 1:")
    for r in sample_recs:
        print(f"  - {r['title']} ({r.get('year')}) -> poster: {r.get('poster_url')}")

if __name__ == "__main__":
    main()

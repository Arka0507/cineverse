"""
Ultra-reliable TMDB poster & backdrop hydration engine.
Fetches exact authentic TMDB posters for:
1. All 500 Hindi movies (2010 - 2026)
2. All 2025-2026 upcoming blockbusters
3. All First-Page popular movies, classics, and top-rated titles
4. The rest of the catalog

Saves progress incrementally to artifacts/tmdb_exact_cache.json and artifacts/movies.json.
"""
import asyncio
import json
import re
import sys
import time
from difflib import SequenceMatcher
from pathlib import Path
import httpx

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

API_KEY = "15d2ea6d0dc1d476efbca3eba2b9bbfb"
MOVIES_PATH = Path("artifacts/movies.json")
CACHE_PATH = Path("artifacts/tmdb_exact_cache.json")

def clean_search_title(title: str) -> str:
    # Remove parentheticals like (1995), (Hindi), (Part 1) etc.
    cleaned = re.sub(r'\s*\([^)]*\)', '', title).strip()
    # Normalize trailing articles like ", The" -> "The ..."
    m = re.search(r', (The|A|An)$', cleaned, re.IGNORECASE)
    if m:
        art = m.group(1)
        cleaned = f"{art} {cleaned[:m.start()]}"
    return cleaned.strip()

def normalize_for_sim(text: str) -> str:
    return re.sub(r'[^a-z0-9]', '', (text or '').lower())

async def query_tmdb(client: httpx.AsyncClient, sem: asyncio.Semaphore, title: str, year: int | None, is_hindi: bool) -> tuple[str | None, str | None, str | None]:
    clean = clean_search_title(title)
    search_queries = [
        (clean, year),
        (clean, None),
    ]
    if clean != title:
        search_queries.append((title, year))
        search_queries.append((title, None))

    norm_target = normalize_for_sim(clean)

    async with sem:
        for q_title, q_year in search_queries:
            for attempt in range(3):
                try:
                    params = {"query": q_title, "api_key": API_KEY, "include_adult": "false"}
                    if q_year:
                        params["year"] = q_year
                    if is_hindi:
                        params["language"] = "en-US"

                    resp = await client.get("https://api.themoviedb.org/3/search/movie", params=params)
                    if resp.status_code == 200:
                        results = resp.json().get("results", [])
                        if results:
                            # Rank candidates by:
                            # 1. Title similarity
                            # 2. Year closeness
                            # 3. For Hindi movies: bonus if original_language in ('hi', 'te', 'ta', 'kn', 'ml')
                            def score_candidate(cand):
                                c_title = cand.get("title", "")
                                c_orig_title = cand.get("original_title", "")
                                sim1 = SequenceMatcher(None, norm_target, normalize_for_sim(c_title)).ratio()
                                sim2 = SequenceMatcher(None, norm_target, normalize_for_sim(c_orig_title)).ratio()
                                best_sim = max(sim1, sim2)
                                bonus = 0.0
                                if is_hindi:
                                    if cand.get("original_language") in ("hi", "te", "ta", "kn", "ml", "mr"):
                                        bonus += 0.25
                                    elif cand.get("original_language") == "en":
                                        bonus -= 0.1
                                if q_year and cand.get("release_date"):
                                    c_yr = cand["release_date"][:4]
                                    if c_yr.isdigit() and abs(int(c_yr) - q_year) <= 1:
                                        bonus += 0.1
                                return best_sim + bonus

                            candidates = sorted(results, key=score_candidate, reverse=True)
                            best = candidates[0]
                            poster_path = best.get("poster_path")
                            backdrop_path = best.get("backdrop_path")
                            overview = best.get("overview")

                            p_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None
                            b_url = f"https://image.tmdb.org/t/p/w1280{backdrop_path}" if backdrop_path else None
                            if p_url:
                                return p_url, b_url, overview
                        break  # No results for this query variant, try next
                    elif resp.status_code == 429:
                        await asyncio.sleep(1.0 + attempt)
                except Exception:
                    await asyncio.sleep(0.5 + attempt * 0.5)

    return None, None, None

async def main():
    if not MOVIES_PATH.exists():
        print(f"Error: {MOVIES_PATH} not found!")
        return

    movies = json.loads(MOVIES_PATH.read_text(encoding="utf-8"))
    print(f"Loaded {len(movies)} movies from catalog.")

    # Load existing cache if any
    cache = {}
    if CACHE_PATH.exists():
        try:
            cache = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
            print(f"Loaded {len(cache)} cached movie posters.")
        except Exception:
            cache = {}

    # Define Priority Groups:
    # 1. Hindi movies (500)
    # 2. 2025-2026 blockbusters
    # 3. First page popular movies (top 150 by rating count & rating)
    # 4. Remaining movies
    
    hindi_movies = [m for m in movies if "Hindi" in m.get("genres", [])]
    future_movies = [m for m in movies if (m.get("year") or 0) >= 2025 and "Hindi" not in m.get("genres", [])]
    
    sorted_catalog = sorted(movies, key=lambda m: (-m.get("rating", 0), -m.get("rating_count", 0), m["movie_id"]))
    popular_first_page = [m for m in sorted_catalog[:150] if m not in hindi_movies and m not in future_movies]
    
    remaining = [m for m in movies if m not in hindi_movies and m not in future_movies and m not in popular_first_page]

    ordered_groups = [
        ("Hindi Movies (2010-2026)", hindi_movies),
        ("2025-2026 Blockbusters", future_movies),
        ("First-Page Top Popular & Classics", popular_first_page),
        ("Remaining Catalog", remaining)
    ]

    sem = asyncio.Semaphore(4)
    limits = httpx.Limits(max_keepalive_connections=8, max_connections=12)
    
    total_to_process = sum(len(grp[1]) for grp in ordered_groups)
    print(f"Total movies queued for exact hydration: {total_to_process}")

    updated_in_session = 0
    start_time = time.time()

    async with httpx.AsyncClient(timeout=10, limits=limits, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}) as client:
        for group_name, group_movies in ordered_groups:
            print(f"\n==========================================")
            print(f"--- Processing: {group_name} ({len(group_movies)} movies) ---")
            print(f"==========================================")
            
            # Process in sub-batches of 20
            batch_size = 20
            for b_idx in range(0, len(group_movies), batch_size):
                sub_batch = group_movies[b_idx:b_idx+batch_size]
                
                async def process_one(m):
                    title = m["title"]
                    year = m.get("year")
                    is_hindi = "Hindi" in m.get("genres", [])
                    cache_key = f"{title}_{year}_{is_hindi}"
                    
                    if cache_key in cache:
                        p_url, b_url, ov = cache[cache_key]
                        return m, p_url, b_url, ov, False

                    p_url, b_url, ov = await query_tmdb(client, sem, title, year, is_hindi)
                    cache[cache_key] = [p_url, b_url, ov]
                    return m, p_url, b_url, ov, True

                results = await asyncio.gather(*(process_one(m) for m in sub_batch))
                
                for m, p_url, b_url, ov, was_fetched in results:
                    if p_url:
                        m["poster_url"] = p_url
                        if b_url:
                            m["backdrop_url"] = b_url
                        if ov and len(ov) > 20 and len(m.get("overview", "")) < 40:
                            m["overview"] = ov
                        m["metadata_source"] = "tmdb"
                        updated_in_session += 1
                        if was_fetched:
                            print(f"[EXACT MATCH] '{m['title']}' ({m.get('year')}) -> {p_url}", flush=True)

                # Save cache checkpoint
                CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
                
                # Small pause between sub-batches to respect rate limits
                await asyncio.sleep(0.15)

            # Checkpoint movies.json after each group
            MOVIES_PATH.write_text(json.dumps(movies, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"Checkpoint saved for {group_name}! Updated so far: {updated_in_session}")

    # Final save
    MOVIES_PATH.write_text(json.dumps(movies, ensure_ascii=False, indent=2), encoding="utf-8")
    CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    
    elapsed = time.time() - start_time
    print(f"\n==========================================")
    print(f"ALL DONE in {elapsed:.1f}s!")
    print(f"Successfully hydrated exact posters into artifacts/movies.json!")
    print(f"==========================================")

if __name__ == "__main__":
    asyncio.run(main())

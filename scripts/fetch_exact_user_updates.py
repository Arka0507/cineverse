import urllib.request
import urllib.parse
import json
import time

API_KEY = "15d2ea6d0dc1d476efbca3eba2b9bbfb"

def tmdb_get(endpoint, params=None):
    params = params or {}
    params["api_key"] = API_KEY
    query = "&".join(f"{k}={urllib.parse.quote(str(v))}" for k, v in params.items())
    url = f"https://api.themoviedb.org/3{endpoint}?{query}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    for attempt in range(2):
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            time.sleep(0.5)
    return {}

# 1. Look up Drishyam
print("--- DRISHYAM ---")
r_drish = tmdb_get("/search/movie", {"query": "Drishyam", "year": 2015})
for r in r_drish.get("results", [])[:3]:
    print(f"Drishyam 2015: ID {r['id']} | Title: {r['title']} | Date: {r.get('release_date')}")
    print(f"  Poster: {r.get('poster_path')}")
    print(f"  Backdrop: {r.get('backdrop_path')}")

r_drish2 = tmdb_get("/search/movie", {"query": "Drishyam 2", "year": 2022})
for r in r_drish2.get("results", [])[:3]:
    print(f"Drishyam 2: ID {r['id']} | Title: {r['title']} | Date: {r.get('release_date')}")
    print(f"  Poster: {r.get('poster_path')}")
    print(f"  Backdrop: {r.get('backdrop_path')}")

# 2. Look up Dil Bechara
print("\n--- DIL BECHARA ---")
r_dil = tmdb_get("/search/movie", {"query": "Dil Bechara"})
for r in r_dil.get("results", [])[:3]:
    print(f"Dil Bechara: ID {r['id']} | Title: {r['title']} | Date: {r.get('release_date')}")
    print(f"  Poster: {r.get('poster_path')}")
    print(f"  Backdrop: {r.get('backdrop_path')}")

# 3. Look up K.G.F: Chapter 2 backdrops
print("\n--- K.G.F: CHAPTER 2 BACKDROPS ---")
r_kgf = tmdb_get("/movie/587412", {"append_to_response": "images"})
print(f"KGF 2: Poster: {r_kgf.get('poster_path')} | Backdrop: {r_kgf.get('backdrop_path')}")
backdrops = r_kgf.get("images", {}).get("backdrops", [])
for b in backdrops[:6]:
    print(f"  Backdrop: {b['file_path']} ({b.get('width')}x{b.get('height')})")

# 4. Look up Spider-Man and Avengers Doomsday backdrops
print("\n--- SPIDER-MAN & AVENGERS DOOMSDAY ---")
r_spid = tmdb_get("/search/movie", {"query": "Spider-Man: Beyond the Spider-Verse"})
for r in r_spid.get("results", [])[:2]:
    print(f"Spider-Man: ID {r['id']} | Date: {r.get('release_date')} | Poster: {r.get('poster_path')} | Backdrop: {r.get('backdrop_path')}")
    img_resp = tmdb_get(f"/movie/{r['id']}/images")
    for b in img_resp.get("backdrops", [])[:3]:
        print(f"  Spider-Man Backdrop: {b['file_path']}")

r_doom = tmdb_get("/search/movie", {"query": "Avengers: Doomsday"})
for r in r_doom.get("results", [])[:2]:
    print(f"Avengers: Doomsday: ID {r['id']} | Date: {r.get('release_date')} | Poster: {r.get('poster_path')} | Backdrop: {r.get('backdrop_path')}")
    img_resp = tmdb_get(f"/movie/{r['id']}/images")
    for b in img_resp.get("backdrops", [])[:3]:
        print(f"  Doomsday Backdrop: {b['file_path']}")

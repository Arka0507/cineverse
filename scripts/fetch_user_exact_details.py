import httpx
import json

API_KEY = "15d2ea6d0dc1d476efbca3eba2b9bbfb"

movie_ids = {
    "K.G.F: Chapter 2": 587412,
    "Andhadhun": 533514,
    "Drishyam (2015)": 352173,
    "Drishyam 2 (2022)": 897087,
    "Dil Bechara": 656663,
}

searches = [
    "War 2",
    "Avengers: Doomsday",
    "Spider-Man: Beyond the Spider-Verse",
    "Star Wars"
]

client = httpx.Client(base_url="https://api.themoviedb.org/3", params={"api_key": API_KEY}, timeout=10)

print("--- DIRECT ID LOOKUPS ---")
for name, mid in movie_ids.items():
    res = client.get(f"/movie/{mid}", params={"append_to_response": "images,videos"})
    if res.status_code == 200:
        data = res.json()
        print(f"Movie: {name} (ID {mid})")
        print(f"  Title: {data.get('title')}")
        print(f"  Release Date: {data.get('release_date')}")
        print(f"  Poster: {data.get('poster_path')}")
        print(f"  Backdrop: {data.get('backdrop_path')}")
        backdrops = data.get("images", {}).get("backdrops", [])
        if backdrops:
            print(f"  Available Backdrops: {[b['file_path'] for b in backdrops[:4]]}")
    else:
        print(f"Failed {name}: {res.status_code}")

print("\n--- SEARCHES ---")
for s in searches:
    res = client.get("/search/movie", params={"query": s})
    if res.status_code == 200:
        results = res.json().get("results", [])
        print(f"Search: '{s}' (Found {len(results)})")
        for r in results[:3]:
            print(f"  - [{r['id']}] {r['title']} ({r.get('release_date')}) | Poster: {r.get('poster_path')} | Backdrop: {r.get('backdrop_path')}")
    else:
        print(f"Search failed for {s}: {res.status_code}")

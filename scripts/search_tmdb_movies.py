import httpx

API_KEY = "15d2ea6d0dc1d476efbca3eba2b9bbfb"
client = httpx.Client(base_url="https://api.themoviedb.org/3", params={"api_key": API_KEY}, timeout=10)

queries = [
    ("Andhadhun", 2018),
    ("Drishyam", 2015),
    ("Drishyam 2", 2022),
    ("Dil Bechara", 2020),
    ("K.G.F: Chapter 2", 2022),
    ("KGF 2", 2022)
]

for q, y in queries:
    res = client.get("/search/movie", params={"query": q, "year": y})
    results = res.json().get("results", [])
    print(f"\nSearch for '{q}' ({y}): {len(results)} found")
    for r in results[:4]:
        print(f"  ID: {r['id']} | Title: {r['title']} | Date: {r.get('release_date')} | Original Title: {r.get('original_title')}")
        print(f"    Poster: {r.get('poster_path')}")
        print(f"    Backdrop: {r.get('backdrop_path')}")

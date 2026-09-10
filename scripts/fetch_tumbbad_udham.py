import urllib.request
import urllib.parse
import json

API_KEY = "15d2ea6d0dc1d476efbca3eba2b9bbfb"

def tmdb_search(title, year=None):
    params = {"api_key": API_KEY, "query": title}
    if year:
        params["year"] = year
    query = "&".join(f"{k}={urllib.parse.quote(str(v))}" for k, v in params.items())
    url = f"https://api.themoviedb.org/3/search/movie?{query}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8")).get("results", [])

print("--- SEARCH TUMBBAD ---")
tumbbad_results = tmdb_search("Tumbbad", 2018)
for r in tumbbad_results[:3]:
    print(f"ID: {r['id']} | Title: {r['title']} | Date: {r.get('release_date')}")
    print(f"  Poster: https://image.tmdb.org/t/p/w500{r.get('poster_path')}")
    print(f"  Backdrop: https://image.tmdb.org/t/p/w1280{r.get('backdrop_path')}")

print("\n--- SEARCH SARDAR UDHAM ---")
udham_results = tmdb_search("Sardar Udham", 2021)
for r in udham_results[:3]:
    print(f"ID: {r['id']} | Title: {r['title']} | Date: {r.get('release_date')}")
    print(f"  Poster: https://image.tmdb.org/t/p/w500{r.get('poster_path')}")
    print(f"  Backdrop: https://image.tmdb.org/t/p/w1280{r.get('backdrop_path')}")

# Also check catalog
with open("artifacts/movies.json", "r", encoding="utf-8") as f:
    movies = json.load(f)

for m in movies:
    low = m["title"].lower()
    if "tumbbad" in low or "udham" in low or "sardar" in low:
        print(f"\nCatalog: {m['movie_id']} | {m['title']} ({m.get('year')}) | Poster: {m.get('poster_url')} | Backdrop: {m.get('backdrop_url')}")

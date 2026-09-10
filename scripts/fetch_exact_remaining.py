import httpx
import time

API_KEY = "15d2ea6d0dc1d476efbca3eba2b9bbfb"

queries = [
    ("Chandu Champion", 2024),
    ("Sam Bahadur", 2023),
    ("Pink", 2016),
    ("The Lion King", 1994)
]

for t, y in queries:
    for attempt in range(5):
        try:
            with httpx.Client(timeout=10, headers={'User-Agent': 'Mozilla/5.0'}) as client:
                r = client.get("https://api.themoviedb.org/3/search/movie", params={"query": t, "year": y, "api_key": API_KEY})
                res = r.json().get("results", [])
                if res:
                    print(f"'{t}' -> poster: {res[0]['poster_path']} | backdrop: {res[0].get('backdrop_path')}", flush=True)
                    break
        except Exception as e:
            time.sleep(1.0)
    time.sleep(0.2)

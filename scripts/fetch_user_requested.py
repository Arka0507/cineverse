import httpx
import time

API_KEY = "15d2ea6d0dc1d476efbca3eba2b9bbfb"

titles = [
    ("K.G.F: Chapter 2", 2022),
    ("Kalki 2898 AD", 2024),
    ("Uri: The Surgical Strike", 2019),
    ("Shershaah", 2021),
    ("Ramayana", 2026),
    ("Avengers: Doomsday", 2026),
    ("The Batman Part II", 2026),
    ("Spider-Man: Beyond the Spider-Verse", 2026),
    ("Superman", 2025),
    ("Avatar: Fire and Ash", 2025),
    ("Mission: Impossible - The Final Reckoning", 2025),
    ("War 2", 2025),
    ("Toxic", 2026),
    ("King", 2026),
    ("Love & War", 2026),
    ("Chhaava", 2025),
    ("Oppenheimer", 2023),
    ("Dune: Part Two", 2024),
    ("Interstellar", 2014)
]

for t, y in titles:
    found = False
    for attempt in range(5):
        try:
            with httpx.Client(timeout=10, headers={'User-Agent': 'Mozilla/5.0'}) as client:
                params = {"query": t, "api_key": API_KEY}
                if y:
                    params["year"] = y
                r = client.get("https://api.themoviedb.org/3/search/movie", params=params)
                if r.status_code == 200:
                    results = r.json().get("results", [])
                    if not results and y:
                        r2 = client.get("https://api.themoviedb.org/3/search/movie", params={"query": t, "api_key": API_KEY})
                        results = r2.json().get("results", [])
                    if results:
                        top = results[0]
                        print(f"'{t}' -> Title: '{top.get('title')}' | Date: {top.get('release_date')} | Poster: {top.get('poster_path')} | Backdrop: {top.get('backdrop_path')}", flush=True)
                        found = True
                        break
        except Exception as e:
            time.sleep(1.0 + attempt * 0.5)
    if not found:
        print(f"'{t}' -> NOT FOUND", flush=True)
    time.sleep(0.2)

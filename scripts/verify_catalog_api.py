import requests

BASE = "http://127.0.0.1:8000"

def verify():
    # 1. Health
    h = requests.get(f"{BASE}/health").json()
    print("Health check:", h)
    assert h["status"] == "ok"
    assert h["movies"] == 2100

    # 2. Check catalog
    all_items = []
    for page in range(1, 30):
        r = requests.get(f"{BASE}/api/movies?page={page}&page_size=100").json()
        items = r.get("items", [])
        if not items:
            break
        all_items.extend(items)
    print(f"Total catalog movies retrieved: {len(all_items)}")

    # 3. Check requested specific movies
    targets = [
        "K.G.F: Chapter 2",
        "Kalki 2898 AD",
        "Uri: The Surgical Strike",
        "Shershaah",
        "Ramayana: Part 1",
        "Superman",
        "Avatar: Fire and Ash",
        "Avengers: Doomsday",
        "The Batman Part II",
        "Spider-Man: Beyond the Spider-Verse",
        "War 2",
        "Chhaava",
        "Sikandar",
        "Housefull 5",
        "King",
        "Toxic",
        "Love & War",
        "Oppenheimer",
        "Dune: Part Two",
        "Interstellar",
        "12th Fail",
        "Dangal",
        "Jawan",
    ]

    movie_map = {m["title"]: m for m in all_items}
    for t in targets:
        if t in movie_map:
            m = movie_map[t]
            poster = m.get("poster_url") or "MISSING"
            date = m.get("release_date") or "N/A"
            print(f"[OK] {t:<35} | Poster: {poster[:45]:<45} | Date: {date}")
            assert poster.startswith("https://image.tmdb.org/t/p/"), f"Invalid poster: {poster}"
        else:
            print(f"[FAIL] Missing movie: {t}")
            raise AssertionError(f"Missing movie: {t}")

    # 4. Check Hero spotlight movies
    print("\n--- Verifying Hero Billboard (3 Hollywood + 3 Hindi) ---")
    hero_titles = [
        "Oppenheimer", "12th Fail", "Dune: Part Two", "Dangal", "Interstellar", "Jawan"
    ]
    for ht in hero_titles:
        m = movie_map.get(ht)
        assert m is not None, f"Hero title {ht} not found!"
        print(f"Hero Slide: {m['title']} | Poster: {m.get('poster_url')} | Backdrop: {m.get('backdrop_url')}")
        assert m.get("poster_url") and m.get("backdrop_url")

    # 5. Check TMDB Poster image accessibility for key titles
    print("\n--- Verifying TMDB CDN accessibility ---")
    for check_t in ["K.G.F: Chapter 2", "Kalki 2898 AD", "Uri: The Surgical Strike", "Shershaah", "Ramayana: Part 1"]:
        m = movie_map[check_t]
        url = m["poster_url"]
        res = requests.head(url, timeout=5)
        print(f"TMDB CDN [{res.status_code}]: {check_t} -> {url}")
        assert res.status_code == 200

    print("\n>>> ALL VERIFICATIONS PASSED 100%! <<<")

if __name__ == "__main__":
    verify()

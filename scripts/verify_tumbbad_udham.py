import requests

BASE = "http://127.0.0.1:8000"

for q in ["Tumbbad", "Sardar Udham"]:
    r = requests.get(f"{BASE}/api/movies?search={q}").json()
    items = r.get("items", [])
    print(f"\nSearch '{q}': {len(items)} found")
    for m in items:
        if m["title"] in ["Tumbbad", "Sardar Udham"]:
            print(f"[OK] {m['title']} ({m.get('year')})")
            print(f"  Release Date: {m.get('release_date')}")
            print(f"  Poster: {m.get('poster_url')}")
            print(f"  Backdrop: {m.get('backdrop_url')}")
            # Verify TMDB HTTP 200
            p_res = requests.head(m["poster_url"], timeout=5)
            b_res = requests.head(m["backdrop_url"], timeout=5)
            print(f"  TMDB Poster [{p_res.status_code}] | Backdrop [{b_res.status_code}]")
            assert p_res.status_code == 200
            assert b_res.status_code == 200

print("\nALL VERIFICATIONS FOR TUMBBAD AND SARDAR UDHAM PASSED 100%!")

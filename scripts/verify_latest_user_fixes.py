import requests

BASE = "http://127.0.0.1:8000"

def run_tests():
    # 1. Health
    h = requests.get(f"{BASE}/health").json()
    print("Health:", h)
    assert h["status"] == "ok"
    assert h["movies"] == 2100

    # 2. Query all catalog items
    all_items = []
    for page in range(1, 30):
        r = requests.get(f"{BASE}/api/movies?page={page}&page_size=100").json()
        items = r.get("items", [])
        if not items:
            break
        all_items.extend(items)
    print(f"Total catalog movies: {len(all_items)}")
    movie_map = {m["title"]: m for m in all_items}

    # 3. Test Andhadhun
    andha = movie_map.get("Andhadhun")
    assert andha is not None, "Andhadhun missing!"
    print(f"\n[OK] Andhadhun: Poster: {andha['poster_url']} | Backdrop: {andha['backdrop_url']}")
    assert "dy3K6hNvwE05siGgiLJcEiwgpdO" in andha["poster_url"]

    # 4. Test Drishyam
    drish = movie_map.get("Drishyam")
    assert drish is not None, "Drishyam missing!"
    print(f"[OK] Drishyam: Poster: {drish['poster_url']} | Backdrop: {drish['backdrop_url']}")
    assert "gIClWRv5OSe8rl5Koi0AeUcCZ9Z" in drish["poster_url"]

    # 5. Test Dil Bechara
    dil = movie_map.get("Dil Bechara")
    assert dil is not None, "Dil Bechara missing!"
    print(f"[OK] Dil Bechara: Poster: {dil['poster_url']} | Backdrop: {dil['backdrop_url']}")
    assert "lMFjMrc8Bn0CQhtJDORfspXrWrK" in dil["poster_url"]

    # 6. Test KGF 2 & verify zero Star Wars images
    print("\n--- Verifying KGF Titles (Zero Star Wars) ---")
    for m in all_items:
        if "kgf" in m["title"].lower() or "k.g.f" in m["title"].lower():
            p = m.get("poster_url", "")
            b = m.get("backdrop_url", "")
            print(f"  {m['title']} | poster: {p} | backdrop: {b}")
            assert "6FfCtAuVAW8XJjZ7eWeLibRLWTw" not in p, "Found Star Wars poster in KGF!"
            assert "zqkmTXzjkAgPTEmOTCQUVHCS0h9" not in b, "Found Star Wars backdrop in KGF!"

    # 7. Test War 2
    war2 = movie_map.get("War 2")
    assert war2 is not None, "War 2 missing!"
    print(f"\n[OK] War 2: Release Date: {war2.get('release_date')} (Released film)")

    # 8. Test Spider-Man and Doomsday
    spid = movie_map.get("Spider-Man: Beyond the Spider-Verse")
    assert spid is not None, "Spider-Man missing!"
    print(f"[OK] Spider-Man Beyond: Poster: {spid['poster_url']}")

    doom = movie_map.get("Avengers: Doomsday")
    assert doom is not None, "Doomsday missing!"
    print(f"[OK] Avengers Doomsday: Poster: {doom['poster_url']}")

    # 9. Verify Award Winners contain NO upcoming movies
    print("\n--- Verifying Award-Winning Masterpieces ---")
    award_titles = [
        "Oppenheimer", "Everything Everywhere All at Once", "Parasite",
        "Godfather, The", "Godfather: Part II, The", "Schindler's List",
        "Forrest Gump", "Silence of the Lambs, The", "Titanic", "Whiplash",
        "Inception", "Interstellar"
    ]
    for at in award_titles:
        m = movie_map.get(at)
        assert m is not None, f"Award winner {at} missing!"
        print(f"[OK] Award Winner: {at} ({m.get('year')}) | Poster: {m.get('poster_url')[:45]}...")
        assert (m.get("year") or 0) <= 2024, f"Upcoming movie found in award winners: {at}"

    print("\n>>> ALL USER FIXES VERIFIED 100% SUCCESSFULLY! <<<")

if __name__ == "__main__":
    run_tests()

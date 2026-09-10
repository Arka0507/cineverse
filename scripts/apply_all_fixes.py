import json
import hashlib

# 1. Load movies.json
with open("artifacts/movies.json", "r", encoding="utf-8") as f:
    movies = json.load(f)

print(f"Loaded {len(movies)} movies.")

# 2. Exact image updates
exact_updates = {
    "Andhadhun": {
        "poster_url": "https://image.tmdb.org/t/p/w500/dy3K6hNvwE05siGgiLJcEiwgpdO.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/ArvKQJv3nEpnBoVyjWDUT7TtJOL.jpg",
        "release_date": "2018-10-05",
        "year": 2018,
    },
    "Drishyam": {
        "poster_url": "https://image.tmdb.org/t/p/w500/gIClWRv5OSe8rl5Koi0AeUcCZ9Z.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/5jxesZtbjNtsDitSBvK1amtd7o2.jpg",
        "release_date": "2015-07-30",
        "year": 2015,
    },
    "Drishyam 2": {
        "poster_url": "https://image.tmdb.org/t/p/w500/wk8Vu0DI0MiNLaXXiVqAwjLRKL5.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/498aYGlnvjvoiqXYhCNHrZERi4l.jpg",
        "release_date": "2022-11-18",
        "year": 2022,
    },
    "Dil Bechara": {
        "poster_url": "https://image.tmdb.org/t/p/w500/lMFjMrc8Bn0CQhtJDORfspXrWrK.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/tnwoGCRe2GV05f1RSIl1PusYc9v.jpg",
        "release_date": "2020-07-24",
        "year": 2020,
    },
    "K.G.F: Chapter 2": {
        "poster_url": "https://image.tmdb.org/t/p/w500/khNVygolU0TxLIDWff5tQlAhZ23.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/nsV5Mfi9FAV4w8eDsdr7uqVswOk.jpg",
        "release_date": "2022-04-14",
        "year": 2022,
    },
    "War 2": {
        "poster_url": "https://image.tmdb.org/t/p/w500/fxxVbjhIOl8ZPS69dH8xeeuxvmh.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/pKIRUTnwY3YYU9urSdsuobdcliP.jpg",
        "release_date": "2025-08-14",
        "year": 2025,
    },
    "Spider-Man: Beyond the Spider-Verse": {
        "poster_url": "https://image.tmdb.org/t/p/w500/9KAe39xqyZnv9J4W3DRGdQqX82h.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/7tT2w75p69nll5PvALpWFCYx5dU.jpg",
        "release_date": "2026",
        "year": 2026,
    },
    "Avengers: Doomsday": {
        "poster_url": "https://image.tmdb.org/t/p/w500/jzPwsojjFStf5lR5Nm07w2hH56G.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/s4v0UX1anfXm0UvloLsTTJ4v222.jpg",
        "release_date": "2026-12-18",
        "year": 2026,
    },
    "Everything Everywhere All at Once": {
        "poster_url": "https://image.tmdb.org/t/p/w500/u68AjlvlutfEIcpmbYpKcdi09ut.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/ss0Os3uWJfQAENILHZUdX8Tt1OC.jpg",
        "year": 2022,
    },
    "Parasite": {
        "poster_url": "https://image.tmdb.org/t/p/w500/7IiTTgloJzvGI1TAYymCfbfl3vT.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/hiKmpZMGZsrkA3cdce8a7Dpos1j.jpg",
        "year": 2019,
    },
    "The Godfather": {
        "poster_url": "https://image.tmdb.org/t/p/w500/3bhkrj58Vtu7enYsRolD1fZdja1.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/tSPT36ZKlP2WVHJLM4cQPLSzv3b.jpg",
        "year": 1972,
    },
    "The Godfather Part II": {
        "poster_url": "https://image.tmdb.org/t/p/w500/sSuQTCZwqKrNBNIsksO9IAUoWP9.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/pGzqRKrYeK4LogoysNro0vG8d8N.jpg",
        "year": 1974,
    },
    "The Lord of the Rings: The Return of the King": {
        "poster_url": "https://image.tmdb.org/t/p/w500/rCzpDGLbOoPwLjy3OAm5NUPOTrC.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/ctiw6FZK4N36LmkjSklWEbuvlq9.jpg",
        "year": 2003,
    },
    "Gladiator": {
        "poster_url": "https://image.tmdb.org/t/p/w500/wN2xWp1eIwCKOD0BHTcErTBv1Uq.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/Ar7QuJ7sJEiC0oP3I8fKBKIQD9u.jpg",
        "year": 2000,
    },
    "Forrest Gump": {
        "poster_url": "https://image.tmdb.org/t/p/w500/arw2vcBveWOVZr6pxd9XTd1TdQa.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/66Kn4XWhkuPkJxOJyPEx4U2CUfN.jpg",
        "year": 1994,
    },
    "The Silence of the Lambs": {
        "poster_url": "https://image.tmdb.org/t/p/w500/uS9m8OBk1A8eM9I042bx8XXpqAq.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/mfwq2nMBzArzZuQiY9R0A664m4x.jpg",
        "year": 1991,
    },
    "Titanic": {
        "poster_url": "https://image.tmdb.org/t/p/w500/9xjZS2rlVxm8SFx8kPC3aIGCOYQ.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/yDIv5nDABpqC37am2m2r481wM57.jpg",
        "year": 1997,
    },
    "Whiplash": {
        "poster_url": "https://image.tmdb.org/t/p/w500/7fn624j5lj3xTme2SgiLCeuedmO.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/fRGxZuo7jJUWQsVg9PREb98Aclp.jpg",
        "year": 2014,
    },
    "Slumdog Millionaire": {
        "poster_url": "https://image.tmdb.org/t/p/w500/5leCCi7ZF0CawAfM5Qo2ECKPprc.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/1wZoVT9RJsZmNjg8CecXqSgFUd9.jpg",
        "year": 2008,
    }
}

# Apply to all matching movies in catalog
modified_count = 0
for m in movies:
    t = m["title"]
    # Fix duplicate KGF Hindi which had Star Wars images
    if t in ["KGF: Chapter 2 (Hindi)", "KGF: Chapter 2"]:
        m["title"] = "K.G.F: Chapter 1"
        m["year"] = 2018
        m["release_date"] = "2018-12-21"
        m["poster_url"] = "https://image.tmdb.org/t/p/w500/khNVygolU0TxLIDWff5tQlAhZ23.jpg"
        m["backdrop_url"] = "https://image.tmdb.org/t/p/w1280/nsV5Mfi9FAV4w8eDsdr7uqVswOk.jpg"
        m["overview"] = "In the 1970s, a fierce rebel rises against brutal oppression to become the savior of the oppressed people in the Kolar Gold Fields."
        modified_count += 1
        print(f"Fixed Star Wars duplicate: renamed to K.G.F: Chapter 1 with genuine KGF artwork!")
    
    # Also fix Silence of the Lambs variations
    if "silence of the lambs" in t.lower():
        m["poster_url"] = exact_updates["The Silence of the Lambs"]["poster_url"]
        m["backdrop_url"] = exact_updates["The Silence of the Lambs"]["backdrop_url"]
        modified_count += 1

    # Also fix Godfather variations
    if t in ["Godfather, The", "The Godfather"]:
        m["poster_url"] = exact_updates["The Godfather"]["poster_url"]
        m["backdrop_url"] = exact_updates["The Godfather"]["backdrop_url"]
        modified_count += 1

    if t in ["Godfather: Part II, The", "The Godfather Part II"]:
        m["poster_url"] = exact_updates["The Godfather Part II"]["poster_url"]
        m["backdrop_url"] = exact_updates["The Godfather Part II"]["backdrop_url"]
        modified_count += 1

    if t in exact_updates:
        u = exact_updates[t]
        for k, v in u.items():
            m[k] = v
        modified_count += 1
        print(f"Updated {t}: poster={m.get('poster_url')[:35]}... backdrop={m.get('backdrop_url')[:35]}...")

# 3. Save movies.json
with open("artifacts/movies.json", "w", encoding="utf-8") as f:
    json.dump(movies, f, indent=2, ensure_ascii=False)

# 4. Hash movies.json
with open("artifacts/movies.json", "rb") as f:
    movies_hash = hashlib.sha256(f.read()).hexdigest()

with open("artifacts/manifest.json", "r", encoding="utf-8") as f:
    manifest = json.load(f)

manifest["sha256"]["movies.json"] = movies_hash

with open("artifacts/manifest.json", "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2)

print(f"\nAll fixes applied! Modified {modified_count} entries. movies.json hash: {movies_hash}")

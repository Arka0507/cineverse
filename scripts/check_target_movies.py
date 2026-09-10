import json

with open("artifacts/movies.json", "r", encoding="utf-8") as f:
    movies = json.load(f)

check_titles = [
    "K.G.F: Chapter 2",
    "War 2",
    "Andhadhun",
    "Drishyam",
    "Dil Bechara",
    "Avengers: Doomsday",
    "Spider-Man: Beyond the Spider-Verse",
]

by_t = {m["title"]: m for m in movies}
for t in check_titles:
    if t in by_t:
        m = by_t[t]
        print(f"TITLE: {t}")
        print(f"  movie_id: {m.get('movie_id')}")
        print(f"  year: {m.get('year')}")
        print(f"  release_date: {m.get('release_date')}")
        print(f"  genres: {m.get('genres')}")
        print(f"  poster_url: {m.get('poster_url')}")
        print(f"  backdrop_url: {m.get('backdrop_url')}")
    else:
        print(f"TITLE: {t} -> NOT FOUND IN CATALOG")

# Check if there are similar titles for Andhadhun, Drishyam, Dil Bechara
print("\n--- Search for similar titles ---")
for m in movies:
    low = m["title"].lower()
    if any(k in low for k in ["andha", "drishy", "bechara", "bachara", "kgf", "war"]):
        print(f"Found: {m['title']} ({m.get('year')}) | poster={m.get('poster_url')[:40] if m.get('poster_url') else None}")

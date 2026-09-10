import json

with open("artifacts/movies.json", "r", encoding="utf-8") as f:
    movies = json.load(f)

found = []
for m in movies:
    low = m["title"].lower()
    if "tumbbad" in low or "udham" in low or "sardar" in low:
        found.append(m)

print(f"Found {len(found)} matching movies in catalog:")
for m in found:
    print(f"ID: {m['movie_id']} | Title: {m['title']} | Year: {m.get('year')} | Poster: {m.get('poster_url')} | Backdrop: {m.get('backdrop_url')}")

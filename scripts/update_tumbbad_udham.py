import json
import hashlib

with open("artifacts/movies.json", "r", encoding="utf-8") as f:
    movies = json.load(f)

for m in movies:
    if m["title"] == "Tumbbad":
        m["poster_url"] = "https://image.tmdb.org/t/p/w500/vzjZAKozbDplHWcQXbXo0APKxst.jpg"
        m["backdrop_url"] = "https://image.tmdb.org/t/p/w1280/l0YKBu3LaehIFzBNjseLjx7MbaN.jpg"
        m["release_date"] = "2018-10-12"
        m["year"] = 2018
        m["genres"] = ["Hindi", "Fantasy", "Horror", "Drama"]
        m["overview"] = "India, 1918. On the outskirts of Tumbbad, a cursed village where it always rains, Vinayak cares for a mysterious old woman who holds the secret of an ancestral treasure—a treasure guarded by the demon Hastar."
        print(f"Updated Tumbbad: poster={m['poster_url']} | backdrop={m['backdrop_url']}")

    elif m["title"] == "Sardar Udham":
        m["poster_url"] = "https://image.tmdb.org/t/p/w500/d4fpJXhUNukd5XnzRO1XfWf7v88.jpg"
        m["backdrop_url"] = "https://image.tmdb.org/t/p/w1280/oZftUn6yOt61LItXE4zPOz4rca9.jpg"
        m["release_date"] = "2021-10-16"
        m["year"] = 2021
        m["genres"] = ["Hindi", "Drama", "History"]
        m["overview"] = "Deeply scarred by the 1919 Jallianwala Bagh massacre, revolutionary Sardar Udham Singh spent 21 years across the world before assassinating Michael O'Dwyer in London to avenge the lost lives of his people."
        print(f"Updated Sardar Udham: poster={m['poster_url']} | backdrop={m['backdrop_url']}")

# Save movies.json
with open("artifacts/movies.json", "w", encoding="utf-8") as f:
    json.dump(movies, f, indent=2, ensure_ascii=False)

# Re-hash movies.json
with open("artifacts/movies.json", "rb") as f:
    movies_hash = hashlib.sha256(f.read()).hexdigest()

with open("artifacts/manifest.json", "r", encoding="utf-8") as f:
    manifest = json.load(f)

manifest["sha256"]["movies.json"] = movies_hash

with open("artifacts/manifest.json", "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2)

print(f"Saved movies.json and updated manifest.json hash to: {movies_hash}")

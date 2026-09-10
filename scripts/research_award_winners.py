import urllib.request
import urllib.parse
import json

API_KEY = "15d2ea6d0dc1d476efbca3eba2b9bbfb"

award_winners = [
    ("Oppenheimer", 2023, "Won 7 Oscars incl. Best Picture"),
    ("Everything Everywhere All at Once", 2022, "Won 7 Oscars incl. Best Picture"),
    ("Parasite", 2019, "Won 4 Oscars incl. Best Picture"),
    ("The Godfather", 1972, "Won 3 Oscars incl. Best Picture"),
    ("The Godfather Part II", 1974, "Won 6 Oscars incl. Best Picture"),
    ("Schindler's List", 1993, "Won 7 Oscars incl. Best Picture"),
    ("The Lord of the Rings: The Return of the King", 2003, "Won 11 Oscars incl. Best Picture"),
    ("Gladiator", 2000, "Won 5 Oscars incl. Best Picture"),
    ("Forrest Gump", 1994, "Won 6 Oscars incl. Best Picture"),
    ("The Silence of the Lambs", 1991, "Won 5 Oscars - Big Five"),
    ("Titanic", 1997, "Won 11 Oscars incl. Best Picture"),
    ("Slumdog Millionaire", 2008, "Won 8 Oscars incl. Best Picture"),
    ("12 Years a Slave", 2013, "Won 3 Oscars incl. Best Picture"),
    ("No Country for Old Men", 2007, "Won 4 Oscars incl. Best Picture"),
    ("The Departed", 2006, "Won 4 Oscars incl. Best Picture"),
    ("Whiplash", 2014, "Won 3 Oscars"),
    ("La La Land", 2016, "Won 6 Oscars"),
    ("The Green Mile", 1999, "Nominated 4 Oscars"),
    ("Inception", 2010, "Won 4 Oscars"),
    ("Interstellar", 2014, "Won Oscar Visual Effects"),
]

results = []
for title, year, awards in award_winners:
    query = urllib.parse.quote(title)
    url = f"https://api.themoviedb.org/3/search/movie?api_key={API_KEY}&query={query}&year={year}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            items = data.get("results", [])
            if items:
                top = items[0]
                poster = f"https://image.tmdb.org/t/p/w500{top['poster_path']}" if top.get("poster_path") else None
                backdrop = f"https://image.tmdb.org/t/p/w1280{top['backdrop_path']}" if top.get("backdrop_path") else None
                results.append({
                    "title": title,
                    "year": year,
                    "awards": awards,
                    "tmdb_id": top["id"],
                    "poster_url": poster,
                    "backdrop_url": backdrop,
                    "overview": top.get("overview")
                })
                print(f"[OK] {title:<45} ({year}) | Poster: {top.get('poster_path')} | Backdrop: {top.get('backdrop_path')}")
            else:
                print(f"[NOT FOUND] {title}")
    except Exception as e:
        print(f"[ERROR] {title}: {e}")

with open("scripts/verified_award_winners.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)
print(f"\nSaved {len(results)} verified award winners to scripts/verified_award_winners.json")

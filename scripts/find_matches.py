import json

movies = json.load(open('artifacts/movies.json', encoding='utf-8'))
for m in movies:
    t = m['title'].lower()
    if any(k in t for k in ['12th', 'dangal', 'stree', 'jawan', 'pathaan', 'animal', 'fighter', 'idiot']):
        print(f"{m['movie_id']}: '{m['title']}' ({m.get('year')}) -> {m.get('poster_url')}")

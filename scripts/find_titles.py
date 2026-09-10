import json

movies = json.load(open('artifacts/movies.json', encoding='utf-8'))
for m in movies:
    t = m['title'].lower()
    if 'kalki' in t or 'chh' in t:
        print(f"'{m['title']}': poster={m.get('poster_url')}")

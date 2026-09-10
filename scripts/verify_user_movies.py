import json

movies = json.load(open('artifacts/movies.json', encoding='utf-8'))
by_title = {m['title'].lower(): m for m in movies}

checks = [
    'k.g.f: chapter 2', 'kalki 2898 ad', 'uri: the surgical strike',
    'shershaah', 'ramayana: part 1', 'brahmastra: part one - shiva',
    'superman', 'oppenheimer', 'dune: part two', 'interstellar', 'dangal', '3 idiots',
    'avengers: doomsday', 'the batman part ii', 'war 2', 'chhaava'
]

for c in checks:
    m = by_title.get(c)
    if m:
        print(f"'{m['title']}' ({m.get('year')}): poster={m.get('poster_url')} | release_date={m.get('release_date')}")
    else:
        print(f"'{c}' -> NOT FOUND")

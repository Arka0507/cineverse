import json

movies = json.load(open('artifacts/movies.json', encoding='utf-8'))
by_title = {m['title'].lower(): m for m in movies}

check_list = [
    '12th fail', 'animal', 'stree 2', 'fighter', 'jawan', 'pathaan',
    'dangal', 'chhava', 'shaitaan', 'kill', 'pushpa 2: the rule (hindi)',
    'bajrangi bhaijaan', '3 idiots', 'pk', 'kantara', 'k.g.f: chapter 2', 'rrr',
    'superman', 'avatar: fire and ash', 'the fantastic four: first steps',
    'mission: impossible - the final reckoning', 'oppenheimer', 'interstellar'
]

for t in check_list:
    m = by_title.get(t)
    if m:
        print(f"'{m['title']}' ({m.get('year')}) -> {m.get('poster_url')}")
    else:
        print(f"'{t}' -> NOT FOUND IN MOVIES.JSON")

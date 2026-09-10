import urllib.request
import json
import urllib.parse
import time

API_KEY = "15d2ea6d0dc1d476efbca3eba2b9bbfb"

test_titles = [
    "Chhaava", "Stree 2", "Pushpa 2: The Rule", "12th Fail", "Animal",
    "Dangal", "3 Idiots", "Sholay", "Bajrangi Bhaijaan", "Fighter",
    "Jawan", "Pathaan", "Kantara", "K.G.F: Chapter 2", "RRR",
    "Sikandar", "Housefull 5", "War 2", "Devara: Part 1", "Superman",
    "Avatar: Fire and Ash", "Mission: Impossible - The Final Reckoning"
]

for t in test_titles:
    q = urllib.parse.quote(t)
    url = f"https://api.themoviedb.org/3/search/movie?query={q}&api_key={API_KEY}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=6) as r:
            d = json.loads(r.read())
            res = d.get('results', [])
            if res:
                top = res[0]
                print(f"{t} -> TMDB: '{top.get('title')}' ({top.get('release_date', '')[:4]}) | Poster: {top.get('poster_path')} | Backdrop: {top.get('backdrop_path')}")
            else:
                print(f"{t} -> NOT FOUND")
    except Exception as e:
        print(f"{t} -> ERROR: {e}")
    time.sleep(0.2)

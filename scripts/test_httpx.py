import httpx
import time

API_KEY = "15d2ea6d0dc1d476efbca3eba2b9bbfb"

queries = [
    ("Stree 2", 2024),
    ("Animal", 2023),
    ("Fighter", 2024),
    ("Pushpa 2: The Rule", 2024),
    ("Chhaava", 2025),
    ("12th Fail", 2023),
    ("Jawan", 2023),
    ("Pathaan", 2023),
    ("Dangal", 2016),
    ("PK", 2014),
    ("Bajrangi Bhaijaan", 2015),
    ("Kabir Singh", 2019),
    ("Sanju", 2018),
    ("Brahmastra Part One: Shiva", 2022),
    ("War", 2019),
    ("Tanhaji: The Unsung Warrior", 2020),
    ("Drishyam 2", 2022),
    ("Kantara", 2022),
    ("K.G.F: Chapter 2", 2022),
    ("RRR", 2022),
    ("Singham Again", 2024),
    ("Bhool Bhulaiyaa 3", 2024),
    ("Shaitaan", 2024),
    ("Munjya", 2024),
    ("Kill", 2024),
    ("Article 370", 2024),
    ("Crew", 2024),
    ("Teri Baaton Mein Aisa Uljha Jiya", 2024),
    ("Chandu Champion", 2024),
    ("Kalki 2898 AD", 2024)
]

def search_movie(title, year):
    for attempt in range(5):
        try:
            with httpx.Client(timeout=10, headers={'User-Agent': 'Mozilla/5.0'}) as client:
                params = {'query': title, 'api_key': API_KEY}
                if year:
                    params['year'] = year
                r = client.get('https://api.themoviedb.org/3/search/movie', params=params)
                if r.status_code == 200:
                    res = r.json().get('results', [])
                    if not res and year:
                        # Try without year
                        r2 = client.get('https://api.themoviedb.org/3/search/movie', params={'query': title, 'api_key': API_KEY})
                        res = r2.json().get('results', [])
                    if res:
                        # Return best match
                        return res[0]
                    return None
        except Exception as e:
            time.sleep(1.0 + attempt * 0.5)
    return None

for t, y in queries:
    res = search_movie(t, y)
    if res:
        print(f"MATCH: '{t}' ({y}) -> '{res['title']}' ({res.get('release_date','')[:4]}) | Poster: {res.get('poster_path')}", flush=True)
    else:
        print(f"FAILED: '{t}'", flush=True)
    time.sleep(0.3)

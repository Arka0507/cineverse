import asyncio
import json
import httpx
import time

API_KEY = "15d2ea6d0dc1d476efbca3eba2b9bbfb"

test_titles = [
    ("Dangal", 2016),
    ("3 Idiots", 2009),
    ("PK", 2014),
    ("Bajrangi Bhaijaan", 2015),
    ("Sultan", 2016),
    ("Sanju", 2018),
    ("Padmaavat", 2018),
    ("Tiger Zinda Hai", 2017),
    ("War", 2019),
    ("Kabir Singh", 2019),
    ("Tanhaji: The Unsung Warrior", 2020),
    ("Sooryavanshi", 2021),
    ("The Kashmir Files", 2022),
    ("Bhool Bhulaiyaa 2", 2022),
    ("Brahmastra Part One: Shiva", 2022),
    ("Drishyam 2", 2022),
    ("Pathaan", 2023),
    ("Gadar 2", 2023),
    ("Jawan", 2023),
    ("Animal", 2023),
    ("12th Fail", 2023),
    ("Fighter", 2024),
    ("Shaitaan", 2024),
    ("Munjya", 2024),
    ("Stree 2", 2024),
    ("Bhool Bhulaiyaa 3", 2024),
    ("Singham Again", 2024),
    ("Pushpa 2: The Rule", 2024),
    ("Chhaava", 2025),
    ("Superman", 2025)
]

async def search_movie(client, sem, title, year):
    async with sem:
        for attempt in range(4):
            try:
                params = {"query": title, "api_key": API_KEY}
                if year:
                    params["year"] = year
                r = await client.get("https://api.themoviedb.org/3/search/movie", params=params)
                if r.status_code == 200:
                    results = r.json().get("results", [])
                    if not results and year:
                        r2 = await client.get("https://api.themoviedb.org/3/search/movie", params={"query": title, "api_key": API_KEY})
                        results = r2.json().get("results", [])
                    if results:
                        # Prioritize Hindi if looking for Indian movie
                        cand = results[0]
                        for item in results[:5]:
                            if item.get("original_language") == "hi" or item.get("title", "").lower() == title.lower():
                                cand = item
                                break
                        return title, cand.get("title"), cand.get("release_date", "")[:4], cand.get("poster_path"), cand.get("backdrop_path")
                await asyncio.sleep(0.3 * (attempt + 1))
            except Exception as e:
                await asyncio.sleep(0.5 * (attempt + 1))
        return title, None, None, None, None

async def main():
    start = time.time()
    sem = asyncio.Semaphore(5)
    limits = httpx.Limits(max_keepalive_connections=10, max_connections=15)
    async with httpx.AsyncClient(timeout=10, limits=limits, headers={"User-Agent": "Mozilla/5.0"}) as client:
        tasks = [search_movie(client, sem, t, y) for t, y in test_titles]
        results = await asyncio.gather(*tasks)
        for orig, found_t, yr, p, b in results:
            print(f"{orig} -> '{found_t}' ({yr}) | Poster: {p} | Backdrop: {b}")
    print(f"Done in {time.time() - start:.2f}s for {len(test_titles)} movies!")

if __name__ == "__main__":
    asyncio.run(main())

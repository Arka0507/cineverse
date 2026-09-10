import urllib.request
import json

h_res = urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)
data = json.loads(h_res.read())
print('FastAPI Health:', data)

m_res = urllib.request.urlopen('http://127.0.0.1:8000/api/movies?genre=Hindi&page_size=10', timeout=3)
hindi_res = json.loads(m_res.read())
print(f"Total Hindi movies returned by API: {hindi_res['total']}")
print("Top 10 Hindi movies:")
for m in hindi_res['items']:
    print(f"  {m['title']} ({m.get('year')}): {m.get('poster_url')}")

f_res = urllib.request.urlopen('http://127.0.0.1:8000/api/movies?search=Superman', timeout=3)
super_res = json.loads(f_res.read())
print(f"Superman search results: {len(super_res['items'])}")
for m in super_res['items']:
    print(f"  {m['title']} ({m.get('year')}): {m.get('poster_url')}")

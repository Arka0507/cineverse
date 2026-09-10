from pathlib import Path
from typing import Any
import asyncio
import numpy as np
import httpx
import pytest
from fastapi.testclient import TestClient
from backend.app.main import create_app
from backend.app.config import Settings
from backend.app.storage import Store
from backend.app.metadata import MetadataService
from ml_engine.recommender import Recommender

ROOT = Path(__file__).resolve().parents[2]

@pytest.fixture
def client(tmp_path: Path) -> Any:
    settings = Settings(artifacts_dir=ROOT/'artifacts', database_path=tmp_path/'test.db', tmdb_api_key='', rate_limit_per_minute=10000)
    with TestClient(create_app(settings)) as c: yield c

def session(client: TestClient, demo: int | None = None) -> tuple[int, dict[str,str]]:
    r=client.post('/api/session',json={'demo_user_id':demo})
    assert r.status_code==200
    data=r.json()
    return data['user_id'], {'Authorization':f"Bearer {data['token']}"}

def test_health_catalog_and_filter(client: TestClient) -> None:
    assert client.get('/health').json()['movies']==1682
    result=client.get('/api/movies',params={'search':'star wars','genre':'Sci-Fi'}).json()
    assert result['total']==1 and result['items'][0]['movie_id']==50
    assert result['items'][0]['metadata_source']=='fallback'
    assert client.get('/api/movies',params={'page_size':101}).status_code==422
    assert client.get('/api/movies',params={'page':999}).json()['items']==[]

def test_cold_start_persistence_and_live_update(client: TestClient) -> None:
    user,headers=session(client)
    body={'user_id':user,'top_k':100}
    first=client.post('/api/recommend/user',json=body,headers=headers).json()
    rated=first[0]['movie_id']
    response=client.post('/api/rate',json={'user_id':user,'movie_id':rated,'rating':5},headers=headers)
    assert response.status_code==200
    second=client.post('/api/recommend/user',json=body,headers=headers).json()
    assert rated not in [m['movie_id'] for m in second]
    assert first != second
    assert client.app.state.store.feedback(user)=={rated:5.0}
    reopened=Store(client.app.state.store.path)
    assert reopened.feedback(user)=={rated:5.0}
    client.post('/api/rate',json={'user_id':user,'movie_id':rated,'rating':1},headers=headers)
    assert reopened.feedback(user)=={rated:1.0}
    assert second != client.post('/api/recommend/user',json=body,headers=headers).json()

def test_auth_and_validation(client: TestClient) -> None:
    user,headers=session(client)
    assert client.post('/api/recommend/user',json={'user_id':user}).status_code==401
    assert client.post('/api/recommend/user',json={'user_id':user+1},headers=headers).status_code==403
    for rating in (0,6):
        assert client.post('/api/rate',json={'user_id':user,'movie_id':1,'rating':rating},headers=headers).status_code==422
    assert client.post('/api/rate',json={'user_id':user,'movie_id':999999,'rating':5},headers=headers).status_code==404
    assert client.post('/api/recommend/item',json={'movie_id':999999}).status_code==404
    assert client.post('/api/recommend/item',json={'movie_id':1,'top_k':-1}).status_code==422

def test_known_user_excludes_history(client: TestClient) -> None:
    user,headers=session(client,1)
    response=client.post('/api/recommend/user',json={'user_id':user,'top_k':100},headers=headers)
    assert response.status_code==200
    movies=response.json();seen=client.app.state.model.model['histories'][user]
    assert not set(m['movie_id'] for m in movies).intersection(seen)
    scores=[m['score'] for m in movies]
    assert scores==sorted(scores,reverse=True)
    assert len({m['movie_id'] for m in movies})==100
    assert all(0<=s<=1 for s in scores)

def test_similar_movies_and_cors(client: TestClient) -> None:
    response=client.post('/api/recommend/item',json={'movie_id':1,'top_k':12})
    assert response.status_code==200
    assert len(response.json())==12
    assert all(m['movie_id']!=1 for m in response.json())
    cors=client.options('/api/rate',headers={'Origin':'http://localhost:3000','Access-Control-Request-Method':'POST'})
    assert cors.headers['access-control-allow-origin']=='http://localhost:3000'

def test_harmonic_and_cold_items() -> None:
    model=Recommender(ROOT/'artifacts',blend='harmonic')
    x=np.array([.2,.8]);y=np.array([.4,.6])
    assert np.allclose(model.blend_scores(x,y,.5),2*x*y/(x+y))
    assert np.allclose(model.blend_scores(x,y,0),y)
    assert np.allclose(model.blend_scores(x,y,1),x)
    result=model.user(999999,20,{1:5,50:1})
    assert len(result)==20 and all(0<=m['score']<=1 for m in result)
    # Simulate a catalog-only item to exercise the explicit no-CF branch.
    model.model['counts'][2]=0
    assert all(np.isfinite(m['score']) for m in model.user(1,100))

def test_artifact_integrity(tmp_path: Path) -> None:
    import shutil
    shutil.copytree(ROOT/'artifacts',tmp_path/'artifacts')
    (tmp_path/'artifacts'/'svd_model.pkl').write_bytes(b'changed')
    with pytest.raises(ValueError,match='checksum'): Recommender(tmp_path/'artifacts')

def test_production_guard_and_demo_disabled(tmp_path: Path) -> None:
    with pytest.raises(ValueError): Settings(environment='production')
    settings=Settings(environment='production',session_secret='x'*40,demo_profiles=False,artifacts_dir=ROOT/'artifacts',database_path=tmp_path/'prod.db')
    with TestClient(create_app(settings)) as client:
        assert client.post('/api/session',json={'demo_user_id':1}).status_code==403
        assert client.post('/api/session',json={}).status_code==200

def test_rate_limit(tmp_path: Path) -> None:
    settings=Settings(artifacts_dir=ROOT/'artifacts',database_path=tmp_path/'limit.db',rate_limit_per_minute=1)
    with TestClient(create_app(settings)) as client:
        assert client.get('/api/genres').status_code==200
        assert client.get('/api/genres').status_code==429
        assert client.get('/health').status_code==200

def test_tmdb_hydration_cache_and_failure(tmp_path: Path) -> None:
    async def run() -> None:
        calls=[]
        def handler(request: httpx.Request) -> httpx.Response:
            calls.append(request.url.path)
            if request.url.path.endswith('/search/movie'):
                return httpx.Response(200,json={'results':[{'id':11,'title':'Star Wars'}]})
            return httpx.Response(200,json={'poster_path':'/poster.jpg','backdrop_path':'/backdrop.jpg','runtime':121,'overview':'Test synopsis','videos':{'results':[{'site':'YouTube','type':'Trailer','key':'abcdefghijk','official':True}]}})
        service=MetadataService(Store(tmp_path/'tmdb.db'),'fake-test-key')
        await service.client.aclose()
        service.client=httpx.AsyncClient(transport=httpx.MockTransport(handler),base_url='https://api.themoviedb.org/3')
        movie={'movie_id':50,'title':'Star Wars','year':1977,'genres':['Sci-Fi']}
        a,b=await asyncio.gather(service.hydrate(movie),service.hydrate(movie))
        assert a==b and a['runtime']==121 and a['metadata_source']=='tmdb'
        assert len(calls)==2
        await service.hydrate(movie)
        assert len(calls)==2
        await service.close()
        failure=MetadataService(Store(tmp_path/'failure.db'),'fake-test-key')
        await failure.client.aclose()
        failure.client=httpx.AsyncClient(transport=httpx.MockTransport(lambda _:httpx.Response(429)),base_url='https://api.themoviedb.org/3')
        assert (await failure.hydrate(movie))['metadata_source']=='fallback'
        await failure.close()
    asyncio.run(run())

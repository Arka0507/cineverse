# Complete source directory map

All paths are relative to the `cineverse/` folder in the source archive. Install-generated node_modules, .next, runtime databases, secrets and caches are omitted.

| File | Area |
|---|---|
| `.dockerignore` | Root configuration / instructions |
| `.env.example` | Root configuration / instructions |
| `.gitignore` | Root configuration / instructions |
| `README.md` | Root configuration / instructions |
| `artifacts/manifest.json` | Trained model artifact |
| `artifacts/movie_indices.json` | Trained model artifact |
| `artifacts/movies.json` | Trained model artifact |
| `artifacts/svd_model.pkl` | Trained model artifact |
| `artifacts/tfidf_matrix.pkl` | Trained model artifact |
| `artifacts/tfidf_vectorizer.pkl` | Trained model artifact |
| `backend/Dockerfile` | API and integration tests |
| `backend/__init__.py` | API and integration tests |
| `backend/app/__init__.py` | API and integration tests |
| `backend/app/config.py` | API and integration tests |
| `backend/app/main.py` | API and integration tests |
| `backend/app/metadata.py` | API and integration tests |
| `backend/app/schemas.py` | API and integration tests |
| `backend/app/storage.py` | API and integration tests |
| `backend/tests/test_system.py` | API and integration tests |
| `data/movielens_100k.csv` | Dataset input and provenance |
| `data/provenance.json` | Dataset input and provenance |
| `data/u.data` | Dataset input and provenance |
| `data/u.item` | Dataset input and provenance |
| `docker-compose.dev.yml` | Root configuration / instructions |
| `docker-compose.yml` | Root configuration / instructions |
| `docs/DIRECTORY_MAP.md` | Documentation and validation |
| `docs/SECURITY.md` | Documentation and validation |
| `docs/VALIDATION.md` | Documentation and validation |
| `docs/benchmark.json` | Documentation and validation |
| `docs/npm-audit.json` | Documentation and validation |
| `frontend/.dockerignore` | Next.js application and serving |
| `frontend/.env.local.example` | Next.js application and serving |
| `frontend/Dockerfile` | Next.js application and serving |
| `frontend/app/globals.css` | Next.js application and serving |
| `frontend/app/layout.tsx` | Next.js application and serving |
| `frontend/app/page.tsx` | Next.js application and serving |
| `frontend/components/AntiGravity.tsx` | Next.js application and serving |
| `frontend/components/HeroBillboard.tsx` | Next.js application and serving |
| `frontend/components/MovieArt.tsx` | Next.js application and serving |
| `frontend/components/MovieModal.tsx` | Next.js application and serving |
| `frontend/components/MovieRow.tsx` | Next.js application and serving |
| `frontend/components/Navbar.tsx` | Next.js application and serving |
| `frontend/components/NetflixCard.tsx` | Next.js application and serving |
| `frontend/lib/api.ts` | Next.js application and serving |
| `frontend/lib/types.ts` | Next.js application and serving |
| `frontend/next-env.d.ts` | Next.js application and serving |
| `frontend/next.config.mjs` | Next.js application and serving |
| `frontend/nginx.conf` | Next.js application and serving |
| `frontend/package-lock.json` | Next.js application and serving |
| `frontend/package.json` | Next.js application and serving |
| `frontend/postcss.config.mjs` | Next.js application and serving |
| `frontend/public/health.html` | Next.js application and serving |
| `frontend/tailwind.config.ts` | Next.js application and serving |
| `frontend/tsconfig.json` | Next.js application and serving |
| `ml_engine/__init__.py` | ML training and serving |
| `ml_engine/recommender.py` | ML training and serving |
| `ml_engine/train_hybrid.py` | ML training and serving |
| `pyproject.toml` | Root configuration / instructions |
| `requirements-dev.txt` | Root configuration / instructions |
| `requirements.txt` | Root configuration / instructions |
| `scripts/preview.py` | Local preview utility |

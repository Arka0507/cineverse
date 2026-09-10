# Cineverse — Hybrid Movie Recommendation Platform

A complete source project combining a trained MovieLens recommender, a typed FastAPI service, a Next.js 14 / React 18 movie interface, and a Matter.js Anti-Gravity sandbox.

**Delivery status:** source, trained artifacts, tests and deployment configuration are included. Python tests, strict type checks and the frontend production build passed. Docker execution and browser interaction QA were unavailable in the build environment. Treat this as a tested application foundation requiring your deployment acceptance checks, not a certified enterprise production release.

## 1. Start in Docker (development)

Install Docker Desktop with Compose v2. Unzip the project and open a terminal in the `cineverse` folder:

```bash
cp .env.example .env
# Optional: edit .env and set TMDB_API_KEY to your TMDB API key or read-access token.
docker compose -f docker-compose.dev.yml up --build
```

Windows PowerShell uses `Copy-Item .env.example .env` instead of `cp`.

- Frontend: http://localhost:3000
- API health: http://localhost:8000/health
- Interactive API docs: http://localhost:8000/docs

Both services reload source changes. The included artifacts mean training is not required for the first launch. The first Docker build requires internet access for dependencies. Without TMDB credentials, catalog pages remain usable with clearly marked typographic artwork and catalog descriptions; these are not claimed to be official posters or synopses.

Stop with `docker compose -f docker-compose.dev.yml down`. Do not add `-v` unless you intend to erase the development database and installed dependency volumes.

## 2. Start without Docker

Prerequisites: Python 3.11, Node.js 22, npm.

```bash
python -m venv .venv
# macOS/Linux:
source .venv/bin/activate
# Windows PowerShell:
# .venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
cp .env.example .env
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

Open a second terminal:

```bash
cd frontend
npm ci
cp .env.local.example .env.local
npm run dev
```

Keep both terminals running. Open http://localhost:3000. For another hostname or port, set `NEXT_PUBLIC_API_BASE_URL` in `frontend/.env.local` and `ALLOWED_ORIGINS` in the root `.env`, then restart both services. On a phone, `localhost` means the phone: use your computer's LAN address in both settings.

The preview helper is optional: with the API running and the frontend built without `.env.local`, run `python scripts/preview.py` from the root. It serves the static export and proxies API requests. It is a development convenience, not a production web server.

## 3. Using the application

- A fresh anonymous profile is created on first visit. Its signed session is stored in this browser. It is not a corporate SSO account and cannot be recovered if browser storage is cleared.
- Browse rotating featured titles, personalized picks, audience favorites and the paginated collection.
- Search by title, filter genres, or scroll each row using its arrows.
- Open a card for details. Rate a title from 1 to 5; the API commits the feedback, reranks picks and shows a related-title row. Hover thumbs-up is a 5-star shortcut. A repeat rating replaces the current preference while retaining an event record.
- Rated titles are excluded from personalized recommendations, including ratings already in the MovieLens profile.
- Profile settings allow a new profile or MovieLens demo user 1. The existing dataset profile option is disabled in production.
- **Anti-Gravity:** click the navbar button or press **Ctrl/Cmd + Shift + G**. Visible cards, the hero panel and navigation become rigid bodies. Drag, fling and collide them. Toggle inverted gravity. Click **Back to browsing**, press the shortcut again, or press **Esc** to spring back. Offscreen elements retain their layout and are not simulated. Resizing returns to the normal layout. Reduced motion shortens the return animation and pauses featured cycling; entering the explicit sandbox still enables physical motion.
- Trailer playback is available only for verified YouTube trailers returned by TMDB. The app does not stream full movies.
- Match percentages are ranking scores, not calibrated probabilities or accuracy claims.

## 4. Production deployment

The production stack serves a static Next.js export through Nginx and proxies `/api/*` and `/health` to FastAPI. No Next.js Node server, server actions, image optimizer or RSC API runs in the production container.

This is deliberate: the requested Next.js 14.2.35 has unresolved upstream advisories as of this delivery. The static deployment removes its server attack surface but does not make the old dependency supported or clear dependency scanners. Do not expose `next dev` or deploy `next start`. An organization that disallows unsupported build dependencies must approve a move to a currently patched Next.js release before rollout. See `docs/SECURITY.md` and the bundled audit report.

Prepare `.env`:

```bash
cp .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Put the generated value into `SESSION_SECRET`; do not commit it. Set `TMDB_API_KEY` if official metadata is needed. Set `ALLOWED_ORIGINS` to your actual frontend origin. Production Compose forces `ENVIRONMENT=production` and `DEMO_PROFILES=false`; startup refuses the development secret.

```bash
docker compose up --build -d
docker compose ps
docker compose logs --tail=100 backend
```

Open http://localhost:3000. The backend port is private to the Compose network. The frontend remains on port 3000, mapped to Nginx port 8080.

Put the frontend behind your managed HTTPS ingress. Configure ingress request limits, TLS, monitoring and backups appropriate to your environment. Only trust ingress forwarding headers after explicitly configuring the proxy boundary. Production uses a per-client Nginx limit plus a process-shared SQLite aggregate backend limit. Direct API deployments use the stricter default peer limit.

Both images have separate build/development/production stages. Backend serving runs as an unprivileged user, with a read-only root filesystem, persistent runtime volume, dropped capabilities and health checks. Nginx also runs unprivileged. Use your container registry's approved base-image digests for reproducible release images; the included tags intentionally allow patched base images.

### Capacity and persistence

SQLite WAL is appropriate for this 100K benchmark and a single application host. Multiple Uvicorn workers share the local database, including feedback and rate limits. Do not share SQLite over a network filesystem or pretend it is a multi-region database. For multiple backend replicas, migrate the Store interface to PostgreSQL and use a distributed limiter/cache such as Redis. The implementation does not claim horizontal scalability with SQLite.

The runtime volume stores ratings, append-only feedback events, anonymous profile IDs and metadata. Back it up using SQLite's backup API or a consistent volume snapshot. Do not copy a live `.db` without its WAL transaction state. Keep the model release and manifest together; roll back by deploying the previous artifacts and application image.

Background work warms metadata only. Rating writes are synchronous and transactional before success is returned. There is no critical job that can silently disappear if a background worker exits. Retraining is an explicit offline deployment job.

## 5. Data and training

The uploaded `movielens_100k.csv` contains **1,681 movie metadata rows**, not 100,000 user ratings. Training therefore uses the MovieLens `u.data` interactions and `u.item` catalog. It enriches directors and actors only when both ID and normalized title agree with the upload; **1,680 titles matched**. Original MovieLens titles and genre flags remain canonical, preserving foreign-key integrity.

Data origin: GroupLens MovieLens 100K. In this build, the original download server returned HTTP 502; the included `u.data` and `u.item` were retrieved from a public mirror. `data/provenance.json` records exact source links and SHA-256 hashes. There are no generated user ratings. Review the original dataset usage terms before commercial use. Do not infer a license grant from this project.

Retrain from the root:

```bash
python -m ml_engine.train_hybrid \
  --data-dir data \
  --metadata data/movielens_100k.csv \
  --output-dir artifacts \
  --factors 20
```

On Windows, use the command on one line. If `u.data` or `u.item` is absent, the script tries the official zip URL. For an offline environment or failed download, place both files in `data/` yourself. The included files allow fully offline training after dependency installation.

Training builds:

1. A sparse explicit-rating matrix and regularized global, user and item biases.
2. A bias-centered sparse residual matrix for 20-component `TruncatedSVD`, with seed 42.
3. TF-IDF title/genre vectors (unigrams and bigrams, L2 normalized), with repeated genre tokens to give genre overlap useful weight.
4. Bayesian item averages with a 25-rating global-mean prior.
5. Catalog, indices, history and SVD artifacts with a version manifest and SHA-256 checksums.

The serving process verifies every artifact checksum at startup. These hashes detect corruption, not malicious replacement of a manifest. Pickle files must come only from your trusted training pipeline; do not accept user uploads as models.

### Exact hybrid logic

`CF = clip((predicted_rating - 1) / 4, 0, 1)`.

For content, compute cosine similarities between each candidate and rated titles. Weight a history rating by `rating - 3`, so dislikes penalize similar titles. Transform the normalized weighted similarity into [0,1], then shrink toward normalized Bayesian popularity while fewer than 10 ratings are available.

With `HYBRID_BLEND=linear` (default):

```text
score = effective_alpha * CF + (1 - effective_alpha) * CB
```

With `HYBRID_BLEND=harmonic`:

```text
score = 1 / (effective_alpha / max(CF, epsilon)
             + (1 - effective_alpha) / max(CB, epsilon))
```

The explicit linear formula and harmonic-blending requirement in the brief are different, so both are implemented and selectable. Alpha defaults to 0.65. Endpoint alpha values use their exact single-component score.

For existing MovieLens users, `effective_alpha = alpha`. A fresh profile with ratings uses `alpha * min(rating_count / 10, 1)`. With zero history there is no personalized content vector to calculate, so ranking is **100% Bayesian popularity**. A new profile acquires content and then collaborative influence as ratings accumulate. Catalog-only items without ratings receive content/prior scores rather than unsupported collaborative estimates.

Feedback is folded into the learned item-factor space using ridge regression, so a rating changes recommendations immediately without retraining the global SVD. New users do not modify global artifacts. Similar-item rows use 90% TF-IDF cosine similarity and 10% popularity, excluding the selected movie.

### Measured evaluation

Evaluation uses the last 20% of each user's interactions in timestamp order as holdout. Evaluation fitting never sees these interactions. After evaluation, production artifacts are refit on all 100,000 ratings.

| Measure | Result |
|---|---:|
| Training interactions in evaluation | 79,619 |
| Held-out interactions | 20,381 |
| SVD RMSE | 0.9934 |
| SVD MAE | 0.7884 |
| Bias-only baseline RMSE | 1.0063 |
| Final production interactions | 100,000 |
| Users / movies | 943 / 1,682 |

These are **rating-prediction** metrics for CF, not hybrid ranking quality or business impact. The final artifacts contain all interactions and must not be re-used to report holdout results. Tune alpha and measure NDCG/Recall and online behavior on your own validation protocol before business claims.

A local 50-call warm benchmark of user recommendation with feedback measured approximately 3.7 ms p50 and 5.4 ms p95. This excludes HTTP, database, TMDB and network time; it is not an end-to-end throughput promise. Exact values are in `docs/benchmark.json`.

## 6. API contract

| Method | Route | Behavior |
|---|---|---|
| GET | `/health` | Model version, readiness, movie count and metadata mode |
| POST | `/api/session` | Create an anonymous signed profile, or a development-only demo profile |
| GET | `/api/genres` | Available genre filter values |
| GET | `/api/movies` | Search/filter catalog with page and page_size |
| GET | `/api/movies/{movie_id}` | Movie detail |
| POST | `/api/recommend/user` | Ranked unseen titles for an authorized profile |
| POST | `/api/recommend/item` | Similar titles |
| POST | `/api/rate` | Persist a rating and append a feedback event |

`POST /api/session` accepts `{}` or, in development, `{"demo_user_id":1}`. It returns `user_id`, `token` and `expires_in`. Send `Authorization: Bearer <token>` for user recommendations and ratings. The requested `user_id` must match the signed subject; changing the request body cannot access another profile.

Example requests in FastAPI `/docs` or any HTTP client:

```json
// POST /api/recommend/user — authenticated
{"user_id":100001,"top_k":20}

// POST /api/recommend/item
{"movie_id":50,"top_k":12}

// POST /api/rate — authenticated
{"user_id":100001,"movie_id":50,"rating":5}
```

Use the actual user ID returned by your session, not the example's ID. JSON comments above label separate examples; omit them from the actual request body.

Catalog example: `GET /api/movies?search=star&genre=Sci-Fi&page=1&page_size=24`. Search is case-insensitive, genre is an exact case-insensitive match. The result includes `items`, `total`, `page` and `page_size`.

`top_k` and `page_size` are bounded to 1–100. Ratings accept finite values from 1 to 5. Invalid bodies return 422; unknown movies 404; absent/expired sessions 401; profile mismatch 403; rate limits 429 with retry guidance. API responses include `X-Request-ID`. Session tokens and TMDB credentials are never logged.

## 7. TMDB setup and behavior

Obtain a TMDB API key or API Read Access Token from your TMDB account. Set `TMDB_API_KEY` on the backend only; never prefix it with `NEXT_PUBLIC_`.

The shared metadata service intercepts/enriches catalog, detail and recommendation responses. It is a typed service layer rather than a middleware that reparses JSON response bodies.

It searches titles with release-year constraints, rejects low-similarity title matches, fetches movie details and videos, and returns poster/backdrop URLs, overview, runtime and verified YouTube trailer keys. Requests are bounded to four concurrent upstream lookups per process; simultaneous requests for the same movie share a task. Successful responses are cached in SQLite for seven days, unmatched searches for one hour and transient failures for one minute.

The initial uncached page can be slower because it hydrates several titles. Subsequent reads use the cache. Missing artwork or an upstream failure falls back to readable catalog cards; the API never invents a trailer. No real TMDB account was available during validation: matching, cache, deduplication and failure paths were tested using mock HTTP responses. Confirm real titles and trailers with your credentials before launch, and meet TMDB's attribution and applicable usage terms.

## 8. Test and build

```bash
python -m pytest -q
python -m mypy backend/app ml_engine
cd frontend
npm ci
npm run typecheck
npm run build
npm audit
```

The 10 backend tests cover catalog search, bounds, sessions, cross-profile access, cold-start/reranking, repeat feedback, persistence, known-user exclusions, similarity, CORS, harmonic scoring, cold items, artifact checksums, production guards, throttling and mocked TMDB cache/failure behavior.

The audit is intentionally not hidden: Next.js 14 remains flagged. PostCSS is overridden to a patched version. Production must remain a static export unless the framework is upgraded. See `docs/VALIDATION.md` for completed checks and unavailable checks.

## 9. Troubleshooting

| Symptom | Action |
|---|---|
| API will not start / missing manifest | Run training from the repository root; check ARTIFACTS_DIR. |
| Checksum mismatch | Restore the full trusted artifact set or retrain; do not disable verification. |
| Official MovieLens download returns 502 | Use the included data files or manually obtain u.data/u.item from the documented source. |
| Production rejects configuration | Generate a unique SESSION_SECRET of at least 32 characters; disable demo profiles. |
| Browser shows connection error | Confirm `/health`, both ports, NEXT_PUBLIC_API_BASE_URL and CORS origins. |
| Only catalog artwork, no trailers | Set a valid backend TMDB key, restart, and allow a failed cache entry to expire. A title may genuinely lack a trailer. |
| Port 3000/8000 already used | Stop the other application or change port mappings and relevant origins. |
| Rating returns 401 | Reload to create a fresh session; existing expired anonymous sessions are not recoverable accounts. |
| Rating returns 403 | Use the same user_id and token returned from the session endpoint. |
| New profile seems unpersonalized | Rate several titles; zero-history profiles start from Bayesian popularity. |
| Development dependency changes not picked up | Rebuild the frontend and refresh only its node_modules volume; preserve the runtime database volume. |
| SQLite is locked | Check competing processes/volume filesystem; use PostgreSQL when moving beyond a single host. |
| Model deserialization warning | Use pinned package versions or retrain with the target environment. |
| Physics looks unstable on a small display | Close/open the mode after resizing; the simulator caps time steps and returns on resize. |
| No full-film playback | The platform recommends films and plays available trailers; film streaming is outside this dataset/API. |

## 10. Source map

See `docs/DIRECTORY_MAP.md` for every delivered file. The main module boundaries are:

| Path | Responsibility |
|---|---|
| `ml_engine/train_hybrid.py` | Download/load, validate, fit, evaluate and serialize |
| `ml_engine/recommender.py` | Hybrid ranking, cold-start, live fold-in and similarity |
| `backend/app/main.py` | FastAPI lifecycle, endpoints, authorization and request logging |
| `backend/app/config.py` | Typed environment configuration and production checks |
| `backend/app/schemas.py` | Pydantic v2 request/response models |
| `backend/app/storage.py` | Transactional feedback, event log, profiles, metadata and limits |
| `backend/app/metadata.py` | TMDB enrichment, concurrency control and caching |
| `backend/tests/test_system.py` | API/model integration tests |
| `frontend/app/page.tsx` | Screen state, session flow and API integration |
| `frontend/components/` | Navbar, billboard, carousels, cards, dialog, artwork and physics |
| `frontend/lib/` | Typed API client and shared frontend types |
| `frontend/nginx.conf` | Production static serving, API proxy and ingress controls |
| `artifacts/` | Trained SVD/TF-IDF, catalog, indices and checksummed manifest |
| `data/` | Supplied metadata, MovieLens inputs and provenance |
| `docker-compose*.yml` | Separate production and live-reload configurations |
| `docs/` | Validation, security, benchmark and directory map |

## Sources

- MovieLens 100K: https://grouplens.org/datasets/movielens/100k/
- Actual retrieval mirror: https://huggingface.co/datasets/includeno/movielens-100k/tree/main
- TMDB authentication: https://developer.themoviedb.org/docs/authentication-application
- TMDB title search: https://developer.themoviedb.org/reference/search-movie
- Next.js static export: https://nextjs.org/docs/14/app/building-your-application/deploying
- Current security release used for the deployment decision: https://nextjs.org/blog/august-2026-security-release

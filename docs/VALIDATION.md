# Validation record

Build date: 2026-09-10.

## Passed

- Full training: 100,000 ratings, 943 users, 1,682 movie records, k=20, seed=42.
- Uploaded metadata enrichment: 1,680 matching title/ID pairs; movie metadata alone was not mistaken for ratings.
- Temporal CF evaluation: 79,619 training interactions / 20,381 holdout interactions. RMSE 0.9933658672, MAE 0.7884311630, bias baseline RMSE 1.0063158935.
- Final model refit on all interactions, artifact hash generation and verified loading.
- 10 backend/model integration tests, including mocked TMDB success, deduplication, cache and HTTP failure.
- Strict mypy checks for backend/app and ml_engine.
- Next.js production compilation, TypeScript validation and static HTML export.
- Production/development Compose YAML parsing; configurations each include frontend and backend services.
- Python 3.11 dependency-resolution dry run with binary wheels.
- Authenticated API smoke request returned HTTP 200 and ranked movies for MovieLens demo user 1.
- Local warm recommendation benchmark recorded in benchmark.json.

## Findings and unverified work

- npm audit still reports a critical finding for the explicitly requested Next.js 14 dependency. PostCSS was patched. Production serves static assets in Nginx and contains no Next.js server runtime; see SECURITY.md. This is not a clean dependency audit.
- Docker is not installed in the authoring environment. Dockerfiles and Compose were authored and configuration syntax checked, but images were not built or executed here.
- Cloud browser navigation to the local application was blocked by the environment. No successful visual, responsive, animation, pointer-drag or browser end-to-end test is claimed. TypeScript/build verification does not replace those checks.
- Python tests and training ran under Python 3.12. Container configuration targets Python 3.11; a 3.11 dependency-resolution check passed, but execution under 3.11 was not available here.
- No actual TMDB API key was supplied. Metadata integration was tested using mock HTTP responses, not a live authenticated TMDB account.
- No load test, container vulnerability scan, security penetration test, SSO integration, enterprise data migration or hosted deployment was performed.
- MovieLens is a historical benchmark, not evidence of current movie popularity or production business value. Match scores are uncalibrated recommendation scores.

## Suggested acceptance flow in your environment

1. Start the development Compose file; open the UI and API health.
2. Search Star Wars, filter Sci-Fi, clear filters and change catalog pages.
3. Open a title, rate it and confirm the personalized row changes; refresh and confirm persistence.
4. Try a fresh profile and the development MovieLens profile.
5. Confirm official poster/backdrop/synopsis and trailer playback with your TMDB key.
6. Hover/focus cards, navigate rows with arrows, test mobile widths and keyboard navigation.
7. Toggle Anti-Gravity using the button and shortcut; drag/fling bodies, invert gravity and return with Escape. Confirm layout and focus restore.
8. Build the production images with a unique secret; confirm demo identities are disabled and API ports remain private.
9. Complete your required dependency, container, identity and deployment reviews before enterprise rollout.

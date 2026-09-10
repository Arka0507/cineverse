# Multi-stage Dockerfile for Cineverse (Full-stack API + ML engine + Next.js UI)
# Stage 1: Build Next.js static frontend
FROM node:22-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
ENV NEXT_TELEMETRY_DISABLED=1
ENV NEXT_PUBLIC_API_BASE_URL=""
RUN npm run build

# Stage 2: Python dependencies
FROM python:3.11-slim AS python-builder
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY requirements.txt .
RUN python -m venv /opt/venv && /opt/venv/bin/pip install --upgrade pip && /opt/venv/bin/pip install -r requirements.txt

# Stage 3: Production runner
FROM python:3.11-slim AS runner
ENV PATH="/opt/venv/bin:$PATH" PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
WORKDIR /app

RUN groupadd --gid 10001 app && useradd --uid 10001 --gid app --no-create-home app && mkdir -p /app/runtime && chown -R app:app /app/runtime

COPY --from=python-builder /opt/venv /opt/venv
COPY --chown=app:app backend ./backend
COPY --chown=app:app ml_engine ./ml_engine
COPY --chown=app:app artifacts ./artifacts
COPY --from=frontend-builder --chown=app:app /app/frontend/out ./frontend/out

ENV ENVIRONMENT=production
ENV DEMO_PROFILES="true"
ENV ARTIFACTS_DIR=/app/artifacts
ENV DATABASE_PATH=/app/runtime/cineverse.db
ENV FRONTEND_DIR=/app/frontend/out
ENV ALLOWED_ORIGINS="*"
ENV PORT=8000

USER app
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s CMD python -c "import os, urllib.request; port = os.environ.get('PORT', '8000'); urllib.request.urlopen(f'http://127.0.0.1:{port}/health', timeout=3)"

CMD ["sh", "-c", "python -m uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]

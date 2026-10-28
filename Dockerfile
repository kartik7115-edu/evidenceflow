# EvidenceFlow: one container serving the React app and the FastAPI API.
#
#   docker build -t evidenceflow .
#   docker run -p 8000:8000 -v evidenceflow-data:/data -e NCBI_EMAIL=you@example.org evidenceflow
#   open http://localhost:8000
#
# The SQLite database lives in /data. Mount a volume there (Railway: add a volume
# with mount path /data) or every restart starts with an empty database.

# ---- 1. Build the frontend -------------------------------------------------
FROM node:22-alpine AS frontend
WORKDIR /web
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

# ---- 2. Backend runtime ----------------------------------------------------
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app/backend
COPY backend/pyproject.toml backend/README.md ./
COPY backend/app ./app
RUN pip install .
COPY backend/alembic ./alembic
COPY backend/alembic.ini ./
COPY --from=frontend /web/dist /app/frontend/dist

ENV FRONTEND_DIST=/app/frontend/dist \
    DATABASE_URL=sqlite:////data/evidenceflow.db \
    ENVIRONMENT=production
RUN mkdir -p /data
VOLUME ["/data"]
EXPOSE 8000

# Apply migrations on every start (no-op when current), then serve.
# Railway and most hosts set $PORT; default to 8000 locally.
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

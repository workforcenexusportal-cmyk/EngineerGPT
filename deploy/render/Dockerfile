# Render-specific Dockerfile for the EngineerGPT backend.
# Build context is the repo ROOT (Render sets the context to the repo, with
# dockerfilePath pointing here). Render injects $PORT; uvicorn must bind it.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps for magic (MIME sniffing) and matplotlib fonts.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libmagic1 gcc \
    && rm -rf /var/lib/apt/lists/*

COPY backend/pyproject.toml ./
RUN pip install --upgrade pip && pip install -e .

COPY backend/ .

# Wait for the DB, apply migrations, seed the admin (idempotent), then serve on
# Render's injected PORT (defaults to 8000 locally).
CMD ["sh", "-c", "python -m scripts.wait_for_db && alembic upgrade head && python -m scripts.seed_admin && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

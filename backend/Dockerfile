FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps for magic (MIME sniffing) and matplotlib fonts
RUN apt-get update \
    && apt-get install -y --no-install-recommends libmagic1 gcc \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
RUN pip install --upgrade pip && pip install -e .

COPY . .

RUN useradd -m appuser && mkdir -p /app/storage && chown -R appuser /app
USER appuser

EXPOSE 8000
# Wait for Postgres, apply migrations, seed the admin (idempotent), then serve.
# Honours $PORT when set (Render) and defaults to 8000 (Docker Compose / Fly).
CMD ["sh", "-c", "python -m scripts.wait_for_db && alembic upgrade head && python -m scripts.seed_admin && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

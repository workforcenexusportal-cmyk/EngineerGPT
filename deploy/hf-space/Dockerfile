# Hugging Face Spaces Docker image for the EngineerGPT backend.
# HF Spaces require the app to listen on port 7860 (see frontmatter in README.md).
# Run `bash deploy/hf-space/sync.sh` first to copy the backend source into this
# folder, then push the folder to your Space.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps for magic (MIME sniffing) and matplotlib fonts.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libmagic1 gcc \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
RUN pip install --upgrade pip && pip install -e .

COPY . .

# Wait for the database, apply migrations, seed the admin (idempotent), serve on 7860.
# Note: no non-root USER here — HF Spaces run as root and file ownership can break otherwise.
CMD ["sh", "-c", "python -m scripts.wait_for_db && alembic upgrade head && python -m scripts.seed_admin && uvicorn app.main:app --host 0.0.0.0 --port 7860"]

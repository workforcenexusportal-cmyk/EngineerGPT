---
title: EngineerGPT API
emoji: 🤖
colorFrom: cyan
colorTo: magenta
sdk: docker
app_port: 7860
pinned: false
---

# EngineerGPT API (backend)

FastAPI backend for EngineerGPT, built from `deploy/hf-space/Dockerfile`.

- Docs: `https://<user>-<space>.hf.space/docs`
- Health: `https://<user>-<space>.hf.space/health`

Run `bash deploy/hf-space/sync.sh` from the repo root **before** pushing this
folder to your Space — it copies the backend source (`app/`, `scripts/`,
`migrations/`, `pyproject.toml`, `alembic.ini`) into this directory.

All configuration comes from Space secrets / variables (never commit secrets):
`DATABASE_URL`, `SECRET_KEY`, `AI_PROVIDER`, `OPENAI_API_KEY`, `ADMIN_EMAIL`,
`ADMIN_PASSWORD`, `CORS_ORIGINS`.

# EngineerGPT

> **AI Operating System for Manufacturing Engineers**

[![CI](https://github.com/workforcenexusportal-cmyk/EngineerGPT/actions/workflows/ci.yml/badge.svg)](https://github.com/workforcenexusportal-cmyk/EngineerGPT/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.12](https://img.shields.io/badge/python-3.12-3776AB.svg)](backend/pyproject.toml)
[![Next.js 15](https://img.shields.io/badge/Next.js-15-000000.svg)](frontend/package.json)

EngineerGPT is a specialized AI platform that reduces engineering documentation
effort, accelerates analysis, preserves company knowledge, and provides
AI-powered engineering agents for manufacturing, validation, test, design, and
quality teams.

This is **not** a generic chatbot. Every response is engineering-focused,
evidence-based, and citation-backed.

---

## Platform Modules

| # | Module | Status |
|---|--------------------------------|-----------------|
| 1 | **AI Test Report Agent** | ✅ Implemented |
| 2 | Engineering Knowledge Hub (RAG) | ✅ Implemented |
| 3 | Failure Analysis Agent | ✅ Implemented |
| 4 | Requirements Intelligence | ✅ Implemented |
| 5 | Meeting Preparation Agent | ✅ Implemented |
| 6 | Design Review Agent | ✅ Implemented |

All six modules are implemented end-to-end (backend agent + REST + UI) and share
the same clean-architecture module contract. The Knowledge Hub provides full
RAG: document ingestion (PDF/CSV/TXT) → chunk → embed → vector search.

---

## Architecture

```
engineer-gpt/
├── backend/          FastAPI · Python 3.12 · SQLAlchemy · pgvector · LangGraph
│   └── app/
│       ├── core/     config, security, db, logging, dependencies
│       ├── ai/       provider abstraction (OpenAI + graceful mock fallback)
│       ├── pipeline/ extract → chunk → embed → store
│       ├── modules/  one clean package per platform module
│       └── api/       versioned REST surface (/api/v1)
├── frontend/         Next.js 15 · TypeScript · Tailwind · Framer Motion · Zustand
├── docker-compose.yml  Postgres+pgvector · Redis · backend · frontend
└── .github/workflows/  CI (lint + test + build)
```

### Design principles

- **Clean architecture** — domain modules never import framework glue.
- **Feature-based folders** — each module owns its schemas, service, router.
- **SOLID + Dependency Injection** — services resolved via FastAPI `Depends`.
- **Provider abstraction** — swap OpenAI ↔ Azure OpenAI ↔ mock without touching modules.
- **Never hallucinate** — every AI output carries confidence + citations.

---

## Quick start (Docker)

## Quick start (Docker — the only requirement is Docker)

No Python, Node, Postgres, or Redis needs to be installed on your machine. All
dependencies are installed **inside the containers** at build time, the database
schema is created automatically on first boot, and the app runs in deterministic
**mock AI mode** until you provide an OpenAI key.

```bash
git clone https://github.com/workforcenexusportal-cmyk/EngineerGPT.git
cd EngineerGPT
docker compose up --build
```

- Backend API → http://localhost:8000/docs
- Frontend    → http://localhost:3000

To enable live AI (optional), set a key before launching — the app auto-detects it:

```bash
# Linux/macOS
export OPENAI_API_KEY=sk-...
# Windows PowerShell
$env:OPENAI_API_KEY="sk-..."

docker compose up --build
```

You can also copy `.env.example` to `.env` to override any default; Compose loads
it automatically. `.env` is optional — the stack launches with sane defaults.

## Quick start (no Docker — local SQLite, zero external services)

Don't have Docker? The stack runs fully locally on **SQLite** with a deterministic
**mock AI** provider — no Postgres, Redis, or API key required. When `POSTGRES_HOST`
is unset the app auto-selects SQLite and stores embeddings as JSON with in-Python
cosine similarity; on Postgres it uses `pgvector`. Nothing else changes.

**Backend** (Python 3.11+)
```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"

# .env for local dev (SQLite + mock AI + seeded admin)
#   ENVIRONMENT=development
#   AI_PROVIDER=mock
#   ADMIN_EMAIL=admin@engineergpt.local
#   ADMIN_PASSWORD=admin1234
#   ADMIN_FULL_NAME=Local Admin
#   SECRET_KEY=local-dev-secret-not-for-production

python -m scripts.init_db      # creates SQLite tables (skips pgvector on sqlite)
python -m scripts.seed_admin   # creates the admin login from ADMIN_* vars
uvicorn app.main:app --reload  # http://127.0.0.1:8000
pytest                         # 24 tests, all green
```

**Frontend** (Node 20+)
```powershell
cd frontend
npm install
npm run dev                    # http://localhost:3000
```

Sign in at http://localhost:3000 with `admin@engineergpt.local` / `admin1234`.
All six modules work offline in mock mode; set `OPENAI_API_KEY` and
`AI_PROVIDER=openai` in `backend/.env` to switch to live AI.

> On locked-down corporate npm setups where `.bin` shims aren't created, run the
> Next.js CLI directly: `node node_modules\next\dist\bin\next dev`
> (and `... next build` for production builds).

### One-command shortcuts (Make)

If you have GNU Make (native on Linux/macOS; use Git Bash or WSL on Windows):

```bash
make up              # build + run the whole stack in Docker
make check           # run every CI gate locally (lint + type + test + build)
make backend-test    # backend tests only
make down            # stop the stack
make help            # list all targets
```

---

## Deploy to production (Fly.io)

Fly builds the images on **remote builders**, so you don't need Docker locally.

```powershell
# 1. Install the CLI and sign in
iwr https://fly.io/install.ps1 -useb | iex
fly auth login

# 2. One-command deploy (backend + frontend + managed Postgres)
.\deploy\fly-deploy.ps1 -Region iad -AiProvider azure
```

The script provisions two Fly apps plus a managed Postgres, wires `DATABASE_URL`,
prompts for secrets **locally** (admin password, Azure OpenAI endpoint/key and
deployment names), generates a strong `SECRET_KEY`, sets CORS to the frontend
origin, and deploys both services. When it finishes you get:

- Frontend → `https://<web-app>.fly.dev`
- Backend  → `https://<api-app>.fly.dev/docs`

**Database & vectors.** Production defaults to portable embedding storage (JSON +
in-Python cosine) so it runs on **any** managed Postgres with zero extensions.
To switch to native `pgvector` for scale: connect as the Postgres superuser, run
`CREATE EXTENSION vector;` in the app database, then
`fly secrets set --app <api-app> USE_PGVECTOR=true` and redeploy.

**Real AI.** With `-AiProvider azure` (or `openai`) the app calls the live model;
omit credentials to run in deterministic mock mode. Provider is swapped purely
via secrets — no code changes.

> **Note:** Fly.io requires a credit card for every new account. If you don't
> want to give one, use the free card-free path below instead.

## Deploy to production (free, no credit card)

Stack: **Vercel** (frontend) + **Hugging Face Spaces** (backend) + **Neon**
(Postgres). All three have free tiers that never ask for a card. Free tiers
sleep after inactivity and cold-start on the next request (~30–60s) — fine for
demos and sharing, not for production traffic.

**1. Database — Neon** (https://neon.tech, free plan, no card)

1. Create a project (any region).
2. Copy the **connection string** (it looks like
   `postgresql://user:pass@ep-xxx.region.aws.neon.tech/dbname`). Append
   `?sslmode=require`.

**2. Backend — Hugging Face Spaces** (free, no card)

1. Create a Space at https://huggingface.co/new-space — **SDK: Docker**, name
   e.g. `engineergpt-api`.
2. From the repo root, prepare and push:
   ```bash
   bash deploy/hf-space/sync.sh          # copies backend source into the folder
   cd deploy/hf-space
   git init && git add -A && git commit -m "deploy"
   git remote add origin https://huggingface.co/spaces/<your-user>/engineergpt-api
   git push -f origin main
   ```
3. On the Space's **Settings → Variables and secrets**, add (secrets are never
   committed):
   ```
   ENVIRONMENT=production
   SECRET_KEY=<long random string>        # e.g. openssl rand -base64 48
   DATABASE_URL=<your Neon connection string with ?sslmode=require>
   AI_PROVIDER=openai                     # or mock / azure
   OPENAI_API_KEY=sk-...
   ADMIN_EMAIL=admin@example.com
   ADMIN_PASSWORD=<strong password>
   CORS_ORIGINS=["https://<your-app>.vercel.app","http://localhost:3000"]
   ```
   The container waits for the DB, applies migrations, seeds the admin, then
   serves. Your API is at `https://<your-user>-engineergpt-api.hf.space/docs`.

   > Free Spaces restart with an empty disk — uploaded knowledge-hub files and
   > SQLite data are ephemeral. All persistent state lives in the Neon database.

**3. Frontend — Vercel** (free, no card)

1. Import this GitHub repo at https://vercel.com/new.
2. **Root Directory:** `frontend`.
3. **Environment Variable (build):** `NEXT_PUBLIC_API_BASE_URL` =
   `https://<your-user>-engineergpt-api.hf.space`.
4. Deploy. The app is live at `https://<your-app>.vercel.app`.

Sign in with your `ADMIN_EMAIL` / `ADMIN_PASSWORD`. All six modules work in mock
mode; the OpenAI key switches the backend to live AI — no code changes.

---

## Contributing & branch protection

CI runs on every push and pull request (`ruff` + `mypy` + `pytest` for the
backend, `lint` + `build` for the frontend). Recommended repository settings on
GitHub → **Settings → Branches → Add branch ruleset** for `main`:

- ✅ Require a pull request before merging (at least 1 approval).
- ✅ Require status checks to pass — select the **backend** and **frontend** CI jobs.
- ✅ Require branches to be up to date before merging.
- ✅ Require conversation resolution before merging.
- ✅ Block force pushes and deletions of `main`.

Do development on feature branches and open PRs into `main`; the same checks you
run locally with `make check` gate the merge.

---

## Security posture

- JWT (OAuth2 password + bearer) auth, RBAC (`admin`/`manager`/`engineer`/`viewer`).
- Secrets only via environment / Azure Key Vault — never in source.
- File uploads: MIME validation, size limits, extension allow-list.
- Input validation via Pydantic, parameterized queries (no raw SQL), rate limiting, audit logging.
- TLS 1.3 in transit, AES-256 at rest (managed by cloud/storage layer).

See `backend/app/core/security.py` and `backend/app/core/middleware.py`.

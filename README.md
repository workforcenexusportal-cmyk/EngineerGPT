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

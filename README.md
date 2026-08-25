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
| 1 | **AI Test Report Agent** (MVP) | ✅ Implemented |
| 2 | Engineering Knowledge Hub | 🧱 Scaffolded |
| 3 | Failure Analysis Agent | 🧱 Scaffolded |
| 4 | Requirements Intelligence | 🧱 Scaffolded |
| 5 | Meeting Preparation Agent | 🧱 Scaffolded |
| 6 | Design Review Agent | 🧱 Scaffolded |

The **AI Test Report Agent** is the first shipped product (MVP). The remaining
modules share the same clean-architecture module contract so they can be filled
in incrementally without structural changes.

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

## Local development (optional — requires Python 3.11+ and Node 20+)

**Backend**
```bash
cd backend
python -m venv .venv && . .venv/Scripts/activate   # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -e ".[dev]"
python -m scripts.init_db      # creates pgvector extension + tables
uvicorn app.main:app --reload
pytest
```

**Frontend**
```bash
cd frontend
npm install
npm run dev
```

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

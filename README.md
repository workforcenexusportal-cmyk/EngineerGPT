# EngineerGPT

> **AI Operating System for Manufacturing Engineers**

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

---

## Security posture

- JWT (OAuth2 password + bearer) auth, RBAC (`admin`/`manager`/`engineer`/`viewer`).
- Secrets only via environment / Azure Key Vault — never in source.
- File uploads: MIME validation, size limits, extension allow-list.
- Input validation via Pydantic, parameterized queries (no raw SQL), rate limiting, audit logging.
- TLS 1.3 in transit, AES-256 at rest (managed by cloud/storage layer).

See `backend/app/core/security.py` and `backend/app/core/middleware.py`.

# EngineerGPT — developer shortcuts
# Usage: `make <target>` (requires GNU Make; on Windows use Git Bash or WSL).

COMPOSE ?= docker compose

.DEFAULT_GOAL := help
.PHONY: help up down build rebuild logs ps restart \
        backend-install backend-test backend-lint backend-type backend-check init-db \
        frontend-install frontend-dev frontend-build frontend-lint \
        check clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

## ---------------------------------------------------------------------------
## Docker (only requirement: Docker)
## ---------------------------------------------------------------------------
up: ## Build + start the full stack (db, cache, backend, frontend)
	$(COMPOSE) up --build

down: ## Stop and remove containers
	$(COMPOSE) down

build: ## Build all images
	$(COMPOSE) build

rebuild: ## Rebuild images without cache
	$(COMPOSE) build --no-cache

logs: ## Tail logs from all services
	$(COMPOSE) logs -f

ps: ## List running services
	$(COMPOSE) ps

restart: down up ## Restart the stack

## ---------------------------------------------------------------------------
## Backend (local dev)
## ---------------------------------------------------------------------------
backend-install: ## Install backend deps (editable + dev extras)
	cd backend && pip install -e ".[dev]"

init-db: ## Create pgvector extension + tables
	cd backend && python -m scripts.init_db

backend-test: ## Run backend tests
	cd backend && pytest -q

backend-lint: ## Lint backend with ruff
	cd backend && ruff check .

backend-type: ## Type-check backend with mypy
	cd backend && mypy app

backend-check: backend-lint backend-type backend-test ## All backend gates

## ---------------------------------------------------------------------------
## Frontend (local dev)
## ---------------------------------------------------------------------------
frontend-install: ## Install frontend deps
	cd frontend && npm install

frontend-dev: ## Run the Next.js dev server
	cd frontend && npm run dev

frontend-build: ## Production build
	cd frontend && npm run build

frontend-lint: ## Lint the frontend
	cd frontend && npm run lint

## ---------------------------------------------------------------------------
## Aggregate
## ---------------------------------------------------------------------------
check: backend-check frontend-build ## Run every CI gate locally

clean: ## Remove build/cache artifacts (keeps Docker volumes)
	$(COMPOSE) down --remove-orphans
	-cd backend && rm -rf .pytest_cache .ruff_cache .mypy_cache
	-cd frontend && rm -rf .next

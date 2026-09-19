SHELL := /bin/zsh
.DEFAULT_GOAL := help

.PHONY: help infra-up infra-down infra-logs setup web-setup api-setup migrate \
        migrate-downgrade seed seed-demo embed embed-demo api-dev web-dev api-test web-test test lint \
        typecheck push clean

help: ## Show help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

infra-up: ## Start Postgres (pgvector) + Redis
	docker compose up -d

infra-down: ## Stop infra containers
	docker compose down

infra-logs: ## Tail infra logs
	docker compose logs -f postgres redis

setup: web-setup api-setup ## Install all dependencies

web-setup: ## Install web + workspace dependencies
	npm install

api-setup: ## Install API Python dependencies + dev tooling
	python3 -m venv .venv || test -d .venv
	./.venv/bin/pip install -U pip
	./.venv/bin/pip install -e apps/api[dev]

migrate: ## Run Alembic migrations against the API database
	./.venv/bin/alembic -c apps/api/alembic.ini upgrade head

migrate-downgrade: ## Downgrade DB one revision
	./.venv/bin/alembic -c apps/api/alembic.ini downgrade -1

seed: ## Load REAL StatsBomb open data (one-time ~17 GB clone; all comps)
	./.venv/bin/python -m apps.api.app.services.statsbomb

seed-demo: ## Load legacy DEMO data (provider=demo) — QA/offline only
	./.venv/bin/python -m apps.api.app.scripts.seed_demo

embed: ## Embed the default provider's roster into pgvector (deterministic)
	./.venv/bin/python -m apps.api.app.scripts.embed_demo

embed-demo: ## Embed the demo roster into pgvector (deterministic)
	./.venv/bin/python -m apps.api.app.scripts.embed_demo --provider demo

api-dev: ## Run FastAPI dev server (http://localhost:8000)
	./.venv/bin/uvicorn apps.api.app.main:app --reload --host 0.0.0.0 --port 8000

api-test: ## Run API + analytics tests
	./.venv/bin/python -m pytest apps/api/tests -q

web-dev: ## Run Next.js dev server (http://localhost:3000)
	npm run dev --workspace apps/web

web-test: ## Run web tests
	npm run test:web

lint: ## Run all linting
	npm run lint
	./.venv/bin/python -m pytest -q apps/api/tests || true

typecheck: ## TypeScript strict checks
	npm run typecheck

test: api-test web-test ## Run all tests

push: ## Commit all changes and push to GitHub
	git add -A
	git commit -m "chore: checkpoint $(shell date +%Y-%m-%d_%H%M)" || true
	git push

clean: ## Remove containers, caches, node deps
	git clean -ndX
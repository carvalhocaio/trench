.PHONY: help dev run sync install hooks hooks-run test lint lint-fix format format-check typecheck audit ci check clean db-up db-down db-reset migrate migration migrate-down seed import-schedule import-rosters import-injuries import-stats web-install web-dev web-types web-lint web-typecheck web-build

help: ## Lists all available Makefile commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-16s\033[0m %s\n", $$1, $$2}'

dev: db-up ## Starts Postgres, the API and the web app together (Ctrl+C stops both)
	@trap 'kill 0' EXIT INT TERM; \
	$(MAKE) run & \
	$(MAKE) web-dev & \
	wait

run: ## Starts the API with auto-reload on http://localhost:8000
	uv run uvicorn trench.api.app:create_app --factory --reload

sync: ## Installs runtime and dev dependencies using uv
	uv sync

install: sync ## Alias for sync

hooks: ## Installs the pre-commit hooks into .git/hooks
	uv run pre-commit install

hooks-run: ## Runs all pre-commit hooks against all files
	uv run pre-commit run --all-files

test: ## Runs the test suite with pytest
	uv run pytest

lint: ## Checks code with ruff
	uv run ruff check .

lint-fix: ## Automatically fixes ruff lint issues
	uv run ruff check --fix .

format: ## Formats code with ruff
	uv run ruff format .

format-check: ## Verifies formatting with ruff without modifying files
	uv run ruff format --check .

typecheck: ## Runs mypy in strict mode over source and tests
	uv run mypy

audit: ## Audits dependencies for known security vulnerabilities
	uv run pip-audit

ci: lint format-check typecheck audit test ## Runs full verification pipeline locally

check: ci ## Alias for ci

clean: ## Cleans build artifacts and caches
	rm -rf .ruff_cache .pytest_cache .mypy_cache dist build *.egg-info .coverage htmlcov
	find . -type d -name '__pycache__' -not -path './.venv*' -exec rm -rf {} +

db-up: ## Starts Postgres and waits until it is healthy
	docker compose up -d --wait

db-down: ## Stops Postgres keeping the data volume
	docker compose down

db-reset: ## Stops Postgres and wipes the data volume
	docker compose down -v

migrate: ## Applies all pending migrations
	uv run alembic upgrade head

migration: ## Autogenerates a migration: make migration m="describe the change"
	@if [ -z "$(m)" ]; then \
		echo 'Error: m is required. Example: make migration m="add teams table"'; \
		exit 1; \
	fi
	uv run alembic revision --autogenerate -m "$(m)"

migrate-down: ## Reverts the latest migration
	uv run alembic downgrade -1

seed: ## Seeds the 32 NFL teams (safe to run more than once)
	uv run trench seed-teams

import-schedule: ## Imports a season's schedule and final scores from ESPN (usage: make import-schedule SEASON=2026)
	uv run trench import-schedule --season $(SEASON)

import-rosters: ## Imports/updates the 32 team rosters from ESPN
	uv run trench import-rosters

import-injuries: ## Imports the current injury report for a week's games (usage: make import-injuries SEASON=2026 WEEK=2)
	uv run trench import-injuries --season $(SEASON) --week $(WEEK)

import-stats: ## Imports team and player box score stats for a week's finished games (usage: make import-stats SEASON=2026 WEEK=1)
	uv run trench import-stats --season $(SEASON) --week $(WEEK)

web-install: ## Installs the web app dependencies with pnpm
	cd web && pnpm install

web-dev: ## Starts the web app with auto-reload on http://localhost:3000
	cd web && pnpm dev

web-types: ## Regenerates the web app's API types from the OpenAPI schema
	uv run trench openapi > web/openapi.json
	cd web && pnpm run types

web-lint: ## Checks the web app with eslint
	cd web && pnpm run lint

web-typecheck: ## Runs the Next.js and TypeScript type checks for the web app
	cd web && pnpm run typecheck

web-build: ## Builds the web app for production
	cd web && pnpm run build


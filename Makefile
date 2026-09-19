.PHONY: help run sync install hooks hooks-run test lint lint-fix format format-check typecheck audit ci check clean db-up db-down db-reset migrate migration migrate-down

help: ## Lists all available Makefile commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-16s\033[0m %s\n", $$1, $$2}'

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

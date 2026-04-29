.PHONY: setup lint test start-api deploy_gcr help

# ── Help ──────────────────────────────────────────────────────────────────────

help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*##' Makefile | awk -F ':.*##' '{printf "  %-15s %s\n", $$1, $$2}'

# ── Setup ─────────────────────────────────────────────────────────────────────

setup: ## Install dependencies
	uv sync --group dev



# ── Serve ─────────────────────────────────────────────────────────────────────

# Usage:
#   make start-api                          # defaults to local.env
#   make start-api APP_CONFIG=stage.env

APP_CONFIG ?= local.env

start-api: ## Start the FastAPI server locally (APP_CONFIG=local.env)
	APP_CONFIG_FILE=$(APP_CONFIG) uv run uvicorn example_api_service.main_api:app --reload --host 0.0.0.0 --port 8080


# ── Lint ──────────────────────────────────────────────────────────────────────

lint: ## Lint and format with ruff
	uv run ruff check --fix .
	uv run ruff format .

# ── Test ──────────────────────────────────────────────────────────────────────

test: ## Run tests
	uv run pytest


# ── Deploy ────────────────────────────────────────────────────────────────────



# Usage:
#   make deploy_gcr DEPLOY_CONFIG=prod.deploy.env
deploy_gcr: ## Deploy to Cloud Run service (DEPLOY_CONFIG=<file>)
ifndef DEPLOY_CONFIG
	$(error DEPLOY_CONFIG is required. Usage: make deploy_gcr DEPLOY_CONFIG=prod.deploy.env)
endif
	bash ./scripts/deploy_cloud_run.sh $(DEPLOY_CONFIG)




.PHONY: setup install lint test execute-job deploy_gcrj help

# ── Help ──────────────────────────────────────────────────────────────────────

help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*##' Makefile | awk -F ':.*##' '{printf "  %-15s %s\n", $$1, $$2}'

# ── Setup ─────────────────────────────────────────────────────────────────────

setup: ## Install dependencies
	uv sync --group dev


install: ## Install CLI globally as editable (source changes apply immediately)
	uv tool install --editable .



# ── Lint ──────────────────────────────────────────────────────────────────────

lint: ## Lint and format with ruff
	uv run ruff check --fix .
	uv run ruff format .

# ── Test ──────────────────────────────────────────────────────────────────────

test: ## Run tests
	uv run pytest


# ── Deploy ────────────────────────────────────────────────────────────────────


# Usage:
#   make execute-job DEPLOY_CONFIG=prod.deploy.env [ARGS="items"]

execute-job: ## Execute an existing Cloud Run Job (DEPLOY_CONFIG=<file> [ARGS="<cli args>"])
ifndef DEPLOY_CONFIG
	$(error DEPLOY_CONFIG is required. Usage: make execute-job DEPLOY_CONFIG=prod.deploy.env)
endif
	bash ./scripts/execute_cloud_run_job.sh $(DEPLOY_CONFIG) $(ARGS)




# Usage:
#   make deploy_gcrj DEPLOY_CONFIG=prod.deploy.env
deploy_gcrj: ## Deploy to Cloud Run Job (DEPLOY_CONFIG=<file>)
ifndef DEPLOY_CONFIG
	$(error DEPLOY_CONFIG is required. Usage: make deploy_gcrj DEPLOY_CONFIG=prod.deploy.env)
endif
	bash ./scripts/deploy_cloud_run_job.sh $(DEPLOY_CONFIG)



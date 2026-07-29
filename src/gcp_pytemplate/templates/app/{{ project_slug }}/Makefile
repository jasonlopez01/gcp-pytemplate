.PHONY: setup{% if include_cli %} install{% endif %} lint test{% if include_api %} start-api{% endif %}{% if include_cloud_run_jobs %} execute-job{% endif %}{% if include_cloud_run %} invoke-api deploy_gcr{% endif %}{% if include_cloud_run_jobs %} deploy_gcrj{% endif %} help

# ── Help ──────────────────────────────────────────────────────────────────────

help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*##' Makefile | awk -F ':.*##' '{printf "  %-15s %s\n", $$1, $$2}'

# ── Setup ─────────────────────────────────────────────────────────────────────

setup: ## Install dependencies
	uv sync --group dev

{% if include_cli %}
install: ## Install CLI globally as editable (source changes apply immediately)
	uv tool install --editable .

{% endif %}
{% if include_api %}
# ── Serve ─────────────────────────────────────────────────────────────────────

# Usage:
#   make start-api                          # defaults to local.env
#   make start-api APP_CONFIG=stage.env

APP_CONFIG ?= local.env

start-api: ## Start the FastAPI server locally (APP_CONFIG=local.env)
	APP_CONFIG_FILE=$(APP_CONFIG) uv run uvicorn {{ project_module }}.main_api:app --reload --host 0.0.0.0 --port 8080

{% endif %}
# ── Lint ──────────────────────────────────────────────────────────────────────

lint: ## Lint and format with ruff
	uv run ruff check --fix .
	uv run ruff format .

# ── Test ──────────────────────────────────────────────────────────────────────

test: ## Run tests
	uv run pytest

{% if include_cloud_run or include_cloud_run_jobs %}
# ── Deploy ────────────────────────────────────────────────────────────────────
{% if include_cloud_run_jobs %}

# Usage:
#   make execute-job DEPLOY_CONFIG=prod.deploy.env [ARGS="items"]

execute-job: ## Execute an existing Cloud Run Job (DEPLOY_CONFIG=<file> [ARGS="<cli args>"])
ifndef DEPLOY_CONFIG
	$(error DEPLOY_CONFIG is required. Usage: make execute-job DEPLOY_CONFIG=prod.deploy.env)
endif
	bash ./scripts/execute_cloud_run_job.sh $(DEPLOY_CONFIG) $(ARGS)
{% endif %}
{% if include_cloud_run %}

# Usage:
#   make deploy_gcr DEPLOY_CONFIG=prod.deploy.env
deploy_gcr: ## Deploy to Cloud Run service (DEPLOY_CONFIG=<file>)
ifndef DEPLOY_CONFIG
	$(error DEPLOY_CONFIG is required. Usage: make deploy_gcr DEPLOY_CONFIG=prod.deploy.env)
endif
	bash ./scripts/deploy_cloud_run.sh $(DEPLOY_CONFIG)

# Usage:
#   make invoke-api DEPLOY_CONFIG=stage.deploy.env ARGS="--health"
#   make invoke-api DEPLOY_CONFIG=stage.deploy.env ARGS="GET /api/list"
invoke-api: ## Call the deployed Cloud Run API behind IAM (DEPLOY_CONFIG=<file> ARGS="--health | <METHOD> <PATH>")
ifndef DEPLOY_CONFIG
	$(error DEPLOY_CONFIG is required. Usage: make invoke-api DEPLOY_CONFIG=stage.deploy.env ARGS="GET /api/list")
endif
	bash ./scripts/invoke_cloud_run.sh $(DEPLOY_CONFIG) $(ARGS)
{%- endif %}
{%- if include_cloud_run_jobs %}

# Usage:
#   make deploy_gcrj DEPLOY_CONFIG=prod.deploy.env
deploy_gcrj: ## Deploy to Cloud Run Job (DEPLOY_CONFIG=<file>)
ifndef DEPLOY_CONFIG
	$(error DEPLOY_CONFIG is required. Usage: make deploy_gcrj DEPLOY_CONFIG=prod.deploy.env)
endif
	bash ./scripts/deploy_cloud_run_job.sh $(DEPLOY_CONFIG)
{%- endif %}
{%- endif %}

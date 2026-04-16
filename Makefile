.PHONY: init lint test version generate-examples help

# ── Help ──────────────────────────────────────────────────────────────────────

help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*##' Makefile | awk -F ':.*##' '{printf "  %-15s %s\n", $$1, $$2}'

# ── Init ──────────────────────────────────────────────────────────────────────

init: ## Install dependencies
	uv sync --group dev

# ── Lint ──────────────────────────────────────────────────────────────────────

lint: ## Lint and format with ruff
	uv run ruff check --fix .
	uv run ruff format .

# ── Test ──────────────────────────────────────────────────────────────────────

test: ## Run tests
	uv run pytest

# ── Version ──────────────────────────────────────────────────────────────────

# Usage:
#   make version                  # show current version
#   make version BUMP=patch       # 0.1.0 → 0.1.1
#   make version BUMP=minor       # 0.1.0 → 0.2.0
#   make version BUMP=major       # 0.1.0 → 1.0.0

version: ## Show or bump version (BUMP=patch|minor|major)
ifdef BUMP
	uv version --bump $(BUMP)
else
	uv version
endif

# ── Generate ─────────────────────────────────────────────────────────────────

generate-examples: ## (Re)generate example projects from YAML files in examples/
	@for f in examples/*.yaml; do \
		echo "Generating from $$f ..."; \
		uv run gcp-uv-pytemplate --from-file "$$f" --output-dir examples/; \
		echo ""; \
	done

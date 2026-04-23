.PHONY: init lint test version generate-examples release-dry-run changelog help

# ── Help ──────────────────────────────────────────────────────────────────────

help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*##' Makefile | awk -F ':.*##' '{printf "  %-15s %s\n", $$1, $$2}'

# ── Init ──────────────────────────────────────────────────────────────────────

setup: ## Install dependencies and git hooks
	uv sync --group dev
	uv run pre-commit install --hook-type commit-msg

# ── Lint ──────────────────────────────────────────────────────────────────────

lint: ## Lint and format with ruff
	uv run ruff check --fix .
	uv run ruff format .

# ── Test ──────────────────────────────────────────────────────────────────────

test: ## Run tests
	uv run pytest

# ── Release ───────────────────────────────────────────────────────────────────

release-dry-run: ## Preview what PSR would release (no changes made)
	uv run semantic-release --noop version

changelog: ## Preview changelog entries since last tag
	uv run semantic-release changelog --unreleased

# ── Generate ─────────────────────────────────────────────────────────────────

generate-examples: ## (Re)generate example projects from YAML files in examples/
	@for f in examples/*.yaml; do \
		echo "Generating from $$f ..."; \
		uv run gcp-uv-pytemplate new --from-file "$$f" --output-dir examples/; \
		echo ""; \
	done

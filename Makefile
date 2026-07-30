.PHONY: init lint test test-all version generate-examples release-dry-run changelog help

PYTHON_VERSIONS := 3.10 3.11 3.12 3.13 3.14

# ── Help ──────────────────────────────────────────────────────────────────────

help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*##' Makefile | awk -F ':.*##' '{printf "  %-15s %s\n", $$1, $$2}'

# ── Init ──────────────────────────────────────────────────────────────────────

setup: ## Install dependencies and git hooks
	uv sync --group dev
	uv run pre-commit install --hook-type pre-commit --hook-type commit-msg

install: ## Install CLI and MCP server globally as editable (source changes apply immediately)
	uv tool install --editable ".[mcp]"

# ── Lint ──────────────────────────────────────────────────────────────────────

lint: ## Lint and format with ruff
	uv run ruff check --fix .
	uv run ruff format .

# ── Test ──────────────────────────────────────────────────────────────────────

test: ## Run tests
	uv run pytest

test-all: ## Run tests against all supported Python versions
	@for v in $(PYTHON_VERSIONS); do \
		echo "=== Python $$v ==="; \
		uv run --python $$v pytest || exit 1; \
	done

# ── Release ───────────────────────────────────────────────────────────────────

release-dry-run: ## Preview what PSR would release (no changes made)
	uv run semantic-release --noop version

changelog: ## Preview changelog entries since last tag
	uv run semantic-release changelog --unreleased

# ── Generate ─────────────────────────────────────────────────────────────────

generate-examples: ## (Re)generate example projects from YAML files in examples/
	@for f in examples/*.yaml; do \
		echo "Generating from $$f ..."; \
		uv run gcp-pytemplate new --from-file "$$f" --output-dir examples/ --overwrite; \
		echo ""; \
	done

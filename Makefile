.PHONY: init lint test test-all smoke version generate-examples release-dry-run changelog help

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

# Installs with pip, not uv sync, so dependencies resolve fresh rather than from uv.lock.
smoke: ## Build and smoke test a clean install of the wheel, including the [mcp] extra
	rm -rf .smoke
	uv build
	python3 -m venv .smoke
	.smoke/bin/pip install --quiet "$$(ls -t dist/*.whl | head -1)[mcp]"
	.smoke/bin/gcp-pytemplate --version
	.smoke/bin/python -c "import asyncio; from gcp_pytemplate.mcp_server import mcp; \
		t = sorted(x.name for x in asyncio.run(mcp.list_tools())); print('mcp tools:', t); \
		assert 'create_project' in t, 'MCP tools missing'"
	.smoke/bin/gcp-pytemplate new --project-name 'Smoke Test' --project-description ci \
		--gcp-project my-gcp-project --gcp-region us-west2 \
		--gcp-service-account sa@my-gcp-project.iam.gserviceaccount.com \
		--author-name CI --interfaces both --deploy-targets both \
		--output-dir .smoke/out --overwrite
	@test -f .smoke/out/smoke-test/pyproject.toml || { echo "ERROR: pyproject.toml not generated"; exit 1; }
	@if find .smoke/out -name '*.jinja' | grep -q .; then echo "ERROR: .jinja leaked into output"; exit 1; fi
	@if find .smoke/out \( -name '*.pyc' -o -name '__pycache__' \) | grep -q .; then \
		echo "ERROR: compiled artefacts leaked into output"; exit 1; fi
	@# -I skips binaries, which can contain matching byte sequences
	@if grep -rlI '{{' .smoke/out >/dev/null 2>&1; then echo "ERROR: unrendered Jinja in output"; exit 1; fi
	@echo "smoke test passed"

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

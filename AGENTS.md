# gcp-uv-pytemplate — Agent Guide

A CLI tool that scaffolds production-ready GCP Python projects. It renders a Jinja2 template tree into a new project directory.

## Commands

Use `make` for all core operations.

| Command | Description |
|---|---|
| `make setup` | Install dependencies and git hooks |
| `make install` | Install CLI and MCP server globally as editable (source changes apply immediately) |
| `make lint` | Lint and autoformat (ruff) |
| `make test` | Run tests |
| `make test-all` | Run tests against all supported Python versions (3.10–3.14) |
| `make generate-examples` | Regenerate `examples/` from the YAML files in `examples/*.yaml` |

Do not invoke `uv`, `ruff`, or `pytest` directly — use the make targets above.

### MCP server

```bash
gcp-uv-pytemplate-mcp   # starts the stdio MCP server (requires the [mcp] extra)
```

See the **MCP Server** section in `README.md` for installation and client config.

### Running the CLI

```bash
uv run gcp-uv-pytemplate new                              # interactive prompts
uv run gcp-uv-pytemplate new --from-file examples/api_project.yaml
uv run gcp-uv-pytemplate update <project-path> --components logging_config
```

## Project Layout

- `src/gcp_uv_pytemplate/main.py` — Typer CLI (`new` and `update` commands), input validation, Jinja2 context assembly
- `src/gcp_uv_pytemplate/render.py` — walks the template tree, renders file contents and paths with Jinja2
- `src/gcp_uv_pytemplate/templates/app/{{ project_slug }}/` — the project template (Jinja2; not valid Python until rendered)
- `examples/` — pre-generated example projects (`example-api-service`, `example-cli-job`) plus the YAML inputs used to generate them
- `src/gcp_uv_pytemplate/mcp_server.py` — MCP server (`create_project`, `update_project`, `list_components` tools)
- `tests/` — `test_render.py` (template output), `test_update.py` (update command), `test_mcp_server.py` (MCP tools)

## Key Rules

**CLI and MCP server must stay in sync.** When adding or changing inputs to the `new` command in `main.py` (parameters, defaults, validation, resolution logic), apply the equivalent change to `create_project` in `mcp_server.py`. Both share `_build_context()` for validation, but default resolution (e.g. git/gcloud config lookups) and the elicitation summary in `_format_summary` must be updated manually to match.

**Templates and examples must stay in sync.** When editing any file under `templates/`, apply the equivalent change to the corresponding file in `examples/example-api-service/` and/or `examples/example-cli-job/`. Alternatively, run `make generate-examples` to fully regenerate both examples (only appropriate when the change should affect all generated content, not for manual example-specific edits).

**Templates are excluded from ruff.** Files under `src/gcp_uv_pytemplate/templates/` contain Jinja2 syntax and are not valid Python — ruff is configured to skip them. Don't run linting on template files.

**Keep documentation in sync.** When making changes that affect functionality or interfaces (CLI flags, MCP tools, Python version support, make targets, project layout), update `README.md` and `AGENTS.md` to match. The Prerequisites, Usage, and Development sections of `README.md` and the Commands table in `AGENTS.md` are the primary places to check.

**Commit style: conventional commits.** Pre-commit hooks enforce the format. Prefixes and their effect on versioning and the changelog:

| Prefix | Version bump | In changelog |
|---|---|---|
| `feat:` | minor | yes |
| `fix:`, `perf:` | patch | yes |
| `docs:` | none | yes |
| `chore:`, `ci:`, `style:`, `test:`, `refactor:` | none | no |

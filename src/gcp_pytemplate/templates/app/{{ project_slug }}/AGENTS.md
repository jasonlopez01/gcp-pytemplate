# {{ project_name }} — Agent Guide

## Commands

Use `make` for all core operations. Run `make help` to list everything available.

| Command | Description |
|---|---|
| `make setup` | Install dependencies |
| `make lint` | Lint and autoformat (ruff) |
| `make test` | Run tests |
{%- if include_api %}
| `make start-api` | Start FastAPI locally on port 8080 |
{%- endif %}
{%- if include_cloud_run %}
| `make deploy_gcr DEPLOY_CONFIG=<file>` | Deploy to Cloud Run |
{%- endif %}
{%- if include_cloud_run_jobs %}
| `make deploy_gcrj DEPLOY_CONFIG=<file>` | Deploy as Cloud Run Job |
| `make execute-job DEPLOY_CONFIG=<file> [ARGS="..."]` | Execute an existing Cloud Run Job |
{%- endif %}

Do not invoke `uv`, `ruff`, `pytest`, or `uvicorn` directly — use the make targets above.
{% if include_cli %}
### Running the CLI locally

```bash
APP_CONFIG_FILE=local.env uv run {{ project_slug }} <command>
APP_CONFIG_FILE=local.env uv run {{ project_slug }} --help
```
{% endif %}
## Configuration

Runtime config is loaded from `config/app_configs/` via the `APP_CONFIG_FILE` env var. The `make start-api` target defaults to `local.env`. Set it explicitly when needed:

```bash
APP_CONFIG_FILE=stage.env make start-api
```

## Project Layout

- `src/{{ project_module }}/` — application source
{%- if include_api %}
  - `main_api.py` — FastAPI entrypoint
  - `api/` — routes and router
{%- endif %}
{%- if include_cli %}
  - `main_cli.py` — Typer CLI entrypoint
  - `cli/` — commands
{%- endif %}
  - `app/` — shared business logic
  - `config/` — app config, logging config, GCP env detection
- `deploy_configs/` — per-environment deploy settings (`stage`, `prod`)
{%- if include_cloud_run or include_cloud_run_jobs %}
- `scripts/` — deployment shell scripts (invoked via make)
{%- endif %}

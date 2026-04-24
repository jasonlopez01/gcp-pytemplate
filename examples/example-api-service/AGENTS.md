# Example API Service — Agent Guide

## Commands

Use `make` for all core operations. Run `make help` to list everything available.

| Command | Description |
|---|---|
| `make setup` | Install dependencies |
| `make lint` | Lint and autoformat (ruff) |
| `make test` | Run tests |
| `make start-api` | Start FastAPI locally on port 8080 |
| `make deploy_gcr DEPLOY_CONFIG=<file>` | Deploy to Cloud Run |

Do not invoke `uv`, `ruff`, `pytest`, or `uvicorn` directly — use the make targets above.

## Configuration

Runtime config is loaded from `config/app_configs/` via the `APP_CONFIG_FILE` env var. The `make start-api` target defaults to `local.env`. Set it explicitly when needed:

```bash
APP_CONFIG_FILE=stage.env make start-api
```

## Project Layout

- `src/example_api_service/` — application source
  - `main_api.py` — FastAPI entrypoint
  - `api/` — routes and router
  - `app/` — shared business logic
  - `config/` — app config, logging config, GCP env detection
- `deploy_configs/` — per-environment deploy settings (`stage`, `prod`)
- `scripts/` — deployment shell scripts (invoked via make)
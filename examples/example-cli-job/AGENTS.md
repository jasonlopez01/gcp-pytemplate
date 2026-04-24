# Example CLI Job — Agent Guide

## Commands

Use `make` for all core operations. Run `make help` to list everything available.

| Command | Description |
|---|---|
| `make setup` | Install dependencies |
| `make lint` | Lint and autoformat (ruff) |
| `make test` | Run tests |
| `make deploy_gcrj DEPLOY_CONFIG=<file>` | Deploy as Cloud Run Job |
| `make execute-job DEPLOY_CONFIG=<file> [ARGS="..."]` | Execute an existing Cloud Run Job |

Do not invoke `uv`, `ruff`, `pytest`, or `uvicorn` directly — use the make targets above.

### Running the CLI locally

```bash
APP_CONFIG_FILE=local.env uv run example-cli-job <command>
APP_CONFIG_FILE=local.env uv run example-cli-job --help
```

## Configuration

Runtime config is loaded from `config/app_configs/` via the `APP_CONFIG_FILE` env var. The `make start-api` target defaults to `local.env`. Set it explicitly when needed:

```bash
APP_CONFIG_FILE=stage.env make start-api
```

## Project Layout

- `src/example_cli_job/` — application source
  - `main_cli.py` — Typer CLI entrypoint
  - `cli/` — commands
  - `app/` — shared business logic
  - `config/` — app config, logging config, GCP env detection
- `deploy_configs/` — per-environment deploy settings (`stage`, `prod`)
- `scripts/` — deployment shell scripts (invoked via make)
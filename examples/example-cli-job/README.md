# Example CLI Job

A Typer CLI application deployed as a Cloud Run Job

## Prerequisites

- [Python 3.13+](https://www.python.org/downloads/)
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- [Google Cloud SDK (gcloud)](https://cloud.google.com/sdk/docs/install)

## Setup

```bash
make setup
```

## Commands

Run `make help` to see all available commands:

```
  setup           Install dependencies
  lint            Lint and format with ruff
  test            Run tests
  execute-job     Execute an existing Cloud Run Job (DEPLOY_CONFIG=<file> [ARGS="<cli args>"])
  deploy_gcrj     Deploy to Cloud Run Job (DEPLOY_CONFIG=<file>)
```

## Interface

This project includes a **Typer** CLI application for Cloud Run Jobs (`src/example_cli_job/main_cli.py`).

## Project Structure

```
example-cli-job/
├── deploy_configs/          # Per-environment deploy settings
│   ├── local.deploy.env
│   ├── dev.deploy.env
│   ├── stage.deploy.env
│   └── prod.deploy.env
├── scripts/                 # Deployment scripts
│   ├── deploy_cloud_run_job.sh
│   └── execute_cloud_run_job.sh
├── src/example_cli_job/
│   ├── __init__.py
│   ├── main_cli.py          # Typer CLI entrypoint
│   ├── cli/
│   │   └── commands.py
│   ├── app/                 # Core business logic
│   │   └── items.py
│   └── config/              # App and environment config
│       ├── app_config.py
│       ├── gcp_env.py
│       ├── logging_config.py
│       └── app_configs/
│           ├── local.env
│           ├── dev.env
│           ├── stage.env
│           └── prod.env
├── tests/
├── Makefile
├── Procfile
└── pyproject.toml
```

## Configuration

This project uses two layers of configuration files:

- **App configs** (`src/example_cli_job/config/app_configs/*.env`) — Application-level settings (feature flags, external service URLs, etc.) loaded at runtime via `APP_CONFIG_FILE`.
- **Deploy configs** (`deploy_configs/*.deploy.env`) — Infrastructure and deployment settings (GCP project, region, resource limits, etc.) used by the deployment scripts.

Both have per-environment variants: `local`, `dev`, `stage`, and `prod`.

### Why aren't the .env files gitignored?

This project takes the opinion that `.env` files are useful for service configuration and should be committed to source control. They make it easy to see and change values across environments — all in one place, version-tracked, and reviewable in PRs.

Any secrets needed should be managed via a secret manager (e.g., GCP Secret Manager) and fetched at runtime, rather than stored in static configuration files. Instead of specifying an API key or database password in a `.env` file, specify the secret's URI, ID, or resource path so it can be securely fetched at runtime.

If secrets in a local file are needed, a gitignored file like `secrets.env` or `secrets.local.env` could be added.
# Example API Service

A FastAPI service deployed to Cloud Run

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
  start-api       Start the FastAPI server locally (APP_CONFIG=local.env)
  deploy_gcr      Deploy to Cloud Run service (DEPLOY_CONFIG=<file>)
```

## Interface

This project includes a **FastAPI** application served via Cloud Run (`src/example_api_service/main_api.py`).

## Project Structure

```
example-api-service/
├── deploy_configs/          # Per-environment deploy settings
│   ├── stage.deploy.env
│   └── prod.deploy.env
├── scripts/                 # Deployment scripts
│   ├── deploy_cloud_run.sh
├── src/example_api_service/
│   ├── __init__.py
│   ├── main_api.py          # FastAPI entrypoint
│   ├── api/
│   │   └── router.py
│   ├── app/                 # Core business logic
│   │   └── models.py
│   └── config/              # App and environment config
│       ├── app_config.py
│       ├── gcp_env.py
│       ├── logging_config.py
│       └── app_configs/
│           ├── local.env
│           ├── stage.env
│           └── prod.env
├── tests/
├── Makefile
├── Procfile
└── pyproject.toml
```

## Configuration

This project uses two layers of configuration files:

- **App configs** (`src/example_api_service/config/app_configs/*.env`) — Application-level settings (feature flags, external service URLs, etc.) loaded at runtime via `APP_CONFIG_FILE`.
- **Deploy configs** (`deploy_configs/*.deploy.env`) — Infrastructure and deployment settings (GCP project, region, resource limits, etc.) used by the deployment scripts.

Both have per-environment variants: `local`, `stage`, and `prod`.

### .env Files and Secrets
**⚠️By default none of the .env files are gitignored and will be included in the git history, do not store senstive credentials there.**

`.env` files are useful for specifying service and deployment configuration. Having a set of files make it easy to see and change values across environments - like certain constants, deployment settings, etc. Exactly the kinf of thing we want to be version-tracked and reviewable in PRs.

Any secrets needed should be managed via a secret manager (e.g., GCP Secret Manager) and fetched at runtime, rather than stored in static configuration files. Instead of specifying an API key or database password in a `.env` file, specify the secret's URI, ID, or resource path so it can be securely fetched at runtime. If secrets in a local file are needed, a gitignored file like `secrets.env` or `secrets.prod.env` could be added.
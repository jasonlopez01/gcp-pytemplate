# {{ project_name }}

{{ project_description }}

## 📋 Prerequisites

- [Python 3.13+](https://www.python.org/downloads/)
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- [Google Cloud SDK (gcloud)](https://cloud.google.com/sdk/docs/install)

## 🚀 Setup

```bash
make setup
```

## 🛠️ Commands

Run `make help` to see all available commands:

```
  setup           Install dependencies
  lint            Lint and format with ruff
  test            Run tests
{%- if include_api %}
  start-api       Start the FastAPI server locally (APP_CONFIG=local.env)
{%- endif %}
{%- if include_cloud_run_jobs %}
  execute-job     Execute an existing Cloud Run Job (DEPLOY_CONFIG=<file> [ARGS="<cli args>"])
{%- endif %}
{%- if include_cloud_run %}
  deploy_gcr      Deploy to Cloud Run service (DEPLOY_CONFIG=<file>)
{%- endif %}
{%- if include_cloud_run_jobs %}
  deploy_gcrj     Deploy to Cloud Run Job (DEPLOY_CONFIG=<file>)
{%- endif %}
```
{% if include_api and include_cli %}

## 🔌 Interfaces

This project includes two interfaces:

- **API** — [FastAPI](https://fastapi.tiangolo.com) application served via Cloud Run (`src/{{ project_module }}/main_api.py`)
- **CLI** — [Typer](https://typer.tiangolo.com) command-line app for Cloud Run Jobs (`src/{{ project_module }}/main_cli.py`)
{% elif include_api %}
## 🔌 Interface

This project includes a **[FastAPI](https://fastapi.tiangolo.com)** application served via Cloud Run (`src/{{ project_module }}/main_api.py`).
{% elif include_cli %}
## 🔌 Interface

This project includes a **[Typer](https://typer.tiangolo.com)** CLI application for Cloud Run Jobs (`src/{{ project_module }}/main_cli.py`).
{% endif %}
## 📁 Project Structure

```
{{ project_slug }}/
├── deploy_configs/          # Per-environment deploy settings
│   ├── stage.deploy.env
│   └── prod.deploy.env
{%- if include_cloud_run or include_cloud_run_jobs %}
├── scripts/                 # Deployment scripts
{%- if include_cloud_run %}
│   ├── deploy_cloud_run.sh
{%- endif %}
{%- if include_cloud_run_jobs %}
│   ├── deploy_cloud_run_job.sh
│   └── execute_cloud_run_job.sh
{%- endif %}
{%- endif %}
├── src/{{ project_module }}/
│   ├── __init__.py
{%- if include_api %}
│   ├── main_api.py          # FastAPI entrypoint
│   ├── api/
│   │   └── router.py
{%- endif %}
{%- if include_cli %}
│   ├── main_cli.py          # Typer CLI entrypoint
│   ├── cli/
│   │   └── commands.py
{%- endif %}
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

## ⚙️ Configuration

This project uses two layers of configuration files:

- **App configs** (`src/{{ project_module }}/config/app_configs/*.env`) — Application-level settings (feature flags, external service URLs, etc.) loaded at runtime via `APP_CONFIG_FILE`.
- **Deploy configs** (`deploy_configs/*.deploy.env`) — Infrastructure and deployment settings (GCP project, region, resource limits, etc.) used by the deployment scripts.

Both have per-environment variants: `local`, `stage`, and `prod`.

### 🔒 .env Files and Secrets
**⚠️By default none of the .env files are gitignored and will be included in the git history, do not store senstive credentials there.**

`.env` files are useful for specifying service and deployment configuration. Having a set of files make it easy to see and change values across environments - like certain constants, deployment settings, etc. Exactly the kinf of thing we want to be version-tracked and reviewable in PRs.

Any secrets needed should be managed via a secret manager (e.g., GCP Secret Manager) and fetched at runtime, rather than stored in static configuration files. Instead of specifying an API key or database password in a `.env` file, specify the secret's URI, ID, or resource path so it can be securely fetched at runtime. If secrets in a local file are needed, a gitignored file like `secrets.env` or `secrets.prod.env` could be added.

---

Generated with [gcp-pytemplate](https://github.com/jasonlopez01/gcp-pytemplate).

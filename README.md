# gcp-uv-pytemplate

A CLI tool that scaffolds production-ready Python projects for Google Cloud Platform, using [uv](https://docs.astral.sh/uv/) for package management and [Cloud Native Buildpacks](https://buildpacks.io/) for containerization.

## What You Get

Generated projects include:

- **Configurable interfaces** — FastAPI (API), Typer (CLI), or both
  - Request/response validation with [Pydantic](https://docs.pydantic.dev/) across both interfaces
  - Auto-generated [OpenAPI](https://www.openapis.org/) spec and interactive docs via FastAPI
- **Configurable deploy targets** — Cloud Run (service), Cloud Run Jobs, or both
- **Per-environment config** — `local`, `dev`, `stage`, and `prod` for both app settings and deploy settings
- **Deployment scripts** — One-command deploys to Cloud Run and Cloud Run Jobs via `make`
- **Structured logging** with [structlog](https://www.structlog.org/), compatible with GCP logging formats
- **Linting and formatting** with [ruff](https://docs.astral.sh/ruff/)
- **Testing** with [pytest](https://docs.pytest.org/) (parallel execution via pytest-xdist)
- **Procfile-based** process definitions for Cloud Native Buildpacks

## Prerequisites

- [Python 3.13+](https://www.python.org/downloads/)
- [uv](https://docs.astral.sh/uv/getting-started/installation/)

## Install

```bash
# Install globally (editable for development)
uv tool install --editable /path/to/gcp-uv-pytemplate

# Or run without installing
uvx --from /path/to/gcp-uv-pytemplate gcp-uv-pytemplate new
```

## Usage

### Interactive

```bash
gcp-uv-pytemplate new
```

You'll be prompted for:

| Prompt | Description | Default |
|---|---|---|
| Project name | Human-readable name | — |
| Project description | Short description | — |
| GCP project | GCP project ID | `gcloud config` |
| GCP region | Compute region | `gcloud config` |
| GCP service account | Service account email | placeholder |
| Artifact Registry repo | GAR repository name | — |
| Interfaces | `api`, `cli`, or `both` | `both` |
| Deploy targets | `cloud-run`, `cloud-run-jobs`, or `both` | `both` |

### CLI flags

```bash
gcp-uv-pytemplate new \
  --project-name "My Service" \
  --project-description "Does things" \
  --gcp-project my-gcp-project \
  --gcp-region us-central1 \
  --interfaces api \
  --deploy-targets cloud-run \
  --output-dir ~/Projects
```

### From a YAML file

```bash
gcp-uv-pytemplate new --from-file config.yaml
```

```yaml
# config.yaml
project_name: My Service
project_description: Does things
gcp_project: my-gcp-project
gcp_region: us-central1
gcp_service_account: sa@my-gcp-project.iam.gserviceaccount.com
gcp_artifact_repo: my-repo
interfaces: both
deploy_targets: both
```

## Development

```bash
make setup    # install dependencies
make lint     # lint and format
make test     # run tests
make version  # show current version
```

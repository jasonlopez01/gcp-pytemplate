# gcp-uv-pytemplate

## Overview
gcp-uv-pytemplate is a CLI tool that scaffolds production-ready Python projects for Google Cloud Platform, using [uv](https://docs.astral.sh/uv/) for package management and [Cloud Native Buildpacks](https://buildpacks.io/) for containerization. With built-in uv tooling, optional FastAPI/Typer entrypoints, GCP authentication utilities, and a CI/CD release pipeline out of the box.

## Features

- 🔌 **Configurable interfaces** — FastAPI (API), Typer (CLI), or both
  - Request/response validation with [Pydantic](https://docs.pydantic.dev/) across both interfaces
  - Auto-generated [OpenAPI](https://www.openapis.org/) spec and interactive docs via FastAPI
- ⚙️ **Per-environment config** — `local`, `stage`, and `prod` for both app settings and similar deploy settings (can add more if needed)
- 🛠️ **Makefile with core commands** - One set of commands to test, lint, and deploy
- 🚀 **Deployment scripts** — One-command deploys to configurable deploy targets including Cloud Run and Cloud Run Jobs
- 📋 **Structured logging** with [structlog](https://www.structlog.org/), compatible with GCP logging formats
- ✨ **Linting and formatting** with [ruff](https://docs.astral.sh/ruff/)
- 🧪 **Testing** with [pytest](https://docs.pytest.org/) (parallel execution via pytest-xdist)
- 📦 **Procfile-based** process definitions for Cloud Native Buildpacks

## Prerequisites

- [Python 3.13+](https://www.python.org/downloads/)
- [uv](https://docs.astral.sh/uv/getting-started/installation/)

## Install

```bash
pip install gcp-pytemplate-uv
# or
uv pip install gcp-pytemplate-uv
```

## Usage

Follow instructions below to generate a new project. Once completed, navigate into your newly created project directory and follow the instructions in the README.md to complete the setup of your project and make it your own!

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

### Setup

1. Clone the repo
2. Run:
```bash
make help              # Show available commands
make setup             # Install dependencies and git hooks (run once after cloning)
make lint              # Lint and format with ruff
make test              # Run tests
make release-dry-run   # Preview next release without making changes
make changelog         # Preview unreleased changelog entries

# Install globally (editable for development)
uv tool install --editable /path/to/gcp-uv-pytemplate
```

## Contributing

Commits on this repo follow the [Conventional Commits](https://www.conventionalcommits.org/) spec. The `make setup` command installs a git hook that validates your commit message format automatically.

| Prefix | SemVer bump | Example |
|--------|-------------|---------|
| `fix:` | patch (0.1.0 → 0.1.1) | `fix: handle empty YAML config` |
| `feat:` | minor (0.1.0 → 0.2.0) | `feat: add terraform target option` |
| `feat!:` or `BREAKING CHANGE:` | major (0.1.0 → 1.0.0) | `feat!: rename CLI entry point` |
| `chore:`, `ci:`, `docs:`, `test:`, `refactor:`, `style:` | none | `chore: update dependencies` |

## Releasing

Releases are fully automated. When commits are merged to `main`, [python-semantic-release](https://python-semantic-release.readthedocs.io/) inspects the commit history since the last tag and, if there are any `fix:` or `feat:` commits, it:

1. Bumps the version in `pyproject.toml`
2. Updates `CHANGELOG.md`
3. Creates a git tag and GitHub Release
4. Builds and publishes to PyPI via OIDC (no token required)

If only non-releasable commits are present (`chore:`, `ci:`, etc.) no release is created.

To preview what the next release would look like without making any changes:

```bash
make release-dry-run   # preview next version
make changelog         # preview unreleased changelog entries
``` 
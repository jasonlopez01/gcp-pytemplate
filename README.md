# gcp-pytemplate

[![Supported Python versions](https://img.shields.io/badge/python-3.10_%7C_3.11_%7C_3.12_%7C_3.13_%7C_3.14-blue?labelColor=grey&color=blue)](https://pypi.org/project/gcp-pytemplate/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview
gcp-pytemplate is a CLI tool that scaffolds production-ready Python projects for Google Cloud Platform, using [uv](https://docs.astral.sh/uv/) for package management and [Cloud Native Buildpacks](https://buildpacks.io/) for containerization. With built-in uv tooling, optional FastAPI/Typer entrypoints, GCP authentication utilities, and a CI/CD release pipeline out of the box.

## Features

- 🐍 **Python env management with [UV](https://docs.astral.sh/uv/)**
- 🔌 **Configurable interfaces** — [FastAPI (API)](https://fastapi.tiangolo.com/), [Typer (CLI)](https://typer.tiangolo.com/), or both
  - Request/response validation with [Pydantic](https://docs.pydantic.dev/) across both interfaces
  - Auto-generated [OpenAPI](https://www.openapis.org/) spec and interactive docs via FastAPI
- ⚙️ **Per-environment config** — `local`, `stage`, and `prod` for both app settings and similar deploy settings (can add more if needed)
- 🛠️ **Makefile with core commands** - One set of commands to test, lint, and deploy
- 🚀 **Deployment scripts** — One-command deploys to configurable deploy targets including Cloud Run and Cloud Run Jobs
- 📋 **Structured logging** with [structlog](https://www.structlog.org/), compatible with GCP logging formats
- ✨ **Linting and formatting** with [ruff](https://docs.astral.sh/ruff/)
- 🧪 **Testing** with [pytest](https://docs.pytest.org/) (parallel execution via pytest-xdist)
- 📦 **Procfile-based** process definitions for Cloud Native Buildpacks
- 🤖 **Agent-ready** — generated projects include an `AGENTS.md` with commands, config conventions, and project layout for AI coding assistants

## Prerequisites

- [Python 3.10+](https://www.python.org/downloads/)
- [uv](https://docs.astral.sh/uv/getting-started/installation/)

## Install

```bash
pip install gcp-pytemplate
# or
uv pip install gcp-pytemplate
```

## Usage

Follow instructions below to generate a new project. Once completed, navigate into your newly created project directory and follow the instructions in the README.md to complete the setup of your project and make it your own!

### Interactive

```bash
gcp-pytemplate new
```

You'll be prompted for:

| Prompt | Description | Default |
|---|---|---|
| Project name | Human-readable name | — |
| Project description | Short description | — |
| GCP project | GCP project ID | `gcloud config` |
| GCP region | Compute region | `gcloud config` |
| GCP service account | Service account email | placeholder |
| Interfaces | `api`, `cli`, or `both` | `both` |
| Deploy targets | `cloud-run`, `cloud-run-jobs`, or `both` | `both` |

### CLI flags

```bash
gcp-pytemplate new \
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
gcp-pytemplate new --from-file config.yaml
```

```yaml
# config.yaml
project_name: My Service
project_description: Does things
gcp_project: my-gcp-project
gcp_region: us-central1
gcp_service_account: sa@my-gcp-project.iam.gserviceaccount.com
interfaces: both
deploy_targets: both
```

## MCP Server

The MCP server lets you scaffold and update projects using an LLM and natural language — no flags or YAML files required. Just describe what you want.

### Install

```bash
pip install gcp-pytemplate[mcp]
```

### Configure

**Claude Code** (`~/.claude/settings.json`):
```json
{
  "mcpServers": {
    "gcp-pytemplate": {
      "command": "gcp-pytemplate-mcp"
    }
  }
}
```

**Claude Desktop** (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):
```json
{
  "mcpServers": {
    "gcp-pytemplate": {
      "command": "gcp-pytemplate-mcp"
    }
  }
}
```

### Available tools

| Tool | Description |
|---|---|
| `create_project` | Scaffold a new project — accepts name, description, GCP config, interfaces, deploy targets |
| `update_project` | Update components of an existing project from the latest template |
| `list_components` | List the components available to update |

### Example prompts

> *"Create a CLI-only project called data-pipeline in us-central1 on GCP project my-org-prod"*

> *"Update the logging config in ~/Projects/my-service to the latest template"*

## Development

### Setup

1. Clone the repo
2. Run:
```bash
make help              # Show available commands
make setup             # Install dependencies and git hooks (run once after cloning)
make install           # Install CLI and MCP server globally as editable (source changes apply immediately)
make lint              # Lint and format with ruff
make test              # Run tests
make test-all          # Run tests against all supported Python versions (3.10–3.14)
make release-dry-run   # Preview next release without making changes
make changelog         # Preview unreleased changelog entries
```

`make install` runs `uv tool install --editable ".[mcp]"`, wiring up both the `gcp-pytemplate` and `gcp-pytemplate-mcp` entry points globally. Because it's editable, any changes you make to the source are picked up immediately without reinstalling.

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

1. Updates `CHANGELOG.md`
2. Creates a git tag and GitHub Release
3. Builds the package — version is derived from the git tag at build time via [hatch-vcs](https://github.com/ofek/hatch-vcs), so `pyproject.toml` carries no static version field
4. Publishes to PyPI via OIDC (no token required)

If only non-releasable commits are present (`chore:`, `ci:`, etc.) no release is created.

To preview what the next release would look like without making any changes:

```bash
make release-dry-run   # preview next version
make changelog         # preview unreleased changelog entries
``` 
import re
import subprocess
from pathlib import Path
from typing import Optional

import typer
import yaml
from rich.console import Console
from rich.tree import Tree

from gcp_uv_pytemplate.render import render_service

app = typer.Typer()
console = Console()


def slugify(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_-]+", "-", slug)
    slug = re.sub(r"^-+|-+$", "", slug)
    return slug


def _git_config(key: str) -> Optional[str]:
    try:
        result = subprocess.run(
            ["git", "config", key],
            capture_output=True, text=True, check=True,
        )
        return result.stdout.strip() or None
    except subprocess.CalledProcessError:
        return None


def _gcloud_config(key: str) -> Optional[str]:
    try:
        result = subprocess.run(
            ["gcloud", "config", "get", key],
            capture_output=True, text=True, check=True,
        )
        return result.stdout.strip() or None
    except subprocess.CalledProcessError:
        return None


def _load_yaml(path: Path) -> dict:
    with open(path) as f:
        data = yaml.safe_load(f)
    required = {"project_name", "project_description", "gcp_project", "gcp_region", "gcp_service_account", "gcp_artifact_repo"}
    missing = required - data.keys()
    if missing:
        raise typer.BadParameter(f"Missing required fields in {path.name}: {', '.join(sorted(missing))}")
    # Optional fields: interfaces, deploy_targets
    return data


@app.command()
def new(
    from_file: Optional[Path] = typer.Option(None, "--from-file", "-f", help="Path to a YAML file with template inputs"),
    project_name: Optional[str] = typer.Option(None, help="Human-readable project name"),
    project_description: Optional[str] = typer.Option(None, help="Short project description"),
    gcp_project: Optional[str] = typer.Option(None, help="GCP project ID (defaults to gcloud config)"),
    gcp_region: Optional[str] = typer.Option(None, help="GCP region (defaults to gcloud config compute/region)"),
    gcp_service_account: Optional[str] = typer.Option(None, help="GCP service account email"),
    gcp_artifact_repo: Optional[str] = typer.Option(None, help="Google Artifact Registry repository name"),
    author_name: Optional[str] = typer.Option(None, help="Author full name (defaults to git config user.name)"),
    author_email: Optional[str] = typer.Option(None, help="Author email (defaults to git config user.email)"),
    interfaces: Optional[str] = typer.Option(None, help="Interfaces to include: api, cli, or both"),
    deploy_targets: Optional[str] = typer.Option(None, help="Deploy targets: cloud-run, cloud-run-jobs, or both"),
    output_dir: Path = typer.Option(Path.cwd(), help="Directory to create the project in"),
) -> None:
    """Create a new GCP app project from the template."""
    if from_file:
        data = _load_yaml(from_file)
        project_name = project_name or data.get("project_name")
        project_description = project_description or data.get("project_description")
        gcp_project = gcp_project or data.get("gcp_project")
        gcp_region = gcp_region or data.get("gcp_region")
        gcp_service_account = gcp_service_account or data.get("gcp_service_account")
        gcp_artifact_repo = gcp_artifact_repo or data.get("gcp_artifact_repo")
        author_name = author_name or data.get("author_name")
        author_email = author_email or data.get("author_email")
        interfaces = interfaces or data.get("interfaces")
        deploy_targets = deploy_targets or data.get("deploy_targets")

    project_name = project_name or typer.prompt("Project name")
    project_description = project_description or typer.prompt("Project description")
    project_slug = slugify(project_name)

    resolved_author_name = author_name or _git_config("user.name") or "Your Name"
    resolved_author_email = author_email or _git_config("user.email") or "you@example.com"

    resolved_gcp_project = gcp_project or typer.prompt(
        "GCP project", default=_gcloud_config("project") or ""
    )
    resolved_gcp_region = gcp_region or typer.prompt(
        "GCP region", default=_gcloud_config("compute/region") or ""
    )
    resolved_gcp_service_account = gcp_service_account or typer.prompt(
        "GCP service account email",
        default=f"placeholder@{resolved_gcp_project}.iam.gserviceaccount.com",
    )
    resolved_gcp_artifact_repo = gcp_artifact_repo or typer.prompt("Artifact Registry repository name")

    # ── Interfaces & deploy targets ──────────────────────────────────────────
    INTERFACE_CHOICES = ["api", "cli", "both"]
    DEPLOY_TARGET_CHOICES = ["cloud-run", "cloud-run-jobs", "both"]

    interfaces = interfaces or typer.prompt(
        "Interfaces (api, cli, both)",
        default="both",
    )
    interfaces = interfaces.strip().lower()
    if interfaces not in INTERFACE_CHOICES:
        raise typer.BadParameter(f"Invalid interface: {interfaces}. Choose from: {', '.join(INTERFACE_CHOICES)}")

    deploy_targets = deploy_targets or typer.prompt(
        "Deploy targets (cloud-run, cloud-run-jobs, both)",
        default="both",
    )
    deploy_targets = deploy_targets.strip().lower()
    if deploy_targets not in DEPLOY_TARGET_CHOICES:
        raise typer.BadParameter(f"Invalid deploy target: {deploy_targets}. Choose from: {', '.join(DEPLOY_TARGET_CHOICES)}")

    # Override interfaces based on deploy targets
    if deploy_targets == "cloud-run" and interfaces == "cli":
        console.print("[yellow]Cloud Run requires the API interface — adding it.[/yellow]")
        interfaces = "both"
    if deploy_targets == "cloud-run-jobs" and interfaces == "api":
        console.print("[yellow]Cloud Run Jobs requires the CLI interface — adding it.[/yellow]")
        interfaces = "both"

    # Compute boolean flags
    include_api = interfaces in ("api", "both")
    include_cli = interfaces in ("cli", "both")
    include_cloud_run = deploy_targets in ("cloud-run", "both")
    include_cloud_run_jobs = deploy_targets in ("cloud-run-jobs", "both")

    project_module = project_slug.replace("-", "_")

    context = {
        "project_name": project_name,
        "project_slug": project_slug,
        "project_module": project_module,
        "project_description": project_description,
        "gcp_project": resolved_gcp_project,
        "gcp_region": resolved_gcp_region,
        "gcp_service_account": resolved_gcp_service_account,
        "gcp_artifact_repo": resolved_gcp_artifact_repo,
        "author_name": resolved_author_name,
        "author_email": resolved_author_email,
        "include_api": include_api,
        "include_cli": include_cli,
        "include_cloud_run": include_cloud_run,
        "include_cloud_run_jobs": include_cloud_run_jobs,
    }

    project_root = output_dir / project_slug
    if project_root.exists():
        overwrite = typer.confirm(
            f"Directory '{project_slug}' already exists. Overwrite?",
            default=False,
        )
        if not overwrite:
            console.print("[yellow]Aborted.[/yellow]")
            raise typer.Exit()

    console.print(f"\n[bold]Creating[/bold] [cyan]{project_name}[/cyan] → [green]{project_slug}[/green]")

    written = render_service(context, output_dir)

    # Save inputs so the project can be regenerated
    template_inputs = {
        "project_name": project_name,
        "project_description": project_description,
        "gcp_project": resolved_gcp_project,
        "gcp_region": resolved_gcp_region,
        "gcp_service_account": resolved_gcp_service_account,
        "gcp_artifact_repo": resolved_gcp_artifact_repo,
        "author_name": resolved_author_name,
        "author_email": resolved_author_email,
        "interfaces": interfaces,
        "deploy_targets": deploy_targets,
    }
    inputs_path = project_root / ".gcp-uv-pytemplate.yaml"
    inputs_path.write_text(yaml.dump(template_inputs, default_flow_style=False, sort_keys=False))
    written.append(inputs_path)

    tree = Tree(f"[green]{project_slug}/[/green]")
    _build_tree(tree, project_root, written)
    console.print(tree)

    console.print(f"\n[bold green]Done![/bold green] Project created at [cyan]{project_root}[/cyan]")


def _build_tree(branch: Tree, directory: Path, written: list[Path]) -> None:
    dirs: dict[Path, Tree] = {directory: branch}
    for file_path in sorted(written):
        parent = file_path.parent
        if parent not in dirs:
            parts = parent.relative_to(directory).parts
            current = directory
            current_branch = branch
            for part in parts:
                current = current / part
                if current not in dirs:
                    dirs[current] = current_branch.add(f"[blue]{part}/[/blue]")
                current_branch = dirs[current]
        dirs[parent].add(file_path.name)

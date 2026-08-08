import keyword
import re
import shutil
import subprocess
import sys
import tempfile
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import questionary
import typer
import yaml
from rich.console import Console
from rich.tree import Tree

from gcp_pytemplate.render import render_service

app = typer.Typer()


def _get_version() -> str:
    try:
        return version("gcp-pytemplate")
    except PackageNotFoundError:
        return "unknown"


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"gcp-pytemplate {_get_version()}")
        raise typer.Exit()


@app.callback()
def _main(
    version: bool = typer.Option(  # noqa: ARG001
        None, "--version", "-V", callback=_version_callback, is_eager=True, help="Show version and exit"
    ),
) -> None:
    pass


console = Console()

UPDATABLE_COMPONENTS: dict[str, list[str]] = {
    "cache": [
        "src/{project_module}/utils/cache.py",
        "tests/unit/test_cache.py",
    ],
    "gcp_auth": [
        "src/{project_module}/utils/gcp_auth/",
    ],
    "logging_config": [
        "src/{project_module}/config/logging_config.py",
    ],
}

_COMPONENT_LABELS = {
    "cache": "utils/cache.py + tests/unit/test_cache.py",
    "gcp_auth": "utils/gcp_auth/",
    "logging_config": "config/logging_config.py",
}


def _stdin_is_tty() -> bool:
    """questionary raises an opaque OSError instead of failing cleanly when stdin is not a terminal."""
    try:
        return sys.stdin.isatty()
    except (AttributeError, ValueError):
        return False


def _select(message: str, choices: list[str], default: str) -> str:
    """Prompt for one of choices, falling back to default when there is no terminal to prompt on."""
    if not _stdin_is_tty():
        console.print(f"[yellow]{message} not a terminal, using default '{default}'.[/yellow]")
        return default
    answer = questionary.select(message, choices=choices, default=default).ask()
    if answer is None:  # interrupted
        raise typer.Exit(1)
    return answer


def _confirm(message: str) -> bool:
    """Ask for confirmation, declining when there is no terminal to prompt on."""
    if not _stdin_is_tty():
        return False
    return bool(questionary.confirm(message, default=False).ask())


def slugify(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_-]+", "-", slug)
    slug = re.sub(r"^-+|-+$", "", slug)
    return slug


def _git_config(key: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "config", key],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip() or None
    except subprocess.CalledProcessError:
        return None


def _gcloud_config(key: str) -> str | None:
    try:
        result = subprocess.run(
            ["gcloud", "config", "get", key],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip() or None
    except subprocess.CalledProcessError:
        return None


def _load_yaml(path: Path) -> dict:
    try:
        with open(path) as f:
            data = yaml.safe_load(f)
    except FileNotFoundError:
        raise typer.BadParameter(f"Config file not found: {path}")
    except yaml.YAMLError as e:
        raise typer.BadParameter(f"Invalid YAML in {path.name}: {e}")
    if not isinstance(data, dict):
        raise typer.BadParameter(f"{path.name} must contain a YAML mapping, got: {type(data).__name__}")
    required = {
        "project_name",
        "project_description",
        "gcp_project",
        "gcp_region",
        "gcp_service_account",
    }
    missing = required - data.keys()
    if missing:
        raise typer.BadParameter(f"Missing required fields in {path.name}: {', '.join(sorted(missing))}")
    return data


_GCP_VALIDATIONS: list[tuple[str, str, str]] = [
    (
        "gcp_project",
        r"^[a-z][a-z0-9\-]{4,28}[a-z0-9]$",
        "lowercase letters, digits, and hyphens (6-30 chars, must start with a letter)",
    ),
    ("gcp_region", r"^[a-z]+-[a-z]+[0-9]+$", "e.g. us-central1, europe-west4"),
    (
        "gcp_service_account",
        r"^[a-z0-9\-]+@[a-z0-9\-]+\.iam\.gserviceaccount\.com$",
        "e.g. my-sa@my-project.iam.gserviceaccount.com",
    ),
]


def _build_context(data: dict) -> dict:
    """Build the full Jinja2 render context from a parsed YAML inputs dict."""
    for field, pattern, hint in _GCP_VALIDATIONS:
        value = data.get(field, "")
        if not re.fullmatch(pattern, str(value)):
            raise typer.BadParameter(f"Invalid {field} {value!r} — expected {hint}")

    project_name = data["project_name"]
    project_slug = slugify(project_name)
    project_module = project_slug.replace("-", "_")

    # An empty slug would resolve the project root to the output directory itself.
    if not project_module.isidentifier() or keyword.iskeyword(project_module):
        raise typer.BadParameter(
            f"Invalid project_name {project_name!r} — must start with a letter and contain at least "
            "one letter, digit, space, hyphen, or underscore"
        )

    interfaces = data.get("interfaces", "both").strip().lower()
    deploy_targets = data.get("deploy_targets", "both").strip().lower()

    include_api = interfaces in ("api", "both")
    include_cli = interfaces in ("cli", "both")
    include_cloud_run = deploy_targets in ("cloud-run", "both")
    include_cloud_run_jobs = deploy_targets in ("cloud-run-jobs", "both")

    return {
        "project_name": project_name,
        "project_slug": project_slug,
        "project_module": project_module,
        "project_description": data["project_description"],
        "gcp_project": data["gcp_project"],
        "gcp_region": data["gcp_region"],
        "gcp_service_account": data["gcp_service_account"],
        "author_name": data.get("author_name", ""),
        "include_api": include_api,
        "include_cli": include_cli,
        "include_cloud_run": include_cloud_run,
        "include_cloud_run_jobs": include_cloud_run_jobs,
    }


def _resolve_component_paths(component_names: list[str], project_module: str) -> list[str]:
    """Resolve component names to template-relative path strings."""
    paths: list[str] = []
    for name in component_names:
        for fragment in UPDATABLE_COMPONENTS[name]:
            paths.append(fragment.format(project_module=project_module))
    return paths


def _validate_rel_paths(rel_paths: list[str]) -> None:
    """Reject update paths that would resolve outside the target project."""
    for p in rel_paths:
        if Path(p).is_absolute() or ".." in Path(p).parts:
            raise typer.BadParameter(f"Invalid path '{p}' — must be a relative path within the project")


def _copy_from_temp(
    temp_project_root: Path,
    dest_project_root: Path,
    rel_paths: list[str],
) -> list[Path]:
    """Copy files/dirs from the rendered temp project into the real project.

    Returns list of destination paths that were written.
    """
    written: list[Path] = []

    for rel in rel_paths:
        src = temp_project_root / rel
        dest = dest_project_root / rel

        if rel.endswith("/"):
            # Directory: copy all files recursively
            if not src.is_dir():
                console.print(f"[yellow]Warning: expected directory not found in template: {rel}[/yellow]")
                continue
            for src_file in sorted(src.rglob("*")):
                if src_file.is_dir():
                    continue
                file_rel = src_file.relative_to(src)
                dest_file = dest / file_rel
                dest_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_file, dest_file)
                written.append(dest_file)
        else:
            if not src.is_file():
                console.print(f"[yellow]Warning: expected file not found in template: {rel}[/yellow]")
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
            written.append(dest)

    return written


@app.command()
def new(
    from_file: Path | None = typer.Option(None, "--from-file", "-f", help="Path to a YAML file with template inputs"),
    project_name: str | None = typer.Option(None, help="Human-readable project name"),
    project_description: str | None = typer.Option(None, help="Short project description"),
    gcp_project: str | None = typer.Option(None, help="GCP project ID (defaults to gcloud config)"),
    gcp_region: str | None = typer.Option(None, help="GCP region (defaults to gcloud config compute/region)"),
    gcp_service_account: str | None = typer.Option(None, help="GCP service account email"),
    author_name: str | None = typer.Option(None, help="Author full name (prompts, defaulting to git config user.name)"),
    interfaces: str | None = typer.Option(None, help="Interfaces to include: api, cli, or both"),
    deploy_targets: str | None = typer.Option(None, help="Deploy targets: cloud-run, cloud-run-jobs, or both"),
    output_dir: Path = typer.Option(Path.cwd(), help="Directory to create the project in"),
    overwrite: bool = typer.Option(
        False, "--overwrite", help="Replace an existing project directory without prompting"
    ),
) -> None:
    """Create a new GCP app project from the template."""
    if from_file:
        data = _load_yaml(from_file)
        project_name = project_name or data.get("project_name")
        project_description = project_description or data.get("project_description")
        gcp_project = gcp_project or data.get("gcp_project")
        gcp_region = gcp_region or data.get("gcp_region")
        gcp_service_account = gcp_service_account or data.get("gcp_service_account")
        author_name = author_name or data.get("author_name")
        interfaces = interfaces or data.get("interfaces")
        deploy_targets = deploy_targets or data.get("deploy_targets")

    project_name = project_name or typer.prompt("Project name")
    project_description = project_description or typer.prompt("Project description")

    # Prompted rather than read silently from git config, so the user sees what gets written.
    # Left empty without a terminal; the template omits the authors field when it is blank.
    if author_name is None:
        author_name = typer.prompt("Author name", default=_git_config("user.name") or "") if _stdin_is_tty() else ""
    resolved_author_name = author_name.strip()

    resolved_gcp_project = gcp_project or typer.prompt("GCP project", default=_gcloud_config("project") or "")
    resolved_gcp_region = gcp_region or typer.prompt("GCP region", default=_gcloud_config("compute/region") or "")
    resolved_gcp_service_account = gcp_service_account or typer.prompt(
        "GCP service account email",
        default=f"placeholder@{resolved_gcp_project}.iam.gserviceaccount.com",
    )

    if not interfaces:
        interfaces = _select("Interfaces:", choices=["both", "api", "cli"], default="both")

    if not deploy_targets:
        deploy_targets = _select("Deploy targets:", choices=["both", "cloud-run", "cloud-run-jobs"], default="both")

    if deploy_targets == "cloud-run" and interfaces == "cli":
        console.print("[yellow]Cloud Run requires the API interface — adding it.[/yellow]")
        interfaces = "both"
    if deploy_targets == "cloud-run-jobs" and interfaces == "api":
        console.print("[yellow]Cloud Run Jobs requires the CLI interface — adding it.[/yellow]")
        interfaces = "both"

    context = _build_context(
        {
            "project_name": project_name,
            "project_description": project_description,
            "gcp_project": resolved_gcp_project,
            "gcp_region": resolved_gcp_region,
            "gcp_service_account": resolved_gcp_service_account,
            "author_name": resolved_author_name,
            "interfaces": interfaces,
            "deploy_targets": deploy_targets,
        }
    )

    project_slug = context["project_slug"]
    project_root = output_dir / project_slug
    if project_root.exists() and any(project_root.iterdir()):
        confirmed = overwrite or _confirm(f"Directory '{project_slug}' already exists. Overwrite?")
        if not confirmed:
            console.print(
                f"[yellow]Aborted.[/yellow] '{project_slug}' already exists — pass --overwrite to replace it."
            )
            raise typer.Exit(1)
        shutil.rmtree(project_root)

    console.print(f"\n[bold]Creating[/bold] [cyan]{project_name}[/cyan] → [green]{project_slug}[/green]")

    written = render_service(context, output_dir)

    template_inputs = {
        "project_name": project_name,
        "project_description": project_description,
        "gcp_project": resolved_gcp_project,
        "gcp_region": resolved_gcp_region,
        "gcp_service_account": resolved_gcp_service_account,
        "author_name": resolved_author_name,
        "interfaces": interfaces,
        "deploy_targets": deploy_targets,
    }
    inputs_path = project_root / ".gcp-pytemplate.yaml"
    inputs_path.write_text(yaml.dump(template_inputs, default_flow_style=False, sort_keys=False))
    written.append(inputs_path)

    tree = Tree(f"[green]{project_slug}/[/green]")
    _build_tree(tree, project_root, written)
    console.print(tree)

    console.print(f"\n[bold green]Done![/bold green] Project created at [cyan]{project_root}[/cyan]")


@app.command()
def update(
    project_path: Path = typer.Argument(..., help="Path to an existing generated project"),
    components: str | None = typer.Option(
        None,
        help=f"Comma-separated components to update: {', '.join(UPDATABLE_COMPONENTS)}",
    ),
    files: str | None = typer.Option(
        None,
        help="Comma-separated file/folder paths relative to the project root to update",
    ),
) -> None:
    """Update components of an existing project from the latest template."""
    inputs_file = project_path / ".gcp-pytemplate.yaml"
    if not project_path.is_dir():
        console.print(f"[red]Error: '{project_path}' is not a directory.[/red]")
        raise typer.Exit(1)
    if not inputs_file.exists():
        console.print(f"[red]Error: '{inputs_file}' not found. Is this a gcp-pytemplate project?[/red]")
        raise typer.Exit(1)

    data = _load_yaml(inputs_file)
    context = _build_context(data)
    project_module = context["project_module"]
    project_slug = context["project_slug"]

    # Determine which relative paths to update
    rel_paths: list[str]

    if files:
        rel_paths = [f.strip() for f in files.split(",") if f.strip()]
        _validate_rel_paths(rel_paths)
    elif components:
        component_names = [c.strip() for c in components.split(",") if c.strip()]
        invalid = [c for c in component_names if c not in UPDATABLE_COMPONENTS]
        if invalid:
            console.print(
                f"[red]Unknown components: {', '.join(invalid)}. Available: {', '.join(UPDATABLE_COMPONENTS)}[/red]"
            )
            raise typer.Exit(1)
        rel_paths = _resolve_component_paths(component_names, project_module)
    else:
        if not _stdin_is_tty():
            console.print(
                "[red]Error: no terminal to prompt on — pass --components or --files "
                f"(available components: {', '.join(UPDATABLE_COMPONENTS)}).[/red]"
            )
            raise typer.Exit(1)
        choices = [
            questionary.Choice(
                title=f"{name}  ({label})",
                value=name,
            )
            for name, label in _COMPONENT_LABELS.items()
        ]
        selected: list[str] = questionary.checkbox(
            "Select components to update:",
            choices=choices,
        ).ask()

        if not selected:
            console.print("[yellow]No components selected. Aborted.[/yellow]")
            raise typer.Exit()

        rel_paths = _resolve_component_paths(selected, project_module)

    console.print(f"\n[bold]Updating[/bold] [cyan]{project_slug}[/cyan] at [green]{project_path}[/green]")

    with tempfile.TemporaryDirectory() as tmp_dir:
        render_service(context, Path(tmp_dir))
        temp_project_root = Path(tmp_dir) / project_slug
        written = _copy_from_temp(temp_project_root, project_path, rel_paths)

    if written:
        console.print("\nUpdated files:")
        for path in written:
            console.print(f"  [green]{path.relative_to(project_path)}[/green]")
        console.print(f"\n[bold green]Done![/bold green] {len(written)} file(s) updated.")
    else:
        console.print("[yellow]No files were updated.[/yellow]")


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

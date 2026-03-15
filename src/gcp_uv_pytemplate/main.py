import re
import subprocess
from pathlib import Path
from typing import Optional

import typer
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


@app.command()
def new(
    project_name: str = typer.Option(..., prompt=True, help="Human-readable project name"),
    project_description: str = typer.Option(..., prompt=True, help="Short project description"),
    author_name: Optional[str] = typer.Option(None, help="Author full name (defaults to git config user.name)"),
    author_email: Optional[str] = typer.Option(None, help="Author email (defaults to git config user.email)"),
    output_dir: Path = typer.Option(Path.cwd(), help="Directory to create the project in"),
) -> None:
    """Create a new GCP app project from the template."""
    project_slug = slugify(project_name)

    resolved_author_name = author_name or _git_config("user.name") or "Your Name"
    resolved_author_email = author_email or _git_config("user.email") or "you@example.com"

    context = {
        "project_name": project_name,
        "project_slug": project_slug,
        "project_description": project_description,
        "author_name": resolved_author_name,
        "author_email": resolved_author_email,
    }

    console.print(f"\n[bold]Creating[/bold] [cyan]{project_name}[/cyan] → [green]{project_slug}[/green]")

    written = render_service(context, output_dir)

    tree = Tree(f"[green]{project_slug}/[/green]")
    project_root = output_dir / project_slug
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

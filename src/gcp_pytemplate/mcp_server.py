import tempfile
from pathlib import Path

import typer
import yaml
from mcp.server.fastmcp import Context, FastMCP
from mcp.shared.exceptions import McpError
from pydantic import BaseModel

from gcp_pytemplate.main import (
    UPDATABLE_COMPONENTS,
    _build_context,
    _copy_from_temp,
    _get_version,
    _git_config,
    _load_yaml,
    _resolve_component_paths,
    slugify,
)
from gcp_pytemplate.render import render_service

mcp = FastMCP("gcp-pytemplate")


class _Confirmation(BaseModel):
    confirmed: bool = True


def _format_summary(
    project_name: str,
    project_description: str,
    author_name: str,
    author_email: str,
    gcp_project: str,
    gcp_region: str,
    gcp_service_account: str,
    interfaces: str,
    deploy_targets: str,
    project_root: Path,
) -> str:
    slug = slugify(project_name)
    return (
        f"Please confirm the following project settings before creation:\n\n"
        f"  project_name:        {project_name}\n"
        f"  project_slug:        {slug}\n"
        f"  project_description: {project_description}\n"
        f"  author_name:         {author_name or '(empty)'}\n"
        f"  author_email:        {author_email or '(empty)'}\n"
        f"  gcp_project:         {gcp_project}\n"
        f"  gcp_region:          {gcp_region}\n"
        f"  gcp_service_account: {gcp_service_account}\n"
        f"  interfaces:          {interfaces}\n"
        f"  deploy_targets:      {deploy_targets}\n"
        f"  output_dir:          {project_root}\n\n"
        f"Set confirmed=true to proceed or confirmed=false to cancel."
    )


@mcp.tool()
def get_version() -> str:
    """Return the installed version of gcp-pytemplate."""
    return f"gcp-pytemplate {_get_version()}"


@mcp.tool()
async def create_project(
    project_name: str,
    project_description: str,
    gcp_project: str,
    gcp_region: str,
    gcp_service_account: str,
    interfaces: str = "both",
    deploy_targets: str = "both",
    output_dir: str | None = None,
    author_name: str | None = None,
    author_email: str | None = None,
    ctx: Context | None = None,
) -> str:
    """Scaffold a new GCP Python project from the gcp-pytemplate template.

    interfaces: "api" (FastAPI), "cli" (Typer), or "both"
    deploy_targets: "cloud-run", "cloud-run-jobs", or "both"
    output_dir: directory to create the project in (defaults to current directory)
    """
    resolved_author_name = author_name or _git_config("user.name") or ""
    resolved_author_email = author_email or _git_config("user.email") or ""
    out = Path(output_dir) if output_dir else Path.cwd()
    project_root = out / slugify(project_name)

    if ctx is not None:
        summary = _format_summary(
            project_name=project_name,
            project_description=project_description,
            author_name=resolved_author_name,
            author_email=resolved_author_email,
            gcp_project=gcp_project,
            gcp_region=gcp_region,
            gcp_service_account=gcp_service_account,
            interfaces=interfaces,
            deploy_targets=deploy_targets,
            project_root=project_root,
        )
        try:
            result = await ctx.elicit(summary, _Confirmation)
            if result.action != "accept" or not result.data.confirmed:
                return "Project creation cancelled."
        except McpError:
            pass  # client doesn't support elicitation — proceed silently

    try:
        context = _build_context({
            "project_name": project_name,
            "project_description": project_description,
            "gcp_project": gcp_project,
            "gcp_region": gcp_region,
            "gcp_service_account": gcp_service_account,
            "interfaces": interfaces,
            "deploy_targets": deploy_targets,
            "author_name": resolved_author_name,
            "author_email": resolved_author_email,
        })
    except typer.BadParameter as e:
        return f"Error: {e}"

    written = render_service(context, out)
    project_root = out / context["project_slug"]

    template_inputs = {
        "project_name": project_name,
        "project_description": project_description,
        "gcp_project": gcp_project,
        "gcp_region": gcp_region,
        "gcp_service_account": gcp_service_account,
        "author_name": resolved_author_name,
        "author_email": resolved_author_email,
        "interfaces": interfaces,
        "deploy_targets": deploy_targets,
    }
    inputs_path = project_root / ".gcp-pytemplate.yaml"
    inputs_path.write_text(yaml.dump(template_inputs, default_flow_style=False, sort_keys=False))

    author_display = f"{resolved_author_name} <{resolved_author_email}>" if resolved_author_name or resolved_author_email else "(none)"
    return (
        f"Created '{context['project_slug']}' with {len(written)} files at {project_root}\n\n"
        f"Settings used:\n"
        f"  author:          {author_display}\n"
        f"  gcp_project:     {gcp_project}\n"
        f"  gcp_region:      {gcp_region}\n"
        f"  service_account: {gcp_service_account}\n"
        f"  interfaces:      {interfaces}\n"
        f"  deploy_targets:  {deploy_targets}"
    )


@mcp.tool()
def update_project(
    project_path: str,
    components: str | None = None,
    files: str | None = None,
) -> str:
    """Update components of an existing gcp-pytemplate project from the latest template.

    project_path: path to an existing generated project directory
    components: comma-separated component names to update (e.g. "cache,logging_config")
                run list_components() to see available options
    files: comma-separated file/folder paths relative to the project root to update
           (alternative to components)
    """
    path = Path(project_path)
    inputs_file = path / ".gcp-pytemplate.yaml"

    if not path.is_dir():
        return f"Error: '{project_path}' is not a directory."
    if not inputs_file.exists():
        return f"Error: '{inputs_file}' not found. Is this a gcp-pytemplate project?"

    try:
        data = _load_yaml(inputs_file)
        context = _build_context(data)
    except Exception as e:
        return f"Error loading project config: {e}"

    project_module = context["project_module"]
    project_slug = context["project_slug"]

    if files:
        rel_paths = [f.strip() for f in files.split(",") if f.strip()]
        for p in rel_paths:
            if Path(p).is_absolute() or ".." in Path(p).parts:
                return f"Error: invalid path '{p}' — must be a relative path within the project"
    elif components:
        component_names = [c.strip() for c in components.split(",") if c.strip()]
        invalid = [c for c in component_names if c not in UPDATABLE_COMPONENTS]
        if invalid:
            available = ", ".join(UPDATABLE_COMPONENTS)
            return f"Error: unknown components: {', '.join(invalid)}. Available: {available}"
        rel_paths = _resolve_component_paths(component_names, project_module)
    else:
        return "Error: provide either 'components' or 'files'. Run list_components() to see options."

    with tempfile.TemporaryDirectory() as tmp_dir:
        render_service(context, Path(tmp_dir))
        temp_project_root = Path(tmp_dir) / project_slug
        written = _copy_from_temp(temp_project_root, path, rel_paths)

    if not written:
        return "No files were updated."

    updated = [str(p.relative_to(path)) for p in written]
    return f"Updated {len(written)} file(s) in '{project_slug}':\n" + "\n".join(f"  {p}" for p in updated)


@mcp.tool()
def list_components() -> str:
    """List the updatable components available for use with update_project."""
    lines = ["Available components for update_project():"]
    for name, paths in UPDATABLE_COMPONENTS.items():
        lines.append(f"  {name}")
        for p in paths:
            lines.append(f"    - {p}")
    return "\n".join(lines)


def main() -> None:
    mcp.run()

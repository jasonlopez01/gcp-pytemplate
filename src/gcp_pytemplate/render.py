import importlib.resources as pkg_resources
from pathlib import Path

import jinja2

# Files/directories to exclude based on context flags.
# Each rule is (path_fragment, required_flag).
_EXCLUSION_RULES = [
    ("src/{{ project_module }}/api/", "include_api"),
    ("src/{{ project_module }}/main_api.py", "include_api"),
    ("tests/unit/test_base_api.py", "include_api"),
    ("src/{{ project_module }}/cli/", "include_cli"),
    ("src/{{ project_module }}/main_cli.py", "include_cli"),
    ("tests/unit/test_base_cli.py", "include_cli"),
    ("scripts/deploy_cloud_run.sh", "include_cloud_run"),
    ("scripts/invoke_cloud_run.sh", "include_cloud_run"),
    ("scripts/deploy_cloud_run_job.sh", "include_cloud_run_jobs"),
    ("scripts/execute_cloud_run_job.sh", "include_cloud_run_jobs"),
]


def _should_skip(rel_path: str, context: dict) -> bool:
    """Return True if rel_path should be excluded based on context flags."""
    # Render the path fragment templates with the actual module name
    for fragment, flag in _EXCLUSION_RULES:
        rendered_fragment = jinja2.Template(fragment).render(**context)
        if rel_path == rendered_fragment or rel_path.startswith(rendered_fragment):
            if not context.get(flag, True):
                return True
    return False


def render_service(context: dict, output_dir: Path) -> list[Path]:
    """Render the service template into output_dir/<project_slug>/.

    Returns a list of files written.
    """
    ref = pkg_resources.files("gcp_pytemplate").joinpath("templates/app/{{ project_slug }}")

    written: list[Path] = []

    with pkg_resources.as_file(ref) as template_root:
        for src_path in sorted(template_root.rglob("*")):
            if src_path.is_dir() or src_path.name == ".gitkeep":
                continue

            # Render any Jinja variables in the file path itself
            rel_str = str(src_path.relative_to(template_root))
            rendered_rel = jinja2.Template(rel_str).render(**context)

            if _should_skip(rendered_rel, context):
                continue

            dest_path = output_dir / context["project_slug"] / rendered_rel
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            try:
                rendered_content = jinja2.Template(src_path.read_text()).render(**context)
            except jinja2.TemplateError as e:
                raise RuntimeError(f"Template error in {src_path.name}: {e}") from e
            dest_path.write_text(rendered_content)
            written.append(dest_path)

    return written

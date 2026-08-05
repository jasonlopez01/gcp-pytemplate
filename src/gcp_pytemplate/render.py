import importlib.resources as pkg_resources
import shutil
from pathlib import Path

import jinja2

# Never copied into a generated project: OS and editor metadata can turn up anywhere in the tree.
_SKIP_FILENAMES = frozenset({".gitkeep", ".DS_Store"})

# Stripped from the rendered path, so a template file can be named to avoid being mistaken for a
# real one. pyproject.toml uses this: left under its real name, GitHub's dependency graph picks it
# up as a pip manifest and fails on the Jinja2 syntax.
_TEMPLATE_SUFFIX = ".jinja"

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


def _render_tree(context: dict, output_dir: Path, template_root: Path) -> list[Path]:
    """Walk template_root and write the rendered result into output_dir/<project_slug>/."""
    written: list[Path] = []

    for src_path in sorted(template_root.rglob("*")):
        if src_path.is_dir() or src_path.name in _SKIP_FILENAMES:
            continue

        # Render any Jinja variables in the file path itself
        rel_str = str(src_path.relative_to(template_root))
        rendered_rel = jinja2.Template(rel_str).render(**context)

        # Strip before the exclusion check so rules can be written against the final path.
        if rendered_rel.endswith(_TEMPLATE_SUFFIX):
            rendered_rel = rendered_rel[: -len(_TEMPLATE_SUFFIX)]

        if _should_skip(rendered_rel, context):
            continue

        dest_path = output_dir / context["project_slug"] / rendered_rel
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            template_text = src_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            # Not text, so there is nothing to render; ship the asset through untouched.
            shutil.copyfile(src_path, dest_path)
            written.append(dest_path)
            continue

        try:
            # keep_trailing_newline: Jinja drops the final newline by default, which leaves
            # every rendered file without one and fails the generated project's own formatter.
            rendered_content = jinja2.Template(template_text, keep_trailing_newline=True).render(**context)
        except jinja2.TemplateError as e:
            raise RuntimeError(f"Template error in {src_path.name}: {e}") from e

        # newline="" keeps LF endings in rendered shell scripts and Procfiles on Windows hosts,
        # where the default would translate them to CRLF and break the Linux container image.
        dest_path.write_text(rendered_content, encoding="utf-8", newline="")
        written.append(dest_path)

    return written


def render_service(context: dict, output_dir: Path, template_root: Path | None = None) -> list[Path]:
    """Render the service template into output_dir/<project_slug>/.

    template_root overrides the packaged template tree so tests can render a fixture instead.

    Returns a list of files written.
    """
    if template_root is not None:
        return _render_tree(context, output_dir, template_root)

    ref = pkg_resources.files("gcp_pytemplate").joinpath("templates/app/{{ project_slug }}")
    with pkg_resources.as_file(ref) as packaged_root:
        return _render_tree(context, output_dir, Path(packaged_root))

import importlib.resources as pkg_resources
from pathlib import Path

import jinja2


def render_service(context: dict, output_dir: Path) -> list[Path]:
    """Render the service template into output_dir/<project_slug>/.

    Returns a list of files written.
    """
    ref = pkg_resources.files("gcp_uv_pytemplate").joinpath(
        "templates/app/{{ project_slug }}"
    )

    written: list[Path] = []

    with pkg_resources.as_file(ref) as template_root:
        for src_path in sorted(template_root.rglob("*")):
            if src_path.is_dir() or src_path.name == ".gitkeep":
                continue

            # Render any Jinja variables in the file path itself
            rel_str = str(src_path.relative_to(template_root))
            rendered_rel = jinja2.Template(rel_str).render(**context)

            dest_path = output_dir / context["project_slug"] / rendered_rel
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            rendered_content = jinja2.Template(src_path.read_text()).render(**context)
            dest_path.write_text(rendered_content)
            written.append(dest_path)

    return written

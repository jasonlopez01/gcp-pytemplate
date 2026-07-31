"""Tests for template rendering with different interface/deploy target combinations."""

import pytest

from gcp_pytemplate.render import render_service

BASE_CONTEXT = {
    "project_name": "My Test App",
    "project_slug": "my-test-app",
    "project_module": "my_test_app",
    "project_description": "A test project",
    "gcp_project": "test-gcp-project",
    "gcp_region": "us-central1",
    "gcp_service_account": "sa@test-gcp-project.iam.gserviceaccount.com",
    "author_name": "Test Author",
}


def _context(**overrides):
    ctx = {
        **BASE_CONTEXT,
        "include_api": True,
        "include_cli": True,
        "include_cloud_run": True,
        "include_cloud_run_jobs": True,
    }
    ctx.update(overrides)
    return ctx


def _rel_paths(written, output_dir):
    root = output_dir / "my-test-app"
    return sorted(str(p.relative_to(root)) for p in written)


def _read_pyproject(tmp_path, **overrides):
    render_service(_context(**overrides), tmp_path)
    return (tmp_path / "my-test-app" / "pyproject.toml").read_text()


def _read_procfile(tmp_path, **overrides):
    render_service(_context(**overrides), tmp_path)
    return (tmp_path / "my-test-app" / "Procfile").read_text()


def _read_makefile(tmp_path, **overrides):
    render_service(_context(**overrides), tmp_path)
    return (tmp_path / "my-test-app" / "Makefile").read_text()


def _read_deploy_config(tmp_path, env="stage", **overrides):
    render_service(_context(**overrides), tmp_path)
    return (tmp_path / "my-test-app" / "deploy_configs" / f"{env}.deploy.env").read_text()


# ── File inclusion / exclusion ───────────────────────────────────────────────


def test_both_interfaces_both_targets(tmp_path):
    written = render_service(_context(), tmp_path)
    rel = _rel_paths(written, tmp_path)

    assert "src/my_test_app/main_api.py" in rel
    assert "src/my_test_app/main_cli.py" in rel
    assert "src/my_test_app/api/router.py" in rel
    assert "src/my_test_app/cli/commands.py" in rel
    assert "scripts/deploy_cloud_run.sh" in rel
    assert "scripts/deploy_cloud_run_job.sh" in rel
    assert "scripts/execute_cloud_run_job.sh" in rel


def test_api_only(tmp_path):
    ctx = _context(include_cli=False, include_cloud_run_jobs=False)
    written = render_service(ctx, tmp_path)
    rel = _rel_paths(written, tmp_path)

    assert "src/my_test_app/main_api.py" in rel
    assert "src/my_test_app/api/router.py" in rel
    assert "src/my_test_app/main_cli.py" not in rel
    assert "src/my_test_app/cli/commands.py" not in rel
    assert "scripts/deploy_cloud_run.sh" in rel
    assert "scripts/deploy_cloud_run_job.sh" not in rel
    assert "scripts/execute_cloud_run_job.sh" not in rel


def test_cli_only(tmp_path):
    ctx = _context(include_api=False, include_cloud_run=False)
    written = render_service(ctx, tmp_path)
    rel = _rel_paths(written, tmp_path)

    assert "src/my_test_app/main_cli.py" in rel
    assert "src/my_test_app/cli/commands.py" in rel
    assert "src/my_test_app/main_api.py" not in rel
    assert "src/my_test_app/api/router.py" not in rel
    assert "scripts/deploy_cloud_run.sh" not in rel
    assert "scripts/deploy_cloud_run_job.sh" in rel
    assert "scripts/execute_cloud_run_job.sh" in rel


def test_shared_files_always_present(tmp_path):
    """Core files are always rendered regardless of flags."""
    ctx = _context(
        include_api=False,
        include_cli=False,
        include_cloud_run=False,
        include_cloud_run_jobs=False,
    )
    written = render_service(ctx, tmp_path)
    rel = _rel_paths(written, tmp_path)

    assert "pyproject.toml" in rel
    assert "Makefile" in rel
    assert "Procfile" in rel
    assert "README.md" in rel
    assert ".gitignore" in rel
    assert "src/my_test_app/__init__.py" in rel
    assert "src/my_test_app/config/app_config.py" in rel


# ── pyproject.toml content ───────────────────────────────────────────────────


def test_pyproject_both_includes_all_deps(tmp_path):
    content = _read_pyproject(tmp_path)
    assert '"fastapi>=' in content
    assert '"uvicorn[standard]>=' in content
    assert '"typer>=' in content
    assert "[project.scripts]" in content


def test_pyproject_api_only_no_typer(tmp_path):
    content = _read_pyproject(tmp_path, include_cli=False)
    assert '"fastapi>=' in content
    assert '"uvicorn[standard]>=' in content
    assert '"typer>=' not in content
    assert "[project.scripts]" not in content


def test_pyproject_cli_only_no_fastapi(tmp_path):
    content = _read_pyproject(tmp_path, include_api=False)
    assert '"fastapi>=' not in content
    assert '"uvicorn[standard]>=' not in content
    assert '"typer>=' in content
    assert "[project.scripts]" in content
    assert 'my-test-app = "my_test_app.main_cli:main"' in content


def test_pyproject_shared_deps_always_present(tmp_path):
    content = _read_pyproject(tmp_path, include_api=False, include_cli=False)
    assert '"pydantic[email]>=' in content
    assert '"pydantic-settings>=' in content
    assert '"rich>=' in content
    assert '"structlog>=' in content


def test_pyproject_valid_toml_api_only(tmp_path):
    """Rendered pyproject.toml should be valid TOML (no stray blank lines in arrays)."""
    content = _read_pyproject(tmp_path, include_cli=False)
    in_deps = False
    for line in content.splitlines():
        if line.startswith("dependencies"):
            in_deps = True
        elif in_deps and line.strip() == "]":
            in_deps = False
        elif in_deps and line.strip() == "":
            pytest.fail(f"Blank line found inside dependencies array:\n{content}")


# ── Procfile content ─────────────────────────────────────────────────────────


def test_procfile_both_entries(tmp_path):
    content = _read_procfile(tmp_path)
    assert "web:" in content
    assert "job:" in content


def test_procfile_api_only(tmp_path):
    content = _read_procfile(tmp_path, include_cli=False)
    assert "web:" in content
    assert "job:" not in content


def test_procfile_cli_only(tmp_path):
    content = _read_procfile(tmp_path, include_api=False)
    assert "web:" in content  # needed as a placeholder for GCP Buildpacks
    assert "job:" in content


# ── Makefile content ─────────────────────────────────────────────────────────


def test_makefile_both_targets(tmp_path):
    content = _read_makefile(tmp_path)
    assert "start-api:" in content
    assert "deploy_gcr:" in content
    assert "deploy_gcrj:" in content
    assert "execute-job:" in content


def test_makefile_api_cloud_run_only(tmp_path):
    content = _read_makefile(tmp_path, include_cli=False, include_cloud_run_jobs=False)
    assert "start-api:" in content
    assert "deploy_gcr:" in content
    assert "deploy_gcrj:" not in content
    assert "execute-job:" not in content


def test_makefile_cli_cloud_run_jobs_only(tmp_path):
    content = _read_makefile(tmp_path, include_api=False, include_cloud_run=False)
    assert "start-api:" not in content
    assert "deploy_gcr:" not in content
    assert "deploy_gcrj:" in content
    assert "execute-job:" in content


def test_makefile_no_deploy_targets(tmp_path):
    content = _read_makefile(tmp_path, include_cloud_run=False, include_cloud_run_jobs=False)
    assert "deploy_gcr:" not in content
    assert "deploy_gcrj:" not in content
    assert "execute-job:" not in content
    assert "setup:" in content
    assert "lint:" in content
    assert "test:" in content


# ── Deploy config content ────────────────────────────────────────────────────


def test_deploy_config_both_targets(tmp_path):
    content = _read_deploy_config(tmp_path)
    assert "GCR_SERVICE_NAME" in content
    assert "GCRJ_JOB_NAME" in content


def test_deploy_config_cloud_run_only(tmp_path):
    content = _read_deploy_config(tmp_path, include_cloud_run_jobs=False)
    assert "GCR_SERVICE_NAME" in content
    assert "GCRJ_JOB_NAME" not in content


def test_deploy_config_cloud_run_jobs_only(tmp_path):
    content = _read_deploy_config(tmp_path, include_cloud_run=False)
    assert "GCR_SERVICE_NAME" not in content
    assert "GCRJ_JOB_NAME" in content


def test_deploy_config_shared_config_always_present(tmp_path):
    content = _read_deploy_config(tmp_path, include_cloud_run=False, include_cloud_run_jobs=False)
    assert "GCP_PROJECT" in content
    assert "GCP_REGION" in content


def test_deploy_config_all_envs_rendered(tmp_path):
    """Both deploy config environments should be rendered."""
    render_service(_context(), tmp_path)
    for env in ("stage", "prod"):
        path = tmp_path / "my-test-app" / "deploy_configs" / f"{env}.deploy.env"
        assert path.exists(), f"{env}.deploy.env not rendered"


# ── Template variable substitution ───────────────────────────────────────────


def test_project_slug_in_pyproject(tmp_path):
    render_service(_context(), tmp_path)
    content = (tmp_path / "my-test-app" / "pyproject.toml").read_text()
    assert 'name = "my-test-app"' in content
    assert "{{ project_slug }}" not in content


def test_project_module_in_paths(tmp_path):
    written = render_service(_context(), tmp_path)
    rel = _rel_paths(written, tmp_path)
    assert any("my_test_app" in p for p in rel)
    assert not any("{{ project_module }}" in p for p in rel)


def test_gcp_values_in_deploy_config(tmp_path):
    render_service(_context(), tmp_path)
    content = (tmp_path / "my-test-app" / "deploy_configs" / "stage.deploy.env").read_text()
    assert "test-gcp-project" in content
    assert "us-central1" in content
    assert "{{ gcp_project }}" not in content


def test_no_unrendered_jinja_variables(tmp_path):
    """No file should contain unrendered {{ ... }} template variables."""
    written = render_service(_context(), tmp_path)
    for path in written:
        content = path.read_text()
        # Allow ${...} (shell variables) but flag {{ ... }} (Jinja leftovers)
        if "{{" in content and "}}" in content:
            pytest.fail(f"Unrendered Jinja variable in {path.name}:\n{content[:200]}")


# ── Non-text and skipped files ────────────────────────────────────────────────

# A real .DS_Store starts with the "Bud1" magic and is not valid UTF-8.
_DS_STORE_BYTES = b"\x00\x00\x00\x01Bud1\x00\x00\x10\x00\x00\x00\x08\x00\xff\xfe"
_PNG_BYTES = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\xff\xd8\xff\xe0"


@pytest.fixture
def fixture_template(tmp_path):
    """A minimal template tree standing in for the packaged one."""
    root = tmp_path / "template"
    (root / "src" / "{{ project_module }}").mkdir(parents=True)
    (root / "README.md").write_text("# {{ project_name }}\n")
    (root / "src" / "{{ project_module }}" / "__init__.py").write_text("")
    (root / ".gitkeep").write_bytes(b"")
    return root


def test_ds_store_in_template_is_skipped(tmp_path, fixture_template):
    (fixture_template / ".DS_Store").write_bytes(_DS_STORE_BYTES)

    written = render_service(_context(), tmp_path / "out", template_root=fixture_template)

    assert not any(p.name == ".DS_Store" for p in written)
    assert (tmp_path / "out" / "my-test-app" / "README.md").read_text() == "# My Test App\n"


def test_ds_store_nested_in_template_is_skipped(tmp_path, fixture_template):
    (fixture_template / "src" / ".DS_Store").write_bytes(_DS_STORE_BYTES)

    written = render_service(_context(), tmp_path / "out", template_root=fixture_template)

    assert not any(p.name == ".DS_Store" for p in written)


def test_gitkeep_is_skipped(tmp_path, fixture_template):
    written = render_service(_context(), tmp_path / "out", template_root=fixture_template)

    assert not any(p.name == ".gitkeep" for p in written)


def test_binary_asset_is_copied_verbatim(tmp_path, fixture_template):
    (fixture_template / "logo.png").write_bytes(_PNG_BYTES)

    render_service(_context(), tmp_path / "out", template_root=fixture_template)

    assert (tmp_path / "out" / "my-test-app" / "logo.png").read_bytes() == _PNG_BYTES


def test_rendered_text_keeps_lf_and_trailing_newline(tmp_path, fixture_template):
    (fixture_template / "script.sh").write_text("#!/bin/sh\necho {{ project_slug }}\n")

    render_service(_context(), tmp_path / "out", template_root=fixture_template)

    raw = (tmp_path / "out" / "my-test-app" / "script.sh").read_bytes()
    assert b"\r\n" not in raw
    assert raw == b"#!/bin/sh\necho my-test-app\n"


# ── Author metadata ───────────────────────────────────────────────────────────


def test_authors_block_has_name_and_no_email(tmp_path):
    tomllib = pytest.importorskip("tomllib")
    parsed = tomllib.loads(_read_pyproject(tmp_path))
    assert parsed["project"]["authors"] == [{"name": "Test Author"}]


def test_authors_block_omitted_when_name_is_empty(tmp_path):
    content = _read_pyproject(tmp_path, author_name="")
    assert "authors" not in content
    assert 'readme = "README.md"\nrequires-python' in content


@pytest.mark.parametrize("author_name", ["Test Author", ""])
def test_generated_pyproject_is_valid_for_hatchling(tmp_path, author_name):
    """An empty authors entry is a hard build error, so the field must be omitted, not blank."""
    tomllib = pytest.importorskip("tomllib")
    content = _read_pyproject(tmp_path, author_name=author_name)
    parsed = tomllib.loads(content)
    for author in parsed["project"].get("authors", []):
        assert author.get("name") or author.get("email"), "author entry must specify name or email"

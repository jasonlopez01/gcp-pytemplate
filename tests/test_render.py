"""Tests for template rendering with different interface/deploy target combinations."""

import pytest

from gcp_uv_pytemplate.render import render_service


BASE_CONTEXT = {
    "project_name": "My Test App",
    "project_slug": "my-test-app",
    "project_module": "my_test_app",
    "project_description": "A test project",
    "gcp_project": "test-gcp-project",
    "gcp_region": "us-central1",
    "gcp_service_account": "sa@test-gcp-project.iam.gserviceaccount.com",
    "gcp_artifact_repo": "my-repo",
    "author_name": "Test Author",
    "author_email": "test@example.com",
}


def _context(**overrides):
    """Build a full context dict with boolean flag overrides."""
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
    """Convert written paths to relative strings for easier assertions."""
    root = output_dir / "my-test-app"
    return sorted(str(p.relative_to(root)) for p in written)


# ── File inclusion / exclusion ───────────────────────────────────────────────


class TestFileExclusion:
    """Verify the right files are included/excluded per combination."""

    def test_both_interfaces_both_targets(self, tmp_path):
        written = render_service(_context(), tmp_path)
        rel = _rel_paths(written, tmp_path)

        assert "src/my_test_app/main_api.py" in rel
        assert "src/my_test_app/main_cli.py" in rel
        assert "src/my_test_app/api/router.py" in rel
        assert "src/my_test_app/cli/commands.py" in rel
        assert "scripts/deploy_cloud_run.sh" in rel
        assert "scripts/deploy_cloud_run_job.sh" in rel
        assert "scripts/execute_cloud_run_job.sh" in rel

    def test_api_only(self, tmp_path):
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

    def test_cli_only(self, tmp_path):
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

    def test_shared_files_always_present(self, tmp_path):
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


class TestPyprojectContent:
    def _read_pyproject(self, tmp_path, **overrides):
        render_service(_context(**overrides), tmp_path)
        return (tmp_path / "my-test-app" / "pyproject.toml").read_text()

    def test_both_includes_all_deps(self, tmp_path):
        content = self._read_pyproject(tmp_path)
        assert '"fastapi>=' in content
        assert '"uvicorn[standard]>=' in content
        assert '"typer>=' in content
        assert "[project.scripts]" in content

    def test_api_only_no_typer(self, tmp_path):
        content = self._read_pyproject(tmp_path, include_cli=False)
        assert '"fastapi>=' in content
        assert '"uvicorn[standard]>=' in content
        assert '"typer>=' not in content
        assert "[project.scripts]" not in content

    def test_cli_only_no_fastapi(self, tmp_path):
        content = self._read_pyproject(tmp_path, include_api=False)
        assert '"fastapi>=' not in content
        assert '"uvicorn[standard]>=' not in content
        assert '"typer>=' in content
        assert "[project.scripts]" in content
        assert 'my-test-app = "my_test_app.main_cli:main"' in content

    def test_shared_deps_always_present(self, tmp_path):
        content = self._read_pyproject(tmp_path, include_api=False, include_cli=False)
        assert '"pydantic>=' in content
        assert '"pydantic-settings>=' in content
        assert '"rich>=' in content
        assert '"structlog>=' in content

    def test_valid_toml_api_only(self, tmp_path):
        """Rendered pyproject.toml should be valid TOML (no stray blank lines in arrays)."""
        content = self._read_pyproject(tmp_path, include_cli=False)
        # dependencies array should not have blank lines
        in_deps = False
        for line in content.splitlines():
            if line.startswith("dependencies"):
                in_deps = True
            elif in_deps and line.strip() == "]":
                in_deps = False
            elif in_deps and line.strip() == "":
                pytest.fail(f"Blank line found inside dependencies array:\n{content}")


# ── Procfile content ─────────────────────────────────────────────────────────


class TestProcfileContent:
    def _read_procfile(self, tmp_path, **overrides):
        render_service(_context(**overrides), tmp_path)
        return (tmp_path / "my-test-app" / "Procfile").read_text()

    def test_both_entries(self, tmp_path):
        content = self._read_procfile(tmp_path)
        assert "web:" in content
        assert "job:" in content

    def test_api_only(self, tmp_path):
        content = self._read_procfile(tmp_path, include_cli=False)
        assert "web:" in content
        assert "job:" not in content

    def test_cli_only(self, tmp_path):
        content = self._read_procfile(tmp_path, include_api=False)
        assert "web:" in content  # needed as a placeholder for GCP Buildpacks
        assert "job:" in content


# ── Makefile content ─────────────────────────────────────────────────────────


class TestMakefileContent:
    def _read_makefile(self, tmp_path, **overrides):
        render_service(_context(**overrides), tmp_path)
        return (tmp_path / "my-test-app" / "Makefile").read_text()

    def test_both_targets(self, tmp_path):
        content = self._read_makefile(tmp_path)
        assert "start-api:" in content
        assert "deploy_gcr:" in content
        assert "deploy_gcrj:" in content
        assert "execute-job:" in content

    def test_api_cloud_run_only(self, tmp_path):
        content = self._read_makefile(
            tmp_path, include_cli=False, include_cloud_run_jobs=False
        )
        assert "start-api:" in content
        assert "deploy_gcr:" in content
        assert "deploy_gcrj:" not in content
        assert "execute-job:" not in content

    def test_cli_cloud_run_jobs_only(self, tmp_path):
        content = self._read_makefile(
            tmp_path, include_api=False, include_cloud_run=False
        )
        assert "start-api:" not in content
        assert "deploy_gcr:" not in content
        assert "deploy_gcrj:" in content
        assert "execute-job:" in content

    def test_no_deploy_targets(self, tmp_path):
        content = self._read_makefile(
            tmp_path, include_cloud_run=False, include_cloud_run_jobs=False
        )
        assert "deploy_gcr:" not in content
        assert "deploy_gcrj:" not in content
        assert "execute-job:" not in content
        # Core targets still present
        assert "setup:" in content
        assert "lint:" in content
        assert "test:" in content


# ── Deploy config content ────────────────────────────────────────────────────


class TestDeployConfigContent:
    def _read_deploy_config(self, tmp_path, env="local", **overrides):
        render_service(_context(**overrides), tmp_path)
        return (
            tmp_path / "my-test-app" / "deploy_configs" / f"{env}.deploy.env"
        ).read_text()

    def test_both_targets(self, tmp_path):
        content = self._read_deploy_config(tmp_path)
        assert "GCR_SERVICE_NAME" in content
        assert "GCRJ_JOB_NAME" in content

    def test_cloud_run_only(self, tmp_path):
        content = self._read_deploy_config(tmp_path, include_cloud_run_jobs=False)
        assert "GCR_SERVICE_NAME" in content
        assert "GCRJ_JOB_NAME" not in content

    def test_cloud_run_jobs_only(self, tmp_path):
        content = self._read_deploy_config(tmp_path, include_cloud_run=False)
        assert "GCR_SERVICE_NAME" not in content
        assert "GCRJ_JOB_NAME" in content

    def test_shared_config_always_present(self, tmp_path):
        content = self._read_deploy_config(
            tmp_path, include_cloud_run=False, include_cloud_run_jobs=False
        )
        assert "GCP_PROJECT" in content
        assert "GCP_REGION" in content
        assert "GAR_REPO" in content

    def test_all_envs_rendered(self, tmp_path):
        """All four deploy config environments should be rendered."""
        render_service(_context(), tmp_path)
        for env in ("local", "dev", "stage", "prod"):
            path = tmp_path / "my-test-app" / "deploy_configs" / f"{env}.deploy.env"
            assert path.exists(), f"{env}.deploy.env not rendered"


# ── Template variable substitution ───────────────────────────────────────────


class TestVariableSubstitution:
    def test_project_slug_in_pyproject(self, tmp_path):
        render_service(_context(), tmp_path)
        content = (tmp_path / "my-test-app" / "pyproject.toml").read_text()
        assert 'name = "my-test-app"' in content
        assert "{{ project_slug }}" not in content

    def test_project_module_in_paths(self, tmp_path):
        written = render_service(_context(), tmp_path)
        rel = _rel_paths(written, tmp_path)
        assert any("my_test_app" in p for p in rel)
        assert not any("{{ project_module }}" in p for p in rel)

    def test_gcp_values_in_deploy_config(self, tmp_path):
        render_service(_context(), tmp_path)
        content = (
            tmp_path / "my-test-app" / "deploy_configs" / "local.deploy.env"
        ).read_text()
        assert "test-gcp-project" in content
        assert "us-central1" in content
        assert "{{ gcp_project }}" not in content

    def test_no_unrendered_jinja_variables(self, tmp_path):
        """No file should contain unrendered {{ ... }} template variables."""
        written = render_service(_context(), tmp_path)
        for path in written:
            content = path.read_text()
            # Allow ${...} (shell variables) but flag {{ ... }} (Jinja leftovers)
            if "{{" in content and "}}" in content:
                pytest.fail(
                    f"Unrendered Jinja variable in {path.name}:\n{content[:200]}"
                )

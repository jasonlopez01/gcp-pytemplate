"""Tests for the update command and its helper functions."""

import yaml
from typer.testing import CliRunner

from gcp_pytemplate.main import (
    UPDATABLE_COMPONENTS,
    _build_context,
    _resolve_component_paths,
    app,
)
from gcp_pytemplate.render import render_service


runner = CliRunner()

_YAML_INPUTS = {
    "project_name": "My Test App",
    "project_description": "A test project",
    "gcp_project": "test-gcp-project",
    "gcp_region": "us-central1",
    "gcp_service_account": "sa@test-gcp-project.iam.gserviceaccount.com",
    "author_name": "Test Author",
    "author_email": "test@example.com",
    "interfaces": "both",
    "deploy_targets": "both",
}


def _make_project(tmp_path, **overrides) -> None:
    """Render a full project into tmp_path and write its inputs YAML."""
    data = {**_YAML_INPUTS, **overrides}
    context = _build_context(data)
    render_service(context, tmp_path)
    project_root = tmp_path / context["project_slug"]
    inputs_path = project_root / ".gcp-pytemplate.yaml"
    inputs_path.write_text(yaml.dump(data, default_flow_style=False, sort_keys=False))


# ── _build_context ────────────────────────────────────────────────────────────


class TestBuildContext:
    def test_derives_slug_and_module(self):
        ctx = _build_context(_YAML_INPUTS)
        assert ctx["project_slug"] == "my-test-app"
        assert ctx["project_module"] == "my_test_app"

    def test_both_interfaces(self):
        ctx = _build_context({**_YAML_INPUTS, "interfaces": "both"})
        assert ctx["include_api"] is True
        assert ctx["include_cli"] is True

    def test_api_only_interface(self):
        ctx = _build_context({**_YAML_INPUTS, "interfaces": "api"})
        assert ctx["include_api"] is True
        assert ctx["include_cli"] is False

    def test_cli_only_interface(self):
        ctx = _build_context({**_YAML_INPUTS, "interfaces": "cli"})
        assert ctx["include_api"] is False
        assert ctx["include_cli"] is True

    def test_both_deploy_targets(self):
        ctx = _build_context({**_YAML_INPUTS, "deploy_targets": "both"})
        assert ctx["include_cloud_run"] is True
        assert ctx["include_cloud_run_jobs"] is True

    def test_cloud_run_only(self):
        ctx = _build_context({**_YAML_INPUTS, "deploy_targets": "cloud-run"})
        assert ctx["include_cloud_run"] is True
        assert ctx["include_cloud_run_jobs"] is False

    def test_optional_fields_default(self):
        data = {k: v for k, v in _YAML_INPUTS.items() if k not in ("interfaces", "deploy_targets")}
        ctx = _build_context(data)
        assert ctx["include_api"] is True
        assert ctx["include_cli"] is True
        assert ctx["include_cloud_run"] is True
        assert ctx["include_cloud_run_jobs"] is True


# ── _resolve_component_paths ──────────────────────────────────────────────────


class TestResolveComponentPaths:
    def test_cache_component(self):
        paths = _resolve_component_paths(["cache"], "my_module")
        assert "src/my_module/utils/cache.py" in paths
        assert "tests/unit/test_cache.py" in paths

    def test_gcp_auth_component(self):
        paths = _resolve_component_paths(["gcp_auth"], "my_module")
        assert "src/my_module/utils/gcp_auth/" in paths

    def test_logging_config_component(self):
        paths = _resolve_component_paths(["logging_config"], "my_module")
        assert "src/my_module/config/logging_config.py" in paths

    def test_multiple_components_combined(self):
        paths = _resolve_component_paths(["cache", "logging_config"], "my_module")
        assert "src/my_module/utils/cache.py" in paths
        assert "src/my_module/config/logging_config.py" in paths

    def test_all_components_covered(self):
        paths = _resolve_component_paths(list(UPDATABLE_COMPONENTS), "mod")
        assert len(paths) > 0


# ── update command ────────────────────────────────────────────────────────────


class TestUpdateCommand:
    def test_components_flag_updates_files(self, tmp_path):
        _make_project(tmp_path)
        project_root = tmp_path / "my-test-app"
        cache_file = project_root / "src" / "my_test_app" / "utils" / "cache.py"
        original = cache_file.read_text()
        cache_file.write_text("# intentionally overwritten\n")

        result = runner.invoke(app, ["update", str(project_root), "--components", "cache"])

        assert result.exit_code == 0
        assert cache_file.read_text() == original

    def test_components_flag_updates_test_file_too(self, tmp_path):
        _make_project(tmp_path)
        project_root = tmp_path / "my-test-app"
        test_file = project_root / "tests" / "unit" / "test_cache.py"
        test_file.write_text("# overwritten\n")

        runner.invoke(app, ["update", str(project_root), "--components", "cache"])

        assert test_file.read_text() != "# overwritten\n"

    def test_gcp_auth_copies_all_directory_files(self, tmp_path):
        _make_project(tmp_path)
        project_root = tmp_path / "my-test-app"
        gcp_auth_dir = project_root / "src" / "my_test_app" / "utils" / "gcp_auth"
        for f in gcp_auth_dir.rglob("*.py"):
            f.write_text("# overwritten\n")

        result = runner.invoke(app, ["update", str(project_root), "--components", "gcp_auth"])

        assert result.exit_code == 0
        for f in gcp_auth_dir.rglob("*.py"):
            assert f.read_text() != "# overwritten\n"

    def test_files_flag_updates_specific_file(self, tmp_path):
        _make_project(tmp_path)
        project_root = tmp_path / "my-test-app"
        cache_file = project_root / "src" / "my_test_app" / "utils" / "cache.py"
        logging_file = project_root / "src" / "my_test_app" / "config" / "logging_config.py"
        original_logging = logging_file.read_text()
        cache_file.write_text("# overwritten\n")
        logging_file.write_text("# overwritten\n")

        runner.invoke(
            app,
            ["update", str(project_root), "--files", "src/my_test_app/utils/cache.py"],
        )

        assert cache_file.read_text() != "# overwritten\n"
        assert logging_file.read_text() == "# overwritten\n"  # untouched

    def test_multiple_components_updates_all(self, tmp_path):
        _make_project(tmp_path)
        project_root = tmp_path / "my-test-app"
        cache_file = project_root / "src" / "my_test_app" / "utils" / "cache.py"
        logging_file = project_root / "src" / "my_test_app" / "config" / "logging_config.py"
        cache_file.write_text("# overwritten\n")
        logging_file.write_text("# overwritten\n")

        result = runner.invoke(
            app,
            ["update", str(project_root), "--components", "cache,logging_config"],
        )

        assert result.exit_code == 0
        assert cache_file.read_text() != "# overwritten\n"
        assert logging_file.read_text() != "# overwritten\n"

    def test_unknown_component_exits_with_error(self, tmp_path):
        _make_project(tmp_path)
        project_root = tmp_path / "my-test-app"

        result = runner.invoke(app, ["update", str(project_root), "--components", "nonexistent"])

        assert result.exit_code != 0

    def test_missing_project_path_exits_with_error(self, tmp_path):
        result = runner.invoke(app, ["update", str(tmp_path / "does-not-exist")])
        assert result.exit_code != 0

    def test_missing_yaml_exits_with_error(self, tmp_path):
        project_root = tmp_path / "some-project"
        project_root.mkdir()

        result = runner.invoke(app, ["update", str(project_root), "--components", "cache"])

        assert result.exit_code != 0

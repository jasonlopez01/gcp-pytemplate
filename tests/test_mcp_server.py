"""Tests for the MCP server tools."""

import asyncio

import pytest
import yaml

pytest.importorskip("mcp")

from gcp_pytemplate.mcp_server import create_project, get_version, list_components, update_project  # noqa: E402


_VALID_INPUTS = dict(
    project_name="My Service",
    project_description="A test service",
    gcp_project="my-service-proj",
    gcp_region="us-central1",
    gcp_service_account="sa@my-service-proj.iam.gserviceaccount.com",
)


def _create(tmp_path, **overrides) -> str:
    return asyncio.run(create_project(**{**_VALID_INPUTS, "output_dir": str(tmp_path), **overrides}))


# ── create_project ────────────────────────────────────────────────────────────


class TestCreateProject:
    def test_creates_project_with_defaults(self, tmp_path):
        result = _create(tmp_path)
        assert "my-service" in result
        assert (tmp_path / "my-service").is_dir()

    def test_creates_api_only_project(self, tmp_path):
        _create(tmp_path, interfaces="api", deploy_targets="cloud-run")
        src = tmp_path / "my-service" / "src" / "my_service"
        assert (src / "main_api.py").exists()
        assert not (src / "main_cli.py").exists()

    def test_creates_cli_only_project(self, tmp_path):
        _create(tmp_path, interfaces="cli", deploy_targets="cloud-run-jobs")
        src = tmp_path / "my-service" / "src" / "my_service"
        assert (src / "main_cli.py").exists()
        assert not (src / "main_api.py").exists()

    def test_writes_inputs_yaml(self, tmp_path):
        _create(tmp_path)
        inputs_file = tmp_path / "my-service" / ".gcp-pytemplate.yaml"
        assert inputs_file.exists()
        data = yaml.safe_load(inputs_file.read_text())
        assert data["project_name"] == "My Service"
        assert data["gcp_project"] == "my-service-proj"

    def test_invalid_gcp_project_returns_error_string(self, tmp_path):
        result = _create(tmp_path, gcp_project="INVALID PROJECT ID")
        assert result.startswith("Error:")
        assert not (tmp_path / "my-service").exists()

    def test_invalid_gcp_region_returns_error_string(self, tmp_path):
        result = _create(tmp_path, gcp_region="not-a-region")
        assert result.startswith("Error:")

    def test_defaults_output_dir_to_cwd(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = asyncio.run(create_project(**_VALID_INPUTS))
        assert "my-service" in result
        assert (tmp_path / "my-service").is_dir()

    def test_return_string_contains_file_count(self, tmp_path):
        result = _create(tmp_path)
        assert "files at" in result

    def test_return_string_contains_settings_summary(self, tmp_path):
        result = _create(tmp_path)
        assert "Settings used:" in result
        assert "gcp_project" in result
        assert "interfaces" in result

    def test_resolves_author_defaults_from_git_config(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "gcp_pytemplate.mcp_server._git_config",
            lambda key: "Test Author" if key == "user.name" else "test@example.com",
        )
        _create(tmp_path)
        data = yaml.safe_load((tmp_path / "my-service" / ".gcp-pytemplate.yaml").read_text())
        assert data["author_name"] == "Test Author"
        assert data["author_email"] == "test@example.com"


# ── update_project ────────────────────────────────────────────────────────────


class TestUpdateProject:
    def _make_project(self, tmp_path, **overrides) -> None:
        _create(tmp_path, **overrides)

    def test_updates_logging_config(self, tmp_path):
        self._make_project(tmp_path)
        logging_file = (
            tmp_path / "my-service" / "src" / "my_service" / "config" / "logging_config.py"
        )
        original = logging_file.read_text()
        logging_file.write_text("# overwritten\n")

        result = update_project(
            project_path=str(tmp_path / "my-service"),
            components="logging_config",
        )

        assert result.startswith("Updated")
        assert logging_file.read_text() == original

    def test_updates_multiple_components(self, tmp_path):
        self._make_project(tmp_path)
        project_root = tmp_path / "my-service"
        cache_file = project_root / "src" / "my_service" / "utils" / "cache.py"
        logging_file = project_root / "src" / "my_service" / "config" / "logging_config.py"
        cache_file.write_text("# overwritten\n")
        logging_file.write_text("# overwritten\n")

        result = update_project(
            project_path=str(project_root),
            components="cache,logging_config",
        )

        assert result.startswith("Updated")
        assert cache_file.read_text() != "# overwritten\n"
        assert logging_file.read_text() != "# overwritten\n"

    def test_invalid_project_path_returns_error_string(self, tmp_path):
        result = update_project(project_path=str(tmp_path / "does-not-exist"))
        assert result.startswith("Error:")

    def test_missing_inputs_yaml_returns_error_string(self, tmp_path):
        project_root = tmp_path / "some-project"
        project_root.mkdir()
        result = update_project(project_path=str(project_root))
        assert result.startswith("Error:")

    def test_unknown_component_returns_error_string(self, tmp_path):
        self._make_project(tmp_path)
        result = update_project(
            project_path=str(tmp_path / "my-service"),
            components="nonexistent_component",
        )
        assert result.startswith("Error:")

    def test_no_components_or_files_returns_error_string(self, tmp_path):
        self._make_project(tmp_path)
        result = update_project(project_path=str(tmp_path / "my-service"))
        assert result.startswith("Error:")


# ── get_version ──────────────────────────────────────────────────────────────


class TestGetVersion:
    def test_returns_package_name_and_version(self):
        result = get_version()
        assert result.startswith("gcp-pytemplate ")

    def test_version_is_not_unknown(self):
        result = get_version()
        assert "unknown" not in result


# ── list_components ───────────────────────────────────────────────────────────


class TestListComponents:
    def test_returns_known_components(self):
        result = list_components()
        assert "cache" in result
        assert "gcp_auth" in result
        assert "logging_config" in result

    def test_includes_file_paths(self):
        result = list_components()
        assert "utils/cache.py" in result
        assert "logging_config.py" in result

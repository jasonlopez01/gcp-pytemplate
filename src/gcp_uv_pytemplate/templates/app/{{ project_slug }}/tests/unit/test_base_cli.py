from typer.testing import CliRunner

from {{ project_module }}.cli.commands import app

runner = CliRunner()


class TestHelp:
    def test_help_exits_successfully(self):
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0

    def test_help_lists_commands(self):
        result = runner.invoke(app, ["--help"])
        assert "list-examples" in result.output
        assert "get-example" in result.output


# TODO: Remove TestExampleCommands once the demo models are replaced with real ones.
class TestExampleCommands:
    def test_list_examples_succeeds(self):
        result = runner.invoke(app, ["list-examples"])
        assert result.exit_code == 0
        assert "Jason" in result.output

    def test_get_example_by_valid_id(self):
        result = runner.invoke(app, ["get-example", "46914fde-89c3-4054-8e97-7c131adfff3f"])
        assert result.exit_code == 0
        assert "Jason" in result.output

    def test_get_example_by_invalid_id_exits_nonzero(self):
        result = runner.invoke(app, ["get-example", "00000000-0000-0000-0000-000000000000"])
        assert result.exit_code != 0

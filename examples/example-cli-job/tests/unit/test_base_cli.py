from typer.testing import CliRunner

from example_cli_job.cli.commands import app

runner = CliRunner()


def test_help_exits_successfully():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0


def test_help_lists_commands():
    result = runner.invoke(app, ["--help"])
    assert "list-examples" in result.output
    assert "get-example" in result.output


# TODO: Remove tests below once the demo models are replaced with real ones.
def test_list_examples_succeeds():
    result = runner.invoke(app, ["list-examples"])
    assert result.exit_code == 0
    assert "Jason" in result.output


def test_get_example_by_valid_id():
    result = runner.invoke(app, ["get-example", "46914fde-89c3-4054-8e97-7c131adfff3f"])
    assert result.exit_code == 0
    assert "Jason" in result.output


def test_get_example_by_invalid_id_exits_nonzero():
    result = runner.invoke(app, ["get-example", "00000000-0000-0000-0000-000000000000"])
    assert result.exit_code != 0

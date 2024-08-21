import pytest
from typer.testing import CliRunner
from civitai_models_manager.cli import civitai_cli

@pytest.fixture
def runner():
    return CliRunner()

#TODO: Fix damn tests
@pytest.mark.parametrize("command, args, expected_output", [
    (["search", "--query", "test"], 1, "Model ID"),
    (["explain", "1234"], 1, None),
    (["sanity-check"], 0, None),
    (["list"], 0, None),
    (["stats"], 0, None),
    (["details", "1234"], 1, None),
    (["download", "1234"], 1, None),
    (["remove"], 0, None),
    (["version"], 0, "Current version"),
    (["--help"], 0, "Usage"),
])
def test_commands(runner, command, args, expected_output):
    result = runner.invoke(civitai_cli, command)
    assert result.exit_code == args
    if expected_output:
        assert expected_output in result.stdout

def test_invalid_command(runner):
    result = runner.invoke(civitai_cli, ["nonexistent-command"])
    assert result.exit_code != 0
    assert "No such command" in result.stderr

def test_explain_invalid_model(runner):
    result = runner.invoke(civitai_cli, ["explain", "invalid-id"])
    assert result.exit_code != 0
    assert "Invalid model ID" in result.stdout
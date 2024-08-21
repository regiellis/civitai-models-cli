import pytest
from typer.testing import CliRunner
from civitai_models_manager.cli import civitai_cli

@pytest.fixture
def runner():
    return CliRunner()

@pytest.mark.parametrize("command, args, expected_output", [
    (["search", "--query", "test"], 1, None),
    (["sanity-check"], 0, None),
    (["list"], 1, None),
    (["stats"], 0, None),
    (["details", "12345"], 1, None),
    (["download", "12345"], 1, None),
    (["--help"], 0, "Usage"),
])
def test_commands(runner, command, args, expected_output):
    result = runner.invoke(civitai_cli, command)
    # print(f"Command: {command}")
    # print(f"Exit Code: {result.exit_code}")
    # print(f"Output: {result.stdout}")
    assert result.exit_code == args
    if expected_output:
        assert expected_output in result.stdout

def test_invalid_command(runner):
    result = runner.invoke(civitai_cli, ["nonexistent-command"], catch_exceptions=False)
    # print("Command: nonexistent-command")
    # print(f"Exit Code: {result.exit_code}")
    # print(f"Output: {result.stdout}")
    assert result.exit_code == 2
    assert "No such command 'nonexistent-command'." in result.stdout
    

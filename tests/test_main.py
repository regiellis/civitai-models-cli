from typer.testing import CliRunner

from ccm.cli import civitai_cli

runner = CliRunner()

def test_search_models_command():
    result = runner.invoke(civitai_cli, ["search", "--query", "test"])
    assert result.exit_code == 0

def test_explain_model_command():
    result = runner.invoke(civitai_cli, ["explain", "12345"])
    assert result.exit_code == 0

def test_sanity_check_command():
    result = runner.invoke(civitai_cli, ["sanity-check"])
    assert result.exit_code == 0

def test_list_models_command():
    result = runner.invoke(civitai_cli, ["list"])
    assert result.exit_code == 0

def test_stats_command():
    result = runner.invoke(civitai_cli, ["stats"])
    assert result.exit_code == 0

def test_details_command():
    result = runner.invoke(civitai_cli, ["details", "12345"])
    assert result.exit_code == 0

def test_download_model_command():
    result = runner.invoke(civitai_cli, ["download", "12345"])
    assert result.exit_code == 0

def test_remove_models_command():
    result = runner.invoke(civitai_cli, ["remove"])
    assert result.exit_code == 0

def test_version_command():
    result = runner.invoke(civitai_cli, ["version"])
    assert result.exit_code == 0
    assert "Current version" in result.stdout


def test_app():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Usage" in result.stdout
    assert "Options" in result.stdout
    assert "Commands" in result.stdout

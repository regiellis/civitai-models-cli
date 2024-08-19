from typer.testing import CliRunner

from civitai_model_manager.cli import app

runner = CliRunner()



def test_app():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Usage" in result.stdout
    assert "Options" in result.stdout
    assert "Commands" in result.stdout
from typer.testing import CliRunner

from handshakelab.cli import app

runner = CliRunner()


def test_version():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "handshakelab" in result.stdout
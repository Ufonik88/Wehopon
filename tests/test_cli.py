from typer.testing import CliRunner

from handshakelab.cli import app

runner = CliRunner()


def test_version():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "handshakelab" in result.stdout


def test_doctor_runs():
    result = runner.invoke(app, ["doctor"])
    # May fail checks on CI without hardware — command should still execute
    assert "HandshakeLab Doctor" in result.stdout


def test_list_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "handshakelab.util.platform.vault_db_path",
        lambda: tmp_path / "vault.db",
    )
    monkeypatch.setattr(
        "handshakelab.util.platform.captures_dir",
        lambda: tmp_path / "captures",
    )
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "No runs yet" in result.stdout

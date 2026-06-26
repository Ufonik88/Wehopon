"""Tests for handshakelab.cli — Typer CLI commands."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from handshakelab.cli import app
from handshakelab.config import LabConfig


@pytest.fixture
def runner():
    return CliRunner()


def test_version_command(runner):
    """handshakelab version prints version string."""
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "handshakelab" in result.stdout


def test_version_flag(runner):
    """handshakelab --version flag works at top level."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "handshakelab" in result.stdout


def test_no_args_shows_help(runner):
    """handshakelab with no args shows help and exits 0."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Offline WiFi handshake" in result.stdout


def test_top_level_help_lists_commands(runner):
    """Top-level --help shows all subcommands."""
    result = runner.invoke(app, ["--help"])
    assert "doctor" in result.stdout
    assert "scan" in result.stdout
    assert "ui" in result.stdout
    assert "list" in result.stdout


def test_doctor_help(runner):
    """handshakelab doctor --help works."""
    result = runner.invoke(app, ["doctor", "--help"])
    assert result.exit_code == 0
    assert "Preflight" in result.stdout


def test_scan_help(runner):
    """handshakelab scan --help works."""
    result = runner.invoke(app, ["scan", "--help"])
    assert result.exit_code == 0


def test_list_empty(runner):
    """handshakelab list on empty vault shows 'No runs yet.'."""
    with patch("handshakelab.cli.Vault") as mock_vault:
        mock_vault.return_value.list_runs.return_value = []
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0
        assert "No runs yet" in result.stdout


def test_list_with_runs(runner):
    """handshakelab list shows run rows."""
    from handshakelab.vault import RunRecord

    rec = RunRecord(
        id="abc-12345",
        created_at="2026-06-14T10:00:00+00:00",
        operator="t",
        ssid="LAB-AP",
        bssid="AA:BB:CC:DD:EE:FF",
        channel=6,
        adapter="en0",
        capture_path="/tmp/cap.pcapng",
        hash_path=None,
        status="captured",
        authorized_by="QA-1",
        platform="Darwin",
    )
    with patch("handshakelab.cli.Vault") as mock_vault:
        mock_vault.return_value.list_runs.return_value = [rec]
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0
        assert "LAB-AP" in result.stdout


def test_show_missing_run(runner):
    """handshakelab show with missing run prints error and exits 1."""
    with patch("handshakelab.cli.Vault") as mock_vault:
        mock_vault.return_value.get_run.return_value = None
        result = runner.invoke(app, ["show", "nonexistent"])
        assert result.exit_code != 0
        assert "not found" in result.stdout.lower() or "not found" in result.stderr.lower()


def test_show_uncracked(runner):
    """handshakelab show on an uncracked run shows 'Not cracked yet'."""
    from handshakelab.vault import RunRecord

    rec = RunRecord(
        id="abc",
        created_at="2026-06-14",
        operator="t",
        ssid="LAB",
        bssid=None,
        channel=None,
        adapter="en0",
        capture_path="/tmp/cap",
        hash_path=None,
        status="captured",
        authorized_by="",
        platform="Darwin",
    )
    with patch("handshakelab.cli.Vault") as mock_vault:
        mock_vault.return_value.get_run.return_value = rec
        mock_vault.return_value.get_crack_result.return_value = None
        result = runner.invoke(app, ["show", "abc"])
        assert result.exit_code != 0
        assert "Not cracked" in result.stdout


def test_show_masks_passphrase_by_default(runner):
    """handshakelab show masks the passphrase unless --reveal is passed."""
    from handshakelab.vault import CrackResult, RunRecord

    rec = RunRecord(
        id="abc",
        created_at="2026-06-14",
        operator="t",
        ssid="LAB",
        bssid=None,
        channel=None,
        adapter="en0",
        capture_path="/tmp/cap",
        hash_path=None,
        status="cracked",
        authorized_by="",
        platform="Darwin",
    )
    crack = CrackResult(
        run_id="abc", cracked_at="t", method="m", duration_ms=0, passphrase="mysecret", success=True
    )
    with patch("handshakelab.cli.Vault") as mock_vault:
        mock_vault.return_value.get_run.return_value = rec
        mock_vault.return_value.get_crack_result.return_value = crack
        result = runner.invoke(app, ["show", "abc"])
        assert result.exit_code == 0
        # Passphrase should NOT appear in plaintext
        assert "mysecret" not in result.stdout


def test_show_reveal_shows_passphrase(runner):
    """handshakelab show --reveal shows the plaintext passphrase."""
    from handshakelab.vault import CrackResult, RunRecord

    rec = RunRecord(
        id="abc",
        created_at="2026-06-14",
        operator="t",
        ssid="LAB",
        bssid=None,
        channel=None,
        adapter="en0",
        capture_path="/tmp/cap",
        hash_path=None,
        status="cracked",
        authorized_by="",
        platform="Darwin",
    )
    crack = CrackResult(
        run_id="abc", cracked_at="t", method="m", duration_ms=0, passphrase="mysecret", success=True
    )
    with patch("handshakelab.cli.Vault") as mock_vault:
        mock_vault.return_value.get_run.return_value = rec
        mock_vault.return_value.get_crack_result.return_value = crack
        result = runner.invoke(app, ["show", "abc", "--reveal"])
        assert result.exit_code == 0
        assert "mysecret" in result.stdout


def test_crack_command_success(runner):
    """handshakelab crack with successful result shows 'Cracked'."""
    from handshakelab.crack import CrackOutput

    out = CrackOutput(
        run_id="abc", success=True, passphrase="recovered", duration_ms=100, method="m"
    )
    with patch("handshakelab.cli.crack_run", return_value=out):
        wl = "/tmp/wl.txt"
        result = runner.invoke(app, ["crack", "abc", "--wordlist", wl])
        assert result.exit_code == 0
        assert "Cracked" in result.stdout
        # Passphrase should be masked, not in plaintext
        assert "recovered" not in result.stdout


def test_crack_command_no_match(runner):
    """handshakelab crack with no match exits 2."""
    from handshakelab.crack import CrackOutput

    out = CrackOutput(
        run_id="abc", success=False, passphrase=None, duration_ms=100, method="m"
    )
    with patch("handshakelab.cli.crack_run", return_value=out):
        result = runner.invoke(app, ["crack", "abc", "--wordlist", "/tmp/wl.txt"])
        assert result.exit_code == 2
        assert "No match" in result.stdout


def test_crack_command_error(runner):
    """handshakelab crack on error exits 1."""
    from handshakelab.crack import CrackError

    with patch("handshakelab.cli.crack_run", side_effect=CrackError("nope")):
        result = runner.invoke(app, ["crack", "abc", "--wordlist", "/tmp/wl.txt"])
        assert result.exit_code == 1
        assert "nope" in result.stdout or "nope" in result.stderr


def test_report_invalid_format(runner):
    """handshakelab report with invalid format exits 1."""
    result = runner.invoke(app, ["report", "abc", "--format", "xml"])
    assert result.exit_code == 1
    assert "md or json" in result.stdout or "md or json" in result.stderr


def test_report_markdown_written(runner, tmp_path, monkeypatch):
    """handshakelab report --format md writes a report file."""
    monkeypatch.setattr(
        "handshakelab.cli.load_config", lambda path: LabConfig(path=Path("lab.toml"))
    )

    from handshakelab.vault import RunRecord

    rec = RunRecord(
        id="abc",
        created_at="2026-06-14",
        operator="t",
        ssid="LAB",
        bssid=None,
        channel=None,
        adapter="en0",
        capture_path=str(tmp_path / "cap.pcapng"),
        hash_path=None,
        status="captured",
        authorized_by="",
        platform="Darwin",
    )
    with (
        patch("handshakelab.cli.Vault") as mock_vault,
        patch("handshakelab.report.Vault") as report_vault,
    ):
        mock_vault.return_value.get_run.return_value = rec
        mock_vault.return_value.get_crack_result.return_value = None
        report_vault.return_value.get_run.return_value = rec
        report_vault.return_value.get_crack_result.return_value = None
        with patch("handshakelab.report.run_dir_for", return_value=tmp_path):
            result = runner.invoke(app, ["report", "abc", "--format", "md"])
            assert result.exit_code == 0
            assert (tmp_path / "report.md").exists()


def test_scan_no_networks(runner):
    """handshakelab scan with no networks exits 1."""
    with patch("handshakelab.cli.scan_networks", return_value=[]):
        result = runner.invoke(app, ["scan", "-i", "en0"])
        assert result.exit_code == 1
        assert "No networks" in result.stdout or "No networks" in result.stderr


def test_scan_with_networks(runner):
    """handshakelab scan with networks prints a table."""
    from handshakelab.util.wifi import Network

    networks = [Network(ssid="LAB-AP", bssid="AA:BB:CC:DD:EE:FF", channel=6, rssi=-50, security="WPA2")]
    with patch("handshakelab.cli.scan_networks", return_value=networks):
        result = runner.invoke(app, ["scan", "-i", "en0"])
        assert result.exit_code == 0
        assert "LAB-AP" in result.stdout

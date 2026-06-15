"""Tests for the convert pipeline (hcxpcapngtool is mocked)."""

from pathlib import Path
from unittest import mock

import pytest

from handshakelab.convert import ConvertError, convert_file, convert_run
from handshakelab.vault import RunRecord, Vault


def _seed_vault(tmp_path: Path, monkeypatch) -> tuple[str, Path]:
    monkeypatch.setattr(
        "handshakelab.util.platform.vault_db_path",
        lambda: tmp_path / "vault.db",
    )
    monkeypatch.setattr(
        "handshakelab.util.platform.captures_dir",
        lambda: tmp_path / "captures",
    )
    vault = Vault()
    run_id, run_dir = vault.create_run_dir()
    cap = run_dir / "capture.pcapng"
    cap.write_bytes(b"fake-pcapng")
    vault.insert_run(
        RunRecord(
            id=run_id,
            created_at="2026-06-14T10:00:00+00:00",
            operator="t",
            ssid="LAB",
            bssid="AA:BB:CC:DD:EE:FF",
            channel=6,
            adapter="wlan0",
            capture_path=str(cap),
            hash_path=None,
            status="captured",
            authorized_by="QA",
            platform="t",
        )
    )
    return run_id, run_dir


def test_convert_run_missing_hcxtools(tmp_path: Path, monkeypatch):
    run_id, _ = _seed_vault(tmp_path, monkeypatch)
    monkeypatch.setattr("handshakelab.convert.which", lambda _: None)
    with pytest.raises(ConvertError, match="hcxpcapngtool"):
        convert_run(run_id)


def test_convert_run_success(tmp_path: Path, monkeypatch):
    run_id, run_dir = _seed_vault(tmp_path, monkeypatch)
    monkeypatch.setattr("handshakelab.convert.which", lambda _: "/usr/bin/hcxpcapngtool")

    # Mock the subprocess runner to write the .22000 file like the real tool
    def fake_run(argv, **kwargs):
        out_path = Path(argv[argv.index("-o") + 1])
        out_path.write_text("WPA*02*abc*def:hash\n")
        return mock.Mock(ok=True, stdout="", stderr="")

    monkeypatch.setattr("handshakelab.convert.run", fake_run)

    out = convert_run(run_id)
    assert out.hash_count == 1
    assert out.hash_path == run_dir / "crack.22000"


def test_convert_run_no_hashes(tmp_path: Path, monkeypatch):
    run_id, _ = _seed_vault(tmp_path, monkeypatch)
    monkeypatch.setattr("handshakelab.convert.which", lambda _: "/usr/bin/hcxpcapngtool")

    def fake_run(argv, **kwargs):
        # Simulate hcxpcapngtool creating an empty output file
        out_path = Path(argv[argv.index("-o") + 1])
        out_path.touch()
        return mock.Mock(ok=True, stdout="", stderr="")

    monkeypatch.setattr("handshakelab.convert.run", fake_run)

    with pytest.raises(ConvertError, match="No crackable hashes"):
        convert_run(run_id)


def test_convert_file_for_standalone_path(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("handshakelab.convert.which", lambda _: None)
    cap = tmp_path / "loose.pcapng"
    cap.write_bytes(b"x")
    with pytest.raises(ConvertError, match="hcxpcapngtool"):
        convert_file(cap)

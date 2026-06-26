"""Tests for handshakelab.convert — pcapng → .22000 conversion."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from handshakelab.convert import (
    ConvertError,
    ConvertResult,
    convert_file,
    convert_run,
)
from handshakelab.vault import RunRecord, Vault


def _make_vault_run(tmp_path, monkeypatch, ssid="LAB-AP") -> RunRecord:
    monkeypatch.setattr(
        "handshakelab.util.platform.vault_db_path", lambda: tmp_path / "vault.db"
    )
    monkeypatch.setattr(
        "handshakelab.util.platform.captures_dir", lambda: tmp_path / "captures"
    )
    vault = Vault()
    run_id, run_dir = vault.create_run_dir()
    cap = run_dir / "capture.pcapng"
    cap.write_bytes(b"fake pcap")
    rec = RunRecord(
        id=run_id,
        created_at="2026-06-14T10:00:00+00:00",
        operator="tester",
        ssid=ssid,
        bssid="AA:BB:CC:DD:EE:FF",
        channel=6,
        adapter="en0",
        capture_path=str(cap),
        hash_path=None,
        status="captured",
        authorized_by="QA-1",
        platform="Darwin test",
    )
    vault.insert_run(rec)
    return rec


def test_convert_run_raises_on_missing_run(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "handshakelab.util.platform.vault_db_path", lambda: tmp_path / "vault.db"
    )
    monkeypatch.setattr(
        "handshakelab.util.platform.captures_dir", lambda: tmp_path / "captures"
    )
    with pytest.raises(ConvertError, match="Run not found"):
        convert_run("nonexistent-run-id")


def test_convert_run_raises_on_missing_capture(tmp_path, monkeypatch):
    rec = _make_vault_run(tmp_path, monkeypatch)
    # Delete the capture file
    Path(rec.capture_path).unlink()
    with pytest.raises(ConvertError, match="Capture missing"):
        convert_run(rec.id)


def test_convert_run_raises_when_hcxpcapngtool_missing(tmp_path, monkeypatch):
    _make_vault_run(tmp_path, monkeypatch)
    with patch("handshakelab.convert.which", return_value=None):
        with pytest.raises(ConvertError, match="hcxpcapngtool not found"):
            convert_run("latest")


def test_convert_file_raises_when_hcxpcapngtool_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "handshakelab.util.platform.vault_db_path", lambda: tmp_path / "vault.db"
    )
    monkeypatch.setattr(
        "handshakelab.util.platform.captures_dir", lambda: tmp_path / "captures"
    )
    fake_pcap = tmp_path / "standalone.pcapng"
    fake_pcap.write_bytes(b"x")
    with patch("handshakelab.convert.which", return_value=None):
        with pytest.raises(ConvertError, match="hcxpcapngtool not found"):
            convert_file(fake_pcap)


def test_convert_file_standalone_raises_on_no_output(tmp_path, monkeypatch):
    """convert_file with no matching run goes standalone; if hcx succeeds but no file, error."""
    monkeypatch.setattr(
        "handshakelab.util.platform.vault_db_path", lambda: tmp_path / "vault.db"
    )
    monkeypatch.setattr(
        "handshakelab.util.platform.captures_dir", lambda: tmp_path / "captures"
    )
    fake_pcap = tmp_path / "standalone.pcapng"
    fake_pcap.write_bytes(b"x")

    fake_hcx = "/opt/homebrew/bin/hcxpcapngtool"
    fake_result = type("R", (), {"ok": True, "stdout": "", "stderr": ""})()
    with (
        patch("handshakelab.convert.which", return_value=fake_hcx),
        patch("handshakelab.convert.run", return_value=fake_result),
    ):
        # No crack.22000 file is written by the mock; expect "produced no output" error
        with pytest.raises(ConvertError, match="produced no output"):
            convert_file(fake_pcap)


def test_convert_file_standalone_succeeds(tmp_path, monkeypatch):
    """convert_file standalone path creates crack.22000 and returns result."""
    monkeypatch.setattr(
        "handshakelab.util.platform.vault_db_path", lambda: tmp_path / "vault.db"
    )
    monkeypatch.setattr(
        "handshakelab.util.platform.captures_dir", lambda: tmp_path / "captures"
    )
    fake_pcap = tmp_path / "standalone.pcapng"
    fake_pcap.write_bytes(b"x")
    hash_out = tmp_path / "crack.22000"

    fake_hcx = "/opt/homebrew/bin/hcxpcapngtool"
    fake_result = type("R", (), {"ok": True, "stdout": "", "stderr": ""})()

    def fake_run(argv, **kwargs):
        # Last argv is the capture; -o is the output
        if "-o" in argv:
            hash_out.write_text("WPA*02*hash*here:secret123\n")
        return fake_result

    with (
        patch("handshakelab.convert.which", return_value=fake_hcx),
        patch("handshakelab.convert.run", side_effect=fake_run),
    ):
        result = convert_file(fake_pcap)
        assert isinstance(result, ConvertResult)
        assert result.run_id == "standalone"
        assert result.hash_count == 1
        assert hash_out.exists()


def test_convert_dataclass():
    """ConvertResult dataclass fields."""
    r = ConvertResult(run_id="abc", hash_path=Path("/tmp/h.22000"), hash_count=5)
    assert r.run_id == "abc"
    assert r.hash_count == 5
    assert r.hash_path == Path("/tmp/h.22000")

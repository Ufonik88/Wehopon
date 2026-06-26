"""Tests for handshakelab.report — QA report generation."""

from __future__ import annotations

import json

import pytest

from handshakelab.report import (
    _mask,
    _safe_crack_payload,
    report_json,
    report_markdown,
    write_report,
)
from handshakelab.vault import CrackResult, RunRecord, Vault


def _make_run(tmp_path, monkeypatch, *, cracked_passphrase="secret123") -> RunRecord:
    monkeypatch.setattr(
        "handshakelab.util.platform.vault_db_path", lambda: tmp_path / "vault.db"
    )
    monkeypatch.setattr(
        "handshakelab.util.platform.captures_dir", lambda: tmp_path / "captures"
    )
    vault = Vault()
    run_id, run_dir = vault.create_run_dir()
    cap = run_dir / "capture.pcapng"
    cap.write_bytes(b"x")
    rec = RunRecord(
        id=run_id,
        created_at="2026-06-14T10:00:00+00:00",
        operator="tester",
        ssid="LAB",
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
    if cracked_passphrase:
        vault.save_crack_result(
            CrackResult(
                run_id=run_id,
                cracked_at="2026-06-14T10:01:00+00:00",
                method="hashcat:22000:wordlist.txt",
                duration_ms=100,
                passphrase=cracked_passphrase,
                success=True,
            )
        )
    return rec


def test_mask_short_value():
    """Values of length <= 2 are fully masked."""
    assert _mask("") == ""
    assert _mask("a") == "*"
    assert _mask("ab") == "**"


def test_mask_normal_value():
    """Longer values show first + last char only."""
    assert _mask("password") == "p******d"
    assert _mask("secret123") == "s*******3"
    assert _mask("xyz") == "x*z"


def test_mask_none_or_empty_safe():
    """Empty/None values are returned as empty string."""
    assert _mask("") == ""


def test_safe_crack_payload_no_passphrase():
    """safe_crack_payload with no plaintext leaves mask as None."""
    c = CrackResult(
        run_id="x", cracked_at="t", method="m", duration_ms=0, passphrase=None, success=False
    )
    payload = _safe_crack_payload(c)
    assert payload["passphrase_masked"] is None
    assert payload["success"] is False
    assert "passphrase" not in payload  # plaintext key never present


def test_safe_crack_payload_with_passphrase():
    """safe_crack_payload with plaintext returns masked form only."""
    c = CrackResult(
        run_id="x",
        cracked_at="t",
        method="m",
        duration_ms=0,
        passphrase="supersecret",
        success=True,
    )
    payload = _safe_crack_payload(c)
    assert payload["passphrase_masked"] == "s*********t"
    assert "supersecret" not in str(payload)
    assert "passphrase" not in payload  # plaintext key not present


def test_report_markdown_contains_metadata(tmp_path, monkeypatch):
    rec = _make_run(tmp_path, monkeypatch)
    md = report_markdown(rec.id)
    assert "# HandshakeLab QA Report" in md
    assert rec.id in md
    assert "LAB" in md  # SSID
    assert "Offline crack only" in md


def test_report_markdown_masks_passphrase(tmp_path, monkeypatch):
    rec = _make_run(tmp_path, monkeypatch, cracked_passphrase="topsecret")
    md = report_markdown(rec.id)
    assert "topsecret" not in md
    assert "use `handshakelab show" in md


def test_report_markdown_raises_on_missing_run(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "handshakelab.util.platform.vault_db_path", lambda: tmp_path / "vault.db"
    )
    monkeypatch.setattr(
        "handshakelab.util.platform.captures_dir", lambda: tmp_path / "captures"
    )
    with pytest.raises(ValueError, match="Run not found"):
        report_markdown("nonexistent")


def test_report_markdown_no_crack_result(tmp_path, monkeypatch):
    rec = _make_run(tmp_path, monkeypatch, cracked_passphrase=None)
    md = report_markdown(rec.id)
    assert "Crack result" not in md  # no section when no crack


def test_report_json_contains_run(tmp_path, monkeypatch):
    rec = _make_run(tmp_path, monkeypatch)
    js = report_json(rec.id)
    data = json.loads(js)
    assert data["run"]["id"] == rec.id
    assert data["run"]["ssid"] == "LAB"
    assert data["crack"]["success"] is True


def test_report_json_masks_passphrase(tmp_path, monkeypatch):
    rec = _make_run(tmp_path, monkeypatch, cracked_passphrase="topsecret")
    js = report_json(rec.id)
    data = json.loads(js)
    # The plaintext passphrase must not appear anywhere in the JSON
    assert "topsecret" not in js
    assert data["crack"]["passphrase_masked"] == "t*******t"


def test_report_json_raises_on_missing_run(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "handshakelab.util.platform.vault_db_path", lambda: tmp_path / "vault.db"
    )
    monkeypatch.setattr(
        "handshakelab.util.platform.captures_dir", lambda: tmp_path / "captures"
    )
    with pytest.raises(ValueError, match="Run not found"):
        report_json("nonexistent")


def test_write_report_markdown(tmp_path, monkeypatch):
    rec = _make_run(tmp_path, monkeypatch)
    out = write_report(rec.id, "md")
    assert out.exists()
    assert out.suffix == ".md"
    assert "QA Report" in out.read_text()


def test_write_report_json(tmp_path, monkeypatch):
    rec = _make_run(tmp_path, monkeypatch)
    out = write_report(rec.id, "json")
    assert out.exists()
    assert out.suffix == ".json"
    data = json.loads(out.read_text())
    assert data["run"]["id"] == rec.id


def test_write_report_raises_on_missing_run(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "handshakelab.util.platform.vault_db_path", lambda: tmp_path / "vault.db"
    )
    monkeypatch.setattr(
        "handshakelab.util.platform.captures_dir", lambda: tmp_path / "captures"
    )
    with pytest.raises(ValueError, match="Run not found"):
        write_report("nonexistent", "md")

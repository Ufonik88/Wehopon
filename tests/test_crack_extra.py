"""Tests for handshakelab.crack — Hashcat offline crack orchestration."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from handshakelab.config import CrackConfig
from handshakelab.crack import (
    CrackError,
    _hashcat_show,
    _parse_potfile,
    attempt_crack,
    crack_run,
)
from handshakelab.vault import RunRecord, Vault


def _make_run(tmp_path, monkeypatch, *, with_hash=True) -> RunRecord:
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
    hash_path = run_dir / "crack.22000" if with_hash else None
    if with_hash:
        hash_path.write_text("WPA*02*hash:secret123\n")
    rec = RunRecord(
        id=run_id,
        created_at="2026-06-14T10:00:00+00:00",
        operator="tester",
        ssid="LAB",
        bssid="AA:BB:CC:DD:EE:FF",
        channel=6,
        adapter="en0",
        capture_path=str(cap),
        hash_path=str(hash_path) if hash_path else None,
        status="captured",
        authorized_by="QA-1",
        platform="Darwin test",
    )
    vault.insert_run(rec)
    return rec


def test_crack_run_raises_on_missing_run(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "handshakelab.util.platform.vault_db_path", lambda: tmp_path / "vault.db"
    )
    monkeypatch.setattr(
        "handshakelab.util.platform.captures_dir", lambda: tmp_path / "captures"
    )
    wl = tmp_path / "wl.txt"
    wl.write_text("secret\n")
    with pytest.raises(CrackError, match="Run not found"):
        crack_run("nope", wordlist=wl)


def test_crack_run_raises_when_not_converted(tmp_path, monkeypatch):
    rec = _make_run(tmp_path, monkeypatch, with_hash=False)
    wl = tmp_path / "wl.txt"
    wl.write_text("x\n")
    with pytest.raises(CrackError, match="not converted"):
        crack_run(rec.id, wordlist=wl)


def test_crack_run_raises_when_wordlist_missing(tmp_path, monkeypatch):
    rec = _make_run(tmp_path, monkeypatch)
    with pytest.raises(CrackError, match="Wordlist required"):
        crack_run(rec.id, wordlist=tmp_path / "nonexistent.txt")


def test_crack_run_succeeds_with_mock_hashcat(tmp_path, monkeypatch):
    rec = _make_run(tmp_path, monkeypatch)
    wl = tmp_path / "wl.txt"
    wl.write_text("secret123\n")

    fake_hc = "/opt/homebrew/bin/hashcat"

    def fake_run(argv, **kwargs):
        # When hashcat finishes, simulate potfile
        if "--potfile-path" in argv:
            pot_idx = argv.index("--potfile-path")
            pot = Path(argv[pot_idx + 1])
            pot.write_text("WPA*02*hash*here:secret123\n")
        return type("R", (), {"ok": True, "stdout": "", "stderr": "Recovered: secret123"})()

    cfg = CrackConfig(hashcat_bin=fake_hc, wordlist=str(wl), workload_profile=2)
    with (
        patch("handshakelab.crack.which", return_value=fake_hc),
        patch("handshakelab.crack.run", side_effect=fake_run),
    ):
        out = crack_run(rec.id, wordlist=wl, crack_config=cfg)
        assert out.success is True
        assert out.passphrase == "secret123"
        assert out.method.startswith("hashcat:22000:")


def test_crack_run_fails_when_no_match(tmp_path, monkeypatch):
    rec = _make_run(tmp_path, monkeypatch)
    wl = tmp_path / "wl.txt"
    wl.write_text("wrongword\n")

    fake_hc = "/opt/homebrew/bin/hashcat"

    def fake_run(argv, **kwargs):
        return type("R", (), {"ok": False, "stdout": "Exhausted", "stderr": ""})()

    cfg = CrackConfig(hashcat_bin=fake_hc, wordlist=str(wl), workload_profile=2)
    with (
        patch("handshakelab.crack.which", return_value=fake_hc),
        patch("handshakelab.crack.run", side_effect=fake_run),
    ):
        out = crack_run(rec.id, wordlist=wl, crack_config=cfg)
        assert out.success is False
        assert out.passphrase is None


def test_attempt_crack_raises_on_missing_wordlist(tmp_path):
    with pytest.raises(CrackError, match="Wordlist not found"):
        attempt_crack(Path("/tmp/h.22000"), tmp_path / "missing.txt")


def test_attempt_crack_raises_when_hashcat_missing(tmp_path):
    h = tmp_path / "h.22000"
    h.write_text("x")
    wl = tmp_path / "wl.txt"
    wl.write_text("x")
    # CrackConfig with a non-existent hashcat path + which() returns None
    cfg = CrackConfig(hashcat_bin="/nonexistent/hashcat", wordlist=str(wl), workload_profile=2)
    with patch("handshakelab.crack.which", return_value=None):
        with pytest.raises(CrackError, match="hashcat not found"):
            attempt_crack(h, wl, cfg=cfg)


def test_parse_potfile_missing_returns_none(tmp_path):
    assert _parse_potfile(tmp_path / "missing.potfile") is None


def test_parse_potfile_empty_returns_none(tmp_path):
    pf = tmp_path / "empty.potfile"
    pf.write_text("")
    assert _parse_potfile(pf) is None


def test_parse_potfile_returns_passphrase(tmp_path):
    pf = tmp_path / "good.potfile"
    pf.write_text("WPA*02*hash*here:secret123\n")
    assert _parse_potfile(pf) == "secret123"


def test_hashcat_show_returns_passphrase():
    fake = type("R", (), {"ok": True, "stdout": "WPA*02*hash:secret\n", "stderr": ""})()
    with patch("handshakelab.crack.run", return_value=fake):
        assert _hashcat_show("hashcat", Path("/tmp/h.22000")) == "secret"


def test_hashcat_show_returns_none_on_failure():
    fake = type("R", (), {"ok": False, "stdout": "", "stderr": ""})()
    with patch("handshakelab.crack.run", return_value=fake):
        assert _hashcat_show("hashcat", Path("/tmp/h.22000")) is None


def test_hashcat_show_returns_none_on_no_colon():
    fake = type("R", (), {"ok": True, "stdout": "no_colon_line\n", "stderr": ""})()
    with patch("handshakelab.crack.run", return_value=fake):
        assert _hashcat_show("hashcat", Path("/tmp/h.22000")) is None

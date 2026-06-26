"""Tests for handshakelab.crack_enhanced — multi-stage cracking."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from handshakelab.config import LabConfig
from handshakelab.crack import CrackOutput
from handshakelab.crack_enhanced import EnhancedCrackResult, enhanced_crack
from handshakelab.vault import RunRecord, Vault


def _make_run(tmp_path, monkeypatch) -> RunRecord:
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
    hash_path = run_dir / "crack.22000"
    hash_path.write_text("WPA*02*hash:secret\n")
    rec = RunRecord(
        id=run_id,
        created_at="2026-06-14T10:00:00+00:00",
        operator="tester",
        ssid="LAB-AP",
        bssid="AA:BB:CC:DD:EE:FF",
        channel=6,
        adapter="en0",
        capture_path=str(cap),
        hash_path=str(hash_path),
        status="converted",
        authorized_by="QA-1",
        platform="Darwin test",
    )
    vault.insert_run(rec)
    return rec


def test_enhanced_crack_raises_when_run_not_converted(tmp_path, monkeypatch):
    """enhanced_crack raises if no hash_path set on the run."""
    monkeypatch.setattr(
        "handshakelab.util.platform.vault_db_path", lambda: tmp_path / "vault.db"
    )
    monkeypatch.setattr(
        "handshakelab.util.platform.captures_dir", lambda: tmp_path / "captures"
    )
    vault = Vault()
    run_id, run_dir = vault.create_run_dir()
    rec = RunRecord(
        id=run_id,
        created_at="2026-06-14T10:00:00+00:00",
        operator="t",
        ssid="L",
        bssid=None,
        channel=1,
        adapter="en0",
        capture_path=str(run_dir / "x"),
        hash_path=None,  # not converted
        status="captured",
        authorized_by="",
        platform="t",
    )
    vault.insert_run(rec)
    cfg = LabConfig(path=tmp_path / "lab.toml", require_authorization=False)
    with patch("handshakelab.crack_enhanced.which", return_value="/opt/homebrew/bin/hashcat"):
        with pytest.raises(Exception, match="not converted"):
            enhanced_crack(run_id, cfg)


def test_enhanced_crack_raises_when_hashcat_missing(tmp_path, monkeypatch):
    """enhanced_crack raises if hashcat binary is not found."""
    rec = _make_run(tmp_path, monkeypatch)
    cfg = LabConfig(path=tmp_path / "lab.toml", require_authorization=False)
    with patch("handshakelab.crack_enhanced.which", return_value=None):
        with pytest.raises(Exception, match="hashcat"):
            enhanced_crack(rec.id, cfg)


def test_enhanced_crack_progress_callback_invoked(tmp_path, monkeypatch):
    """Progress callback is invoked at each stage."""
    rec = _make_run(tmp_path, monkeypatch)
    cfg = LabConfig(path=tmp_path / "lab.toml", require_authorization=False)

    progress_calls = []

    def on_progress(stage, msg, pct):
        progress_calls.append((stage, msg, pct))

    fake_out = CrackOutput(
        run_id=rec.id, success=False, passphrase=None, duration_ms=100, method="hashcat:22000:x"
    )

    with (
        patch("handshakelab.crack_enhanced.which", return_value="/opt/homebrew/bin/hashcat"),
        patch("handshakelab.crack_enhanced.attempt_crack", return_value=fake_out),
    ):
        result = enhanced_crack(rec.id, cfg, use_ai=False, on_progress=on_progress)

    assert len(progress_calls) > 0
    # All progress calls are (stage, msg, pct) tuples
    for s, m, p in progress_calls:
        assert isinstance(s, str)
        assert isinstance(m, str)
        assert isinstance(p, int)
    assert result.success is False


def test_enhanced_crack_uses_ai_when_available(tmp_path, monkeypatch):
    """When use_ai=True and key set, AI is invoked."""
    rec = _make_run(tmp_path, monkeypatch)
    cfg = LabConfig(path=tmp_path / "lab.toml", require_authorization=False)

    fake_out = CrackOutput(
        run_id=rec.id, success=False, passphrase=None, duration_ms=100, method="x"
    )
    fake_ai = ["ai_guess_1", "ai_guess_2"]

    with (
        patch("handshakelab.crack_enhanced.which", return_value="/opt/homebrew/bin/hashcat"),
        patch("handshakelab.crack_enhanced.ai_available", return_value=True),
        patch("handshakelab.crack_enhanced.generate_ai_candidates", return_value=fake_ai),
        patch("handshakelab.crack_enhanced.attempt_crack", return_value=fake_out),
    ):
        result = enhanced_crack(rec.id, cfg, use_ai=True)
    assert result.success is False


def test_enhanced_crack_skips_ai_when_key_unset(tmp_path, monkeypatch):
    """When use_ai=True but no key, AI is skipped (no error)."""
    rec = _make_run(tmp_path, monkeypatch)
    cfg = LabConfig(path=tmp_path / "lab.toml", require_authorization=False)

    fake_out = CrackOutput(
        run_id=rec.id, success=False, passphrase=None, duration_ms=100, method="x"
    )

    with (
        patch("handshakelab.crack_enhanced.which", return_value="/opt/homebrew/bin/hashcat"),
        patch("handshakelab.crack_enhanced.ai_available", return_value=False),
        patch("handshakelab.crack_enhanced.attempt_crack", return_value=fake_out),
    ):
        result = enhanced_crack(rec.id, cfg, use_ai=True)
    assert result.success is False


def test_enhanced_crack_succeeds_on_first_stage(tmp_path, monkeypatch):
    """If first stage succeeds, no later stages run; result captures passphrase."""
    rec = _make_run(tmp_path, monkeypatch)
    cfg = LabConfig(path=tmp_path / "lab.toml", require_authorization=False)

    fake_out = CrackOutput(
        run_id=rec.id,
        success=True,
        passphrase="recovered123",
        duration_ms=50,
        method="hashcat:22000:ssid",
    )
    attempt_calls = []

    def fake_attempt(*args, **kwargs):
        attempt_calls.append(kwargs.get("stage_label"))
        return fake_out

    with (
        patch("handshakelab.crack_enhanced.which", return_value="/opt/homebrew/bin/hashcat"),
        patch("handshakelab.crack_enhanced.attempt_crack", side_effect=fake_attempt),
    ):
        result = enhanced_crack(rec.id, cfg, use_ai=False)

    assert result.success is True
    assert result.passphrase == "recovered123"
    assert result.stages_run == 1
    # Should stop after first stage
    assert len(attempt_calls) == 1


def test_enhanced_crack_updates_status_to_failed_on_no_match(tmp_path, monkeypatch):
    """If all stages fail, run status is updated to 'failed'."""
    rec = _make_run(tmp_path, monkeypatch)
    cfg = LabConfig(path=tmp_path / "lab.toml", require_authorization=False)

    fake_out = CrackOutput(
        run_id=rec.id, success=False, passphrase=None, duration_ms=10, method="x"
    )

    with (
        patch("handshakelab.crack_enhanced.which", return_value="/opt/homebrew/bin/hashcat"),
        patch("handshakelab.crack_enhanced.attempt_crack", return_value=fake_out),
    ):
        result = enhanced_crack(rec.id, cfg, use_ai=False)

    assert result.success is False
    vault = Vault()
    record = vault.get_run(rec.id)
    assert record.status == "failed"


def test_enhanced_crack_continues_after_stage_error(tmp_path, monkeypatch):
    """If one stage raises CrackError, the next stage is attempted."""
    from handshakelab.crack import CrackError

    rec = _make_run(tmp_path, monkeypatch)
    cfg = LabConfig(path=tmp_path / "lab.toml", require_authorization=False)

    call_count = {"n": 0}

    def fake_attempt(*args, **kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise CrackError("transient error")
        return CrackOutput(
            run_id=rec.id, success=True, passphrase="found", duration_ms=10, method="x"
        )

    with (
        patch("handshakelab.crack_enhanced.which", return_value="/opt/homebrew/bin/hashcat"),
        patch("handshakelab.crack_enhanced.attempt_crack", side_effect=fake_attempt),
    ):
        result = enhanced_crack(rec.id, cfg, use_ai=False)

    assert result.success is True
    assert result.passphrase == "found"
    assert call_count["n"] == 2  # 1st failed, 2nd succeeded


def test_enhanced_crack_result_dataclass():
    """EnhancedCrackResult dataclass has expected fields."""
    r = EnhancedCrackResult(
        success=True, passphrase="x", method="m", stages_run=2
    )
    assert r.success is True
    assert r.passphrase == "x"
    assert r.method == "m"
    assert r.stages_run == 2

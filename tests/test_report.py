"""Tests for the QA report generator."""

from pathlib import Path

from handshakelab.report import _mask, report_json, report_markdown
from handshakelab.vault import CrackResult, RunRecord, Vault


def test_mask_short_string():
    assert _mask("a") == "*"
    assert _mask("ab") == "**"
    assert _mask("abc") == "a*c"
    assert _mask("") == ""
    assert _mask("hello") == "h***o"


def test_mask_none_safe():
    assert _mask(None) == ""  # type: ignore[arg-type]


def _setup_run(tmp_path: Path, monkeypatch) -> str:
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
    cap.write_bytes(b"test")
    record = RunRecord(
        id=run_id,
        created_at="2026-06-14T10:00:00+00:00",
        operator="tester",
        ssid="LAB",
        bssid="AA:BB:CC:DD:EE:FF",
        channel=6,
        adapter="wlan0",
        capture_path=str(cap),
        hash_path=None,
        status="cracked",
        authorized_by="QA-1",
        platform="Linux test",
    )
    vault.insert_run(record)
    vault.save_crack_result(
        CrackResult(
            run_id=run_id,
            cracked_at="2026-06-14T10:01:00+00:00",
            method="hashcat:22000:qa.txt",
            duration_ms=42,
            passphrase="superSecret123",
            success=True,
        )
    )
    return run_id


def test_markdown_report_does_not_leak_passphrase(tmp_path: Path, monkeypatch):
    run_id = _setup_run(tmp_path, monkeypatch)
    md = report_markdown(run_id)
    assert "superSecret123" not in md
    assert "[recovered" in md
    assert "QA Report" in md


def test_json_report_masks_passphrase(tmp_path: Path, monkeypatch):
    import json

    run_id = _setup_run(tmp_path, monkeypatch)
    payload = json.loads(report_json(run_id))
    # Plaintext passphrase must NOT appear
    assert "superSecret123" not in payload["crack"]
    # Masked passphrase IS present and uses first + last char pattern
    masked = payload["crack"]["passphrase_masked"]
    assert masked.startswith("s")
    assert masked.endswith("3")
    assert masked.count("*") == len("superSecret123") - 2
    # Success flag still surfaces
    assert payload["crack"]["success"] is True
    assert payload["crack"]["method"] == "hashcat:22000:qa.txt"


def test_json_report_with_no_crack(tmp_path: Path, monkeypatch):
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
    (run_dir / "capture.pcapng").write_bytes(b"x")
    vault.insert_run(
        RunRecord(
            id=run_id,
            created_at="2026-06-14T10:00:00+00:00",
            operator="t",
            ssid="S",
            bssid=None,
            channel=None,
            adapter=None,
            capture_path=str(run_dir / "capture.pcapng"),
            hash_path=None,
            status="captured",
            authorized_by=None,
            platform="t",
        )
    )
    import json

    payload = json.loads(report_json(run_id))
    assert payload["crack"] is None

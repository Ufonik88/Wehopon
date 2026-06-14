from pathlib import Path

from handshakelab.vault import CrackResult, RunRecord, Vault


def test_vault_roundtrip(tmp_path: Path, monkeypatch):
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
        status="captured",
        authorized_by="QA-1",
        platform="Linux test",
    )
    vault.insert_run(record)

    loaded = vault.get_run(run_id)
    assert loaded is not None
    assert loaded.ssid == "LAB"

    vault.save_crack_result(
        CrackResult(
            run_id=run_id,
            cracked_at="2026-06-14T10:01:00+00:00",
            method="hashcat:22000:test.txt",
            duration_ms=100,
            passphrase="secret123",
            success=True,
        )
    )
    crack = vault.get_crack_result(run_id)
    assert crack is not None
    assert crack.passphrase == "secret123"
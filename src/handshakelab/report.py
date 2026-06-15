"""QA report generation."""

from __future__ import annotations

import json
from pathlib import Path

from handshakelab.vault import CrackResult, Vault, run_dir_for


def _mask(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 2:
        return "*" * len(value)
    return value[0] + "*" * (len(value) - 2) + value[-1]


def _safe_crack_payload(crack: CrackResult) -> dict:
    """Return a JSON-safe crack dict. Never include the plaintext passphrase."""
    return {
        "run_id": crack.run_id,
        "cracked_at": crack.cracked_at,
        "method": crack.method,
        "duration_ms": crack.duration_ms,
        "success": crack.success,
        "passphrase_masked": _mask(crack.passphrase) if crack.passphrase else None,
    }


def report_markdown(run_id: str) -> str:
    vault = Vault()
    record = vault.get_run(run_id)
    if not record:
        raise ValueError(f"Run not found: {run_id}")

    crack = vault.get_crack_result(run_id)
    lines = [
        "# HandshakeLab QA Report",
        "",
        f"- **Run ID:** `{record.id}`",
        f"- **SSID:** {record.ssid}",
        f"- **BSSID:** {record.bssid or 'n/a'}",
        f"- **Channel:** {record.channel or 'n/a'}",
        f"- **Platform:** {record.platform}",
        f"- **Captured:** {record.created_at}",
        f"- **Status:** {record.status}",
        f"- **Authorization:** {record.authorized_by or 'n/a'}",
        f"- **Capture SHA-256:** `{record.capture_sha256 or 'n/a'}`",
    ]

    if crack:
        lines.extend(
            [
                "",
                "## Crack result",
                f"- **Method:** {crack.method}",
                f"- **Duration:** {crack.duration_ms} ms",
                f"- **Success:** {'yes' if crack.success else 'no'}",
                f"- **Passphrase:** {'[recovered — use `handshakelab show <run> --reveal`]' if crack.success else 'n/a'}",
            ]
        )

    lines.extend(
        [
            "",
            "## Artifacts",
            f"- Capture: `{record.capture_path}`",
            f"- Hash: `{record.hash_path or 'n/a'}`",
            "",
            "*Offline crack only — no online authentication attempts were made against the AP.*",
        ]
    )
    return "\n".join(lines)


def report_json(run_id: str) -> str:
    """JSON report with the plaintext passphrase masked.

    The plaintext passphrase is only ever exposed through
    `handshakelab show <run> --reveal` so it cannot leak via shared
    QA artifacts.
    """
    vault = Vault()
    record = vault.get_run(run_id)
    if not record:
        raise ValueError(f"Run not found: {run_id}")
    crack = vault.get_crack_result(run_id)
    payload = {
        "run": record.__dict__,
        "crack": _safe_crack_payload(crack) if crack else None,
    }
    return json.dumps(payload, indent=2)


def write_report(run_id: str, fmt: str) -> Path:
    vault = Vault()
    record = vault.get_run(run_id)
    if not record:
        raise ValueError(f"Run not found: {run_id}")

    run_dir = run_dir_for(record)
    if fmt == "json":
        content = report_json(run_id)
        path = run_dir / "report.json"
    else:
        content = report_markdown(run_id)
        path = run_dir / "report.md"

    path.write_text(content)
    return path
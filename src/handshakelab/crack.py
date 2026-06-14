"""Offline Hashcat cracking — never contacts the AP."""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from handshakelab.config import CrackConfig
from handshakelab.util.proc import format_cmd, run, which
from handshakelab.vault import CrackResult, Vault


class CrackError(Exception):
    pass


@dataclass
class CrackOutput:
    run_id: str
    success: bool
    passphrase: str | None
    duration_ms: int
    method: str


def crack_run(
    run_id: str,
    *,
    wordlist: Path | None = None,
    crack_config: CrackConfig | None = None,
) -> CrackOutput:
    vault = Vault()
    record = vault.get_run(run_id)
    if not record:
        raise CrackError(f"Run not found: {run_id}")

    if not record.hash_path:
        raise CrackError("Run not converted yet. Run `handshakelab convert` first.")

    hash_path = Path(record.hash_path)
    if not hash_path.exists():
        raise CrackError(f"Hash file missing: {hash_path}")

    cfg = crack_config or CrackConfig()
    wl = wordlist or (Path(cfg.wordlist) if cfg.wordlist else None)
    if not wl or not wl.exists():
        raise CrackError(
            "Wordlist required. Pass --wordlist or set crack.wordlist in lab.toml."
        )

    output = attempt_crack(hash_path, wl, cfg, run_dir=hash_path.parent)
    vault.save_crack_result(
        CrackResult(
            run_id=record.id,
            cracked_at=datetime.now(UTC).isoformat(),
            method=output.method,
            duration_ms=output.duration_ms,
            passphrase=output.passphrase,
            success=output.success,
        )
    )
    return output


def attempt_crack(
    hash_path: Path,
    wordlist: Path,
    cfg: CrackConfig | None = None,
    *,
    run_dir: Path | None = None,
    stage_label: str | None = None,
) -> CrackOutput:
    """Run a single hashcat attempt without touching the vault."""
    cfg = cfg or CrackConfig()
    if not wordlist.exists():
        raise CrackError(f"Wordlist not found: {wordlist}")
    run_id = hash_path.parent.name
    output = _crack_hash(
        hash_path,
        wordlist,
        run_id,
        cfg,
        run_dir=run_dir or hash_path.parent,
        stage_label=stage_label,
    )
    return CrackOutput(
        run_id=run_id,
        success=output.success,
        passphrase=output.passphrase,
        duration_ms=output.duration_ms,
        method=output.method,
    )


def _crack_hash(
    hash_path: Path,
    wordlist: Path,
    run_id: str,
    cfg: CrackConfig,
    *,
    run_dir: Path | None = None,
    stage_label: str | None = None,
    vault: Vault | None = None,
) -> CrackOutput:
    hashcat = cfg.hashcat_bin if Path(cfg.hashcat_bin).exists() else (which("hashcat") or cfg.hashcat_bin)
    if not which(hashcat) and not Path(hashcat).exists():
        raise CrackError("hashcat not found in PATH.")

    run_dir = run_dir or hash_path.parent
    potfile = run_dir / "hashcat.potfile"
    log_path = run_dir / "crack.log"

    # Offline only — hashcat local mode; no network tools invoked.
    argv = [
        hashcat,
        "-m",
        "22000",
        "-a",
        "0",
        "-w",
        str(cfg.workload_profile),
        "--potfile-path",
        str(potfile),
        "--quiet",
        str(hash_path),
        str(wordlist),
    ]

    label = stage_label or wordlist.name
    with log_path.open("a") as log:
        log.write(f"\n# Stage: {label}\n# {format_cmd(argv)}\n")

    start = time.monotonic()
    result = run(argv, timeout=3600)
    elapsed_ms = int((time.monotonic() - start) * 1000)
    with log_path.open("a") as log:
        log.write((result.stdout or "") + (result.stderr or ""))

    passphrase = _parse_potfile(potfile) or _hashcat_show(hashcat, hash_path)

    success = passphrase is not None
    method = f"hashcat:22000:{label}"

    if vault is not None:
        vault.save_crack_result(
            CrackResult(
                run_id=run_id,
                cracked_at=datetime.now(UTC).isoformat(),
                method=method,
                duration_ms=elapsed_ms,
                passphrase=passphrase,
                success=success,
            )
        )

    return CrackOutput(
        run_id=run_id,
        success=success,
        passphrase=passphrase,
        duration_ms=elapsed_ms,
        method=method,
    )


def _parse_potfile(potfile: Path) -> str | None:
    if not potfile.exists():
        return None
    for line in potfile.read_text(errors="ignore").splitlines():
        if not line.strip():
            continue
        # WPA*02*...:passphrase
        if ":" in line:
            return line.rsplit(":", 1)[-1]
    return None


def _hashcat_show(hashcat: str, hash_path: Path) -> str | None:
    result = run([hashcat, "-m", "22000", str(hash_path), "--show"], timeout=60)
    if not result.ok or not result.stdout.strip():
        return None
    line = result.stdout.strip().splitlines()[0]
    if ":" in line:
        return line.rsplit(":", 1)[-1]
    return None
"""Multi-stage enhanced offline cracking."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from handshakelab.ai_wordlist import ai_available, generate_ai_candidates
from handshakelab.config import LabConfig
from handshakelab.crack import CrackError, attempt_crack
from handshakelab.util.proc import which
from handshakelab.vault import CrackResult, Vault
from handshakelab.wordlist_gen import stage_wordlists

ProgressFn = Callable[[str, str, int], None]


@dataclass
class EnhancedCrackResult:
    success: bool
    passphrase: str | None
    method: str
    stages_run: int


def enhanced_crack(
    run_id: str,
    config: LabConfig,
    *,
    use_ai: bool = True,
    on_progress: ProgressFn | None = None,
) -> EnhancedCrackResult:
    def emit(stage: str, msg: str, pct: int) -> None:
        if on_progress:
            on_progress(stage, msg, pct)

    vault = Vault()
    record = vault.get_run(run_id)
    if not record or not record.hash_path:
        raise CrackError("Run not converted")

    hash_path = Path(record.hash_path)
    run_dir = hash_path.parent
    cfg = config.crack

    if not which(cfg.hashcat_bin) and not which("hashcat"):
        raise CrackError("hashcat not installed")

    emit("crack", "Preparing attack stages…", 55)

    ai_candidates: list[str] = []
    if use_ai and ai_available():
        emit("crack", "AI generating smart wordlist candidates…", 58)
        ai_candidates = generate_ai_candidates(
            record.ssid,
            bssid=record.bssid,
            lab_name=config.name,
        )
        emit("crack", f"AI produced {len(ai_candidates)} candidates", 60)
    elif use_ai:
        emit("crack", "AI skipped (set HANDSHAKELAB_AI_API_KEY to enable)", 60)

    config_wl = Path(cfg.wordlist) if cfg.wordlist else None
    stages = stage_wordlists(
        record.ssid,
        bssid=record.bssid,
        work_dir=run_dir,
        config_wordlist=config_wl,
        ai_candidates=ai_candidates or None,
    )

    total = len(stages)
    for idx, (name, wl_path) in enumerate(stages):
        pct = 60 + int(35 * idx / max(total, 1))
        emit("crack", f"Hashcat: {name}…", pct)
        try:
            out = attempt_crack(
                hash_path,
                wl_path,
                cfg,
                run_dir=run_dir,
                stage_label=name,
            )
        except CrackError:
            continue
        if out.success and out.passphrase:
            vault.save_crack_result(
                CrackResult(
                    run_id=record.id,
                    cracked_at=datetime.now(UTC).isoformat(),
                    method=out.method,
                    duration_ms=out.duration_ms,
                    passphrase=out.passphrase,
                    success=True,
                )
            )
            emit("crack", f"Password recovered via {name}", 100)
            return EnhancedCrackResult(
                success=True,
                passphrase=out.passphrase,
                method=out.method,
                stages_run=idx + 1,
            )

    vault.update_run_status(record.id, "failed")
    emit("crack", "No match in any attack stage", 95)
    return EnhancedCrackResult(success=False, passphrase=None, method="", stages_run=total)

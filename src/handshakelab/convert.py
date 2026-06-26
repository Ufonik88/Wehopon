"""Convert capture.pcapng to Hashcat .22000 format."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from handshakelab.util.proc import run, which
from handshakelab.vault import Vault, run_dir_for


class ConvertError(Exception):
    pass


@dataclass
class ConvertResult:
    run_id: str
    hash_path: Path
    hash_count: int


def convert_run(run_id: str) -> ConvertResult:
    vault = Vault()
    record = vault.get_run(run_id)
    if not record:
        raise ConvertError(f"Run not found: {run_id}")

    capture = Path(record.capture_path)
    if not capture.exists():
        raise ConvertError(f"Capture missing: {capture}")

    run_dir = run_dir_for(record)
    hash_path = run_dir / "crack.22000"
    return _convert_file(capture, hash_path, record.id, vault)


def convert_file(path: Path) -> ConvertResult:
    vault = Vault()
    for record in vault.list_runs():
        if Path(record.capture_path).resolve() == path.resolve():
            return convert_run(record.id)

    hash_path = path.parent / "crack.22000"
    return _convert_file(path, hash_path, "standalone", vault)


def _convert_file(
    capture: Path,
    hash_path: Path,
    run_id: str,
    vault: Vault,
) -> ConvertResult:
    hcx = which("hcxpcapngtool")
    if not hcx:
        raise ConvertError("hcxpcapngtool not found. Install hcxtools.")

    log_path = capture.parent / "convert.log"
    result = run([hcx, "-o", str(hash_path), str(capture)], timeout=120)
    log_path.write_text((result.stdout or "") + (result.stderr or ""))

    if not hash_path.exists():
        raise ConvertError("Conversion produced no output file.")

    lines = [ln for ln in hash_path.read_text(errors="ignore").splitlines() if ln.strip()]
    if not lines:
        raise ConvertError(
            "No crackable hashes extracted. Capture may lack a complete WPA handshake or PMKID."
        )

    if run_id != "standalone":
        vault.update_run_status(run_id, "converted", hash_path=str(hash_path))

    return ConvertResult(run_id=run_id, hash_path=hash_path, hash_count=len(lines))

"""WiFi handshake capture — Linux (hcxdumptool) and macOS (hcxdumptool or airport sniff)."""

from __future__ import annotations

import shutil
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from handshakelab.config import LabConfig
from handshakelab.legal import assert_authorized
from handshakelab.util import platform as plat
from handshakelab.util.proc import run, which
from handshakelab.util.wifi import (
    airport_path,
    has_root,
    linux_supports_monitor,
    scan_networks,
    set_linux_monitor_mode,
    validate_eapol,
)
from handshakelab.vault import RunRecord, Vault, sha256_file


class CaptureError(Exception):
    pass


@dataclass
class CaptureResult:
    run_id: str
    run_dir: Path
    capture_path: Path
    ssid: str
    bssid: str | None
    channel: int | None


def capture_handshake(
    *,
    iface: str,
    ssid: str,
    config: LabConfig,
    bssid: str | None = None,
    channel: int | None = None,
    duration_sec: int | None = None,
    ack_authorized: bool = False,
) -> CaptureResult:
    if not has_root():
        raise CaptureError("Capture requires root. Re-run with sudo.")

    assert_authorized(ssid, bssid, config, ack=ack_authorized)

    duration = duration_sec or config.capture.default_duration_sec

    if not bssid or not channel:
        networks = scan_networks(iface)
        for net in networks:
            if net.ssid == ssid:
                bssid = bssid or net.bssid
                channel = channel or net.channel
                break

    if not channel:
        raise CaptureError(
            f"Could not determine channel for SSID '{ssid}'. "
            "Run `handshakelab scan` and pass --channel explicitly."
        )

    vault = Vault()
    run_id, run_dir = vault.create_run_dir()
    capture_path = run_dir / "capture.pcapng"

    if which("hcxdumptool") and (plat.is_linux() or _mac_hcx_viable(iface)):
        _capture_hcxdumptool(
            iface=iface,
            output=capture_path,
            bssid=bssid,
            channel=channel,
            duration=duration,
        )
    elif plat.is_macos() and airport_path():
        cap = _capture_macos_airport(iface=iface, channel=channel, duration=duration, run_dir=run_dir)
        capture_path = _ensure_pcapng(cap, run_dir)
    else:
        raise CaptureError(
            "No capture backend available. Install hcxdumptool (brew install hcxtools) "
            "or use macOS airport utility with a supported interface."
        )

    if not capture_path.exists() or capture_path.stat().st_size == 0:
        raise CaptureError("Capture file is empty. Wait for a client to connect or extend --duration.")

    if not validate_eapol(capture_path):
        raise CaptureError(
            "No EAPOL handshake detected in capture. "
            "Ensure a WiFi client associates with the AP during capture, then retry."
        )

    target = config.find_target(ssid, bssid)
    record = RunRecord(
        id=run_id,
        created_at=datetime.now(UTC).isoformat(),
        operator=config.operator,
        ssid=ssid,
        bssid=bssid,
        channel=channel,
        adapter=iface,
        capture_path=str(capture_path),
        hash_path=None,
        status="captured",
        authorized_by=target.authorization_ref if target else None,
        platform=plat.platform_label(),
        capture_sha256=sha256_file(capture_path),
    )
    vault.insert_run(record)
    vault.write_meta(
        run_dir,
        {
            "run_id": run_id,
            "ssid": ssid,
            "bssid": bssid,
            "channel": channel,
            "adapter": iface,
            "duration_sec": duration,
            "capture_backend": "hcxdumptool" if which("hcxdumptool") else "airport",
        },
    )
    return CaptureResult(
        run_id=run_id,
        run_dir=run_dir,
        capture_path=capture_path,
        ssid=ssid,
        bssid=bssid,
        channel=channel,
    )


def import_capture(
    *,
    source: Path,
    ssid: str,
    config: LabConfig,
    bssid: str | None = None,
    channel: int | None = None,
    ack_authorized: bool = False,
) -> CaptureResult:
    """Import an existing capture file (useful on macOS or external tools)."""
    assert_authorized(ssid, bssid, config, ack=ack_authorized)

    if not source.exists():
        raise CaptureError(f"File not found: {source}")

    vault = Vault()
    run_id, run_dir = vault.create_run_dir()
    dest = run_dir / "capture.pcapng"
    shutil.copy2(source, dest)

    if not validate_eapol(dest):
        raise CaptureError("Imported file has no detectable EAPOL handshake.")

    target = config.find_target(ssid, bssid)
    record = RunRecord(
        id=run_id,
        created_at=datetime.now(UTC).isoformat(),
        operator=config.operator,
        ssid=ssid,
        bssid=bssid,
        channel=channel,
        adapter=None,
        capture_path=str(dest),
        hash_path=None,
        status="captured",
        authorized_by=target.authorization_ref if target else None,
        platform=plat.platform_label(),
        capture_sha256=sha256_file(dest),
    )
    vault.insert_run(record)
    vault.write_meta(
        run_dir,
        {"run_id": run_id, "ssid": ssid, "source": str(source), "imported": True},
    )
    return CaptureResult(
        run_id=run_id,
        run_dir=run_dir,
        capture_path=dest,
        ssid=ssid,
        bssid=bssid,
        channel=channel,
    )


def _mac_hcx_viable(iface: str) -> bool:
    return which("hcxdumptool") is not None


def _capture_hcxdumptool(
    *,
    iface: str,
    output: Path,
    bssid: str | None,
    channel: int,
    duration: int,
) -> None:
    restored = False
    if plat.is_linux():
        if not linux_supports_monitor(iface):
            raise CaptureError(f"Interface {iface} does not support monitor mode.")
        set_linux_monitor_mode(iface, enable=True)

    filter_file: Path | None = None
    argv = ["hcxdumptool", "-i", iface, "-o", str(output), "-c", str(channel), "--enable_status=1"]
    if bssid:
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
            f.write(bssid.replace(":", "").lower() + "\n")
            filter_file = Path(f.name)
        argv.extend(["--filterlist_ap", str(filter_file)])

    try:
        result = run(argv, timeout=duration + 15)
        if not result.ok:
            raise CaptureError(f"hcxdumptool failed: {result.stderr or result.stdout}")
    finally:
        if filter_file and filter_file.exists():
            filter_file.unlink()
        if plat.is_linux():
            set_linux_monitor_mode(iface, enable=False)
            restored = True

    if not restored and plat.is_linux():
        set_linux_monitor_mode(iface, enable=False)


def _capture_macos_airport(*, iface: str, channel: int, duration: int, run_dir: Path) -> Path:
    airport = airport_path()
    if not airport:
        raise CaptureError("macOS airport utility not found.")

    # airport sniff writes to /tmp/airport*.cap
    before = set(Path("/tmp").glob("airport*.cap"))
    proc_argv = [str(airport), iface, "sniff", str(channel)]
    result = run(proc_argv, timeout=duration + 5)
    after = set(Path("/tmp").glob("airport*.cap"))
    new_files = after - before

    if new_files:
        newest = max(new_files, key=lambda p: p.stat().st_mtime)
        dest = run_dir / "capture.cap"
        shutil.copy2(newest, dest)
        return dest

    if result.stderr or result.stdout:
        # airport may still create files on interrupt
        caps = sorted(Path("/tmp").glob("airport*.cap"), key=lambda p: p.stat().st_mtime)
        if caps:
            dest = run_dir / "capture.cap"
            shutil.copy2(caps[-1], dest)
            return dest

    raise CaptureError(
        "macOS airport sniff produced no capture. "
        "Try: sudo airport en0 sniff <channel> (or use hcxdumptool with USB adapter)."
    )


def _ensure_pcapng(cap_path: Path, run_dir: Path) -> Path:
    if cap_path.suffix == ".pcapng":
        return cap_path

    pcapng = run_dir / "capture.pcapng"
    # hcxpcapngtool can read .cap; copy and rename if needed, or convert via tshark
    tshark = which("tshark")
    if tshark:
        result = run(
            [
                tshark,
                "-r",
                str(cap_path),
                "-F",
                "pcapng",
                "-w",
                str(pcapng),
            ],
            timeout=120,
        )
        if result.ok and pcapng.exists():
            return pcapng

    shutil.copy2(cap_path, pcapng)
    return pcapng
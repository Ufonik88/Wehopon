"""WiFi handshake capture — built-in passive sniffer, no network join required."""

from __future__ import annotations

import shutil
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from handshakelab.config import LabConfig
from handshakelab.eapol import CaptureAnalysis, has_eapol_handshake
from handshakelab.legal import assert_authorized
from handshakelab.sniffer import SnifferError, passive_capture
from handshakelab.util import platform as plat
from handshakelab.util.proc import run, which
from handshakelab.util.wifi import has_root, scan_networks
from handshakelab.vault import RunRecord, Vault, sha256_file

CaptureTickFn = Callable[[CaptureAnalysis, str], None]


class CaptureError(Exception):
    pass


def _tool_versions() -> dict[str, str]:
    """Return installed tool versions for audit storage in meta.json."""
    versions: dict[str, str] = {}
    for name in ("hashcat", "hcxdumptool", "hcxpcapngtool", "tcpdump", "tshark"):
        path = which(name)
        if not path:
            continue
        flag = "-V" if name == "hashcat" else "-v"
        result = run([path, flag], check=False)
        line = (result.stdout or result.stderr or "").strip().splitlines()
        versions[name] = line[0] if line else path
    return versions


@dataclass
class CaptureResult:
    run_id: str
    run_dir: Path
    capture_path: Path
    ssid: str
    bssid: str | None
    channel: int | None
    backend: str
    analysis: CaptureAnalysis


def capture_handshake(
    *,
    iface: str,
    ssid: str,
    config: LabConfig,
    bssid: str | None = None,
    channel: int | None = None,
    duration_sec: int | None = None,
    ack_authorized: bool = False,
    on_tick: CaptureTickFn | None = None,
) -> CaptureResult:
    """
    Passively capture WPA handshake. You do NOT need the WiFi password.
    You do NOT join the network. We sniff the air while any client connects.
    """
    if not has_root():
        raise CaptureError("Capture requires root. Run: sudo handshakelab ui")

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
            f"Could not determine channel for '{ssid}'. Run Scan first or set channel manually."
        )

    vault = Vault()
    run_id, run_dir = vault.create_run_dir()
    capture_path = run_dir / "capture.pcapng"

    try:
        sniff = passive_capture(
            iface=iface,
            output=capture_path,
            bssid=bssid,
            channel=channel,
            duration_sec=duration,
            on_tick=on_tick,
        )
    except SnifferError as exc:
        raise CaptureError(str(exc)) from exc

    if not sniff.capture_path.exists() or sniff.capture_path.stat().st_size == 0:
        raise CaptureError(
            "Empty capture. While we listen, another device must connect to the target AP "
            "(phone, laptop, smart TV). You do not connect yourself."
        )

    if not has_eapol_handshake(sniff.capture_path):
        raise CaptureError(
            f"Captured {sniff.analysis.total_packets} packets but no WPA handshake yet. "
            f"Leave a phone/laptop connecting to '{ssid}' and retry with longer duration, "
            "or wait until you see a device join that network."
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
        capture_path=str(sniff.capture_path),
        hash_path=None,
        status="captured",
        authorized_by=target.authorization_ref if target else None,
        platform=plat.platform_label(),
        capture_sha256=sha256_file(sniff.capture_path),
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
            "capture_backend": sniff.backend,
            "packets": sniff.analysis.total_packets,
            "eapol_frames": sniff.analysis.eapol_frames,
            "tool_versions": _tool_versions(),
        },
    )
    return CaptureResult(
        run_id=run_id,
        run_dir=run_dir,
        capture_path=sniff.capture_path,
        ssid=ssid,
        bssid=bssid,
        channel=channel,
        backend=sniff.backend,
        analysis=sniff.analysis,
    )


def import_capture(
    *,
    source: Path,
    ssid: str,
    config: LabConfig,
    iface: str | None = None,
    bssid: str | None = None,
    channel: int | None = None,
    ack_authorized: bool = False,
) -> CaptureResult:
    """Import an existing capture file."""
    assert_authorized(ssid, bssid, config, ack=ack_authorized)

    if not source.exists():
        raise CaptureError(f"File not found: {source}")

    vault = Vault()
    run_id, run_dir = vault.create_run_dir()
    dest = run_dir / "capture.pcapng"
    shutil.copy2(source, dest)

    if not has_eapol_handshake(dest):
        raise CaptureError("Imported file has no detectable EAPOL handshake.")

    from handshakelab.eapol import analyze_capture

    analysis = analyze_capture(dest)
    target = config.find_target(ssid, bssid)
    record = RunRecord(
        id=run_id,
        created_at=datetime.now(UTC).isoformat(),
        operator=config.operator,
        ssid=ssid,
        bssid=bssid,
        channel=channel,
        adapter=iface,
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
        backend="import",
        analysis=analysis,
    )

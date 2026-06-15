"""Built-in passive WiFi sniffer (Wireshark-style capture, no joining the network)."""

from __future__ import annotations

import signal
import subprocess
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from handshakelab.eapol import CaptureAnalysis, analyze_capture
from handshakelab.util import platform as plat
from handshakelab.util.proc import run, which
from handshakelab.util.wifi import (
    airport_path,
    linux_supports_monitor,
    set_linux_monitor_mode,
)

CaptureTickFn = Callable[[CaptureAnalysis, str], None]


@dataclass
class SnifferResult:
    capture_path: Path
    backend: str
    analysis: CaptureAnalysis
    duration_sec: int


class SnifferError(Exception):
    pass


def passive_capture(
    *,
    iface: str,
    output: Path,
    bssid: str | None,
    channel: int,
    duration_sec: int = 300,
    on_tick: CaptureTickFn | None = None,
) -> SnifferResult:
    """
    Passively sniff for WPA handshakes. You do NOT connect to the WiFi network.
    Captures EAPOL when any client authenticates to the target AP.
    """
    output.parent.mkdir(parents=True, exist_ok=True)
    backends = _available_backends()
    if not backends:
        raise SnifferError(
            "No capture engine found. Install tcpdump (recommended) or hcxtools: "
            "sudo apt install tcpdump hcxdumptool   /   brew install tcpdump hcxtools"
        )

    errors: list[str] = []
    for name in backends:
        try:
            if name == "hcxdumptool":
                result = _sniff_hcxdumptool(
                    iface, output, bssid, channel, duration_sec, on_tick
                )
            elif name == "tcpdump":
                result = _sniff_tcpdump(
                    iface, output, bssid, channel, duration_sec, on_tick
                )
            elif name == "airport":
                result = _sniff_airport(iface, output, channel, duration_sec, on_tick)
            else:
                continue
            if result.analysis.has_handshake or result.analysis.total_packets > 0:
                return result
            errors.append(f"{name}: capture empty")
        except SnifferError as exc:
            errors.append(f"{name}: {exc}")

    raise SnifferError(
        "Passive capture failed. " + "; ".join(errors) + ". "
        "Tip: another device (phone/TV/camera) must connect to the target AP while we listen. "
        "You never need to join the network yourself."
    )


def _available_backends() -> list[str]:
    """Return backends in documented preference order: tcpdump first.

    tcpdump ships with virtually every Linux distro and macOS, so it is the
    safest primary. hcxdumptool is preferred when PMKID is desired and the
    adapter supports it. macOS airport is the last-resort channel-bound sniffer.
    """
    order: list[str] = []
    if which("tcpdump"):
        order.append("tcpdump")
    if which("hcxdumptool"):
        order.append("hcxdumptool")
    if plat.is_macos() and airport_path():
        order.append("airport")
    return order


def _sniff_tcpdump(
    iface: str,
    output: Path,
    bssid: str | None,
    channel: int,
    duration_sec: int,
    on_tick: CaptureTickFn | None,
) -> SnifferResult:
    tcpdump = which("tcpdump")
    if not tcpdump:
        raise SnifferError("tcpdump not found")

    mon_iface = iface
    restored = False
    if plat.is_linux():
        if not linux_supports_monitor(iface):
            raise SnifferError(
                f"{iface} has no monitor mode. Use a USB WiFi adapter (see docs/HARDWARE.md)."
            )
        set_linux_monitor_mode(iface, enable=True)
        restored = True
        mon_iface = iface

    if plat.is_linux() and which("iw"):
        run(["iw", "dev", iface, "set", "channel", str(channel)], check=False)

    # Capture EAPOL + WiFi data; filter by BSSID when known
    bpf = "ether proto 0x888e or wlan type data"
    if bssid:
        bpf = f"(wlan addr1 {bssid} or wlan addr2 {bssid} or wlan addr3 {bssid}) and (ether proto 0x888e or wlan type data)"

    argv = [tcpdump, "-i", mon_iface, "-w", str(output), "-U", bpf]

    proc = subprocess.Popen(
        argv,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    start = time.monotonic()
    try:
        while time.monotonic() - start < duration_sec:
            time.sleep(2)
            analysis = analyze_capture(output)
            msg = (
                f"Listening passively… {analysis.total_packets} packets, "
                f"{analysis.eapol_frames} EAPOL frame(s)"
            )
            if on_tick:
                on_tick(analysis, msg)
            if analysis.has_handshake and analysis.eapol_frames >= 2:
                break
        else:
            analysis = analyze_capture(output)
    finally:
        proc.send_signal(signal.SIGINT)
        try:
            proc.wait(timeout=8)
        except subprocess.TimeoutExpired:
            proc.kill()
        if restored:
            set_linux_monitor_mode(iface, enable=False)

    analysis = analyze_capture(output)
    if not analysis.has_handshake and analysis.total_packets == 0:
        raise SnifferError("tcpdump captured no packets — check adapter and channel")

    return SnifferResult(
        capture_path=output,
        backend="tcpdump",
        analysis=analysis,
        duration_sec=int(time.monotonic() - start),
    )


def _sniff_hcxdumptool(
    iface: str,
    output: Path,
    bssid: str | None,
    channel: int,
    duration_sec: int,
    on_tick: CaptureTickFn | None,
) -> SnifferResult:
    import tempfile

    hcx = which("hcxdumptool")
    if not hcx:
        raise SnifferError("hcxdumptool not found")

    restored = False
    if plat.is_linux():
        if linux_supports_monitor(iface):
            set_linux_monitor_mode(iface, enable=True)
            restored = True

    filter_file: Path | None = None
    argv = [hcx, "-i", iface, "-o", str(output), "-c", str(channel), "--enable_status=1"]
    if bssid:
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
            f.write(bssid.replace(":", "").lower() + "\n")
            filter_file = Path(f.name)
        argv.extend(["--filterlist_ap", str(filter_file)])

    proc = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    start = time.monotonic()
    try:
        while time.monotonic() - start < duration_sec:
            time.sleep(2)
            analysis = analyze_capture(output)
            if on_tick:
                on_tick(
                    analysis,
                    f"hcxdumptool listening… {analysis.eapol_frames} EAPOL, {analysis.file_bytes // 1024} KB",
                )
            if analysis.has_handshake:
                break
    finally:
        proc.send_signal(signal.SIGINT)
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
        if filter_file and filter_file.exists():
            filter_file.unlink()
        if restored:
            set_linux_monitor_mode(iface, enable=False)

    analysis = analyze_capture(output)
    return SnifferResult(
        capture_path=output,
        backend="hcxdumptool",
        analysis=analysis,
        duration_sec=int(time.monotonic() - start),
    )


def _sniff_airport(
    iface: str,
    output: Path,
    channel: int,
    duration_sec: int,
    on_tick: CaptureTickFn | None,
) -> SnifferResult:
    airport = airport_path()
    if not airport:
        raise SnifferError("airport utility not found")

    cap_out = output.parent / "capture_raw.cap"
    proc = subprocess.Popen(
        [str(airport), iface, "sniff", str(channel)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    start = time.monotonic()
    try:
        while time.monotonic() - start < duration_sec:
            time.sleep(2)
            caps = sorted(Path("/tmp").glob("airport*.cap"), key=lambda p: p.stat().st_mtime)
            if caps:
                latest = caps[-1]
                latest.read_bytes()  # touch
                if on_tick:
                    on_tick(
                        CaptureAnalysis(1, 0, 0, 0, False, latest.stat().st_size),
                        f"airport sniffing ch {channel}… {latest.stat().st_size // 1024} KB",
                    )
    finally:
        proc.send_signal(signal.SIGINT)
        try:
            proc.wait(timeout=8)
        except subprocess.TimeoutExpired:
            proc.kill()

    caps = sorted(Path("/tmp").glob("airport*.cap"), key=lambda p: p.stat().st_mtime)
    if caps:
        cap_out.write_bytes(caps[-1].read_bytes())

    tshark = which("tshark")
    if tshark and cap_out.exists():
        run([tshark, "-r", str(cap_out), "-F", "pcapng", "-w", str(output)], timeout=120)
    elif cap_out.exists():
        output.write_bytes(cap_out.read_bytes())
    else:
        raise SnifferError("airport sniff produced no file")

    analysis = analyze_capture(output)
    return SnifferResult(
        capture_path=output,
        backend="airport",
        analysis=analysis,
        duration_sec=int(time.monotonic() - start),
    )
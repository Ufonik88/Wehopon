"""Built-in EAPOL / handshake detection — no Wireshark GUI required."""

from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path

from handshakelab.util.proc import run, which

EAPOL_ETHERTYPE = 0x888E


@dataclass
class CaptureAnalysis:
    total_packets: int
    eapol_frames: int
    data_frames: int
    beacon_frames: int
    has_handshake: bool
    file_bytes: int


def analyze_capture(path: Path) -> CaptureAnalysis:
    """Analyze a pcap/pcapng using built-in parser with tcpdump/tshark fallback."""
    if not path.exists():
        return CaptureAnalysis(0, 0, 0, 0, False, 0)

    size = path.stat().st_size
    if size == 0:
        return CaptureAnalysis(0, 0, 0, 0, False, 0)

    tcpdump = which("tcpdump")
    if tcpdump:
        return _analyze_tcpdump(path, tcpdump, size)

    tshark = which("tshark")
    if tshark:
        return _analyze_tshark(path, tshark, size)

    return _analyze_pcap_builtin(path, size)


def _analyze_tcpdump(path: Path, tcpdump: str, size: int) -> CaptureAnalysis:
    total_r = run([tcpdump, "-r", str(path), "-n"], timeout=120)
    total = max(0, len([ln for ln in total_r.stdout.splitlines() if ln.strip()]) - 1)

    eapol_r = run(
        [tcpdump, "-r", str(path), "-n", "ether proto 0x888e"],
        timeout=60,
    )
    eapol = max(0, len([ln for ln in eapol_r.stdout.splitlines() if "EAPOL" in ln or "0x888e" in ln.lower()]))

    if eapol == 0:
        eapol_r2 = run(
            [tcpdump, "-r", str(path), "-n", "-c", "50", "wlan type data"],
            timeout=60,
        )
        eapol = 1 if "EAPOL" in (eapol_r2.stdout + eapol_r2.stderr) else 0

    return CaptureAnalysis(
        total_packets=total,
        eapol_frames=eapol,
        data_frames=0,
        beacon_frames=0,
        has_handshake=eapol >= 1,
        file_bytes=size,
    )


def _analyze_tshark(path: Path, tshark: str, size: int) -> CaptureAnalysis:
    total_r = run([tshark, "-r", str(path), "-q", "-z", "io,stat,0"], timeout=60)
    eapol_r = run(
        [tshark, "-r", str(path), "-Y", "eapol", "-T", "fields", "-e", "frame.number"],
        timeout=60,
    )
    eapol_lines = [ln for ln in eapol_r.stdout.splitlines() if ln.strip()]
    total = 0
    for line in total_r.stderr.splitlines():
        if "Frames" in line or "frames" in line:
            parts = line.split()
            for p in parts:
                if p.isdigit():
                    total = int(p)
                    break
    return CaptureAnalysis(
        total_packets=total or len(eapol_lines),
        eapol_frames=len(eapol_lines),
        data_frames=0,
        beacon_frames=0,
        has_handshake=len(eapol_lines) >= 1,
        file_bytes=size,
    )


def _analyze_pcap_builtin(path: Path, size: int) -> CaptureAnalysis:
    """Minimal classic pcap parser looking for EAPOL ethertype."""
    try:
        data = path.read_bytes()
    except OSError:
        return CaptureAnalysis(0, 0, 0, 0, False, size)

    if len(data) < 24:
        return CaptureAnalysis(0, 0, 0, 0, False, size)

    magic = data[:4]
    if magic == b"\xd4\xc3\xb2\xa1":
        endian = "<"
    elif magic == b"\xa1\xb2\xc3\xd4":
        endian = ">"
    else:
        # pcapng — use hcxpcapngtool or size heuristic
        hcx = which("hcxpcapngtool")
        if hcx:
            tmp = path.parent / ".eapol_probe.22000"
            try:
                result = run([hcx, "-o", str(tmp), str(path)], timeout=90)
                if result.ok and tmp.exists():
                    lines = [ln for ln in tmp.read_text(errors="ignore").splitlines() if ln.strip()]
                    if lines:
                        return CaptureAnalysis(max(1, len(lines)), len(lines), 0, 0, True, size)
            finally:
                if tmp.exists():
                    tmp.unlink()
        return CaptureAnalysis(1, 0, 0, 0, size > 512, size)

    offset = 24
    total = 0
    eapol = 0
    hdr_fmt = endian + "IIII"

    while offset + 16 <= len(data):
        try:
            _ts_sec, _ts_usec, incl_len, _orig_len = struct.unpack(
                hdr_fmt, data[offset : offset + 16]
            )
        except struct.error:
            break
        offset += 16
        frame = data[offset : offset + incl_len]
        offset += incl_len
        total += 1
        if _frame_has_eapol(frame):
            eapol += 1

    return CaptureAnalysis(
        total_packets=total,
        eapol_frames=eapol,
        data_frames=0,
        beacon_frames=0,
        has_handshake=eapol >= 1,
        file_bytes=size,
    )


def _frame_has_eapol(frame: bytes) -> bool:
    if len(frame) < 14:
        return False
    # Ethernet II
    ethertype = struct.unpack("!H", frame[12:14])[0]
    if ethertype == EAPOL_ETHERTYPE:
        return True
    # 802.11 monitor frames — scan for EAPOL ethertype in payload
    if EAPOL_ETHERTYPE.to_bytes(2, "big") in frame:
        return True
    if b"\x88\x8e" in frame:
        return True
    return False


def has_eapol_handshake(path: Path) -> bool:
    return analyze_capture(path).has_handshake
"""WiFi interface helpers for Linux and macOS."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from handshakelab.util import platform as plat
from handshakelab.util.platform import is_builtin_wifi
from handshakelab.util.proc import CommandResult, run, which


MAC_AIRPORT = (
    "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport"
)


__all__ = [
    "Network",
    "airport_path",
    "list_interfaces",
    "interface_exists",
    "has_root",
    "tool_paths",
    "linux_supports_monitor",
    "set_linux_monitor_mode",
    "scan_networks",
    "is_builtin_wifi",
    "validate_eapol",
]


@dataclass
class Network:
    ssid: str
    bssid: str | None
    channel: int | None
    rssi: int | None
    security: str


def airport_path() -> Path | None:
    path = Path(MAC_AIRPORT)
    return path if path.exists() else None


def list_interfaces() -> list[str]:
    if plat.is_linux():
        net = Path("/sys/class/net")
        return sorted(p.name for p in net.iterdir() if p.is_dir() and p.name != "lo")
    if plat.is_macos():
        result = run(["ifconfig", "-l"])
        if result.ok:
            return [i for i in result.stdout.split() if i != "lo"]
    return []


def interface_exists(iface: str) -> bool:
    if plat.is_linux():
        return Path(f"/sys/class/net/{iface}").exists()
    if plat.is_macos():
        result = run(["ifconfig", iface])
        return result.ok and ("inet " in result.stdout or "status:" in result.stdout)
    return False


def has_root() -> bool:
    import os

    return os.geteuid() == 0


def tool_paths() -> dict[str, str | None]:
    tools = {
        "hcxdumptool": which("hcxdumptool"),
        "hcxpcapngtool": which("hcxpcapngtool"),
        "hashcat": which("hashcat"),
        "tshark": which("tshark"),
        "iw": which("iw"),
        "airport": str(airport_path()) if airport_path() else None,
    }
    return tools


def linux_supports_monitor(iface: str) -> bool:
    if not which("iw"):
        return False
    # Find phy for interface
    link = run(["iw", "dev", iface, "info"])
    if not link.ok:
        return False
    match = re.search(r"wiphy (\d+)", link.stdout)
    if not match:
        return False
    phy = run(["iw", "phy", f"phy{match.group(1)}", "info"])
    return phy.ok and "monitor" in phy.stdout


def set_linux_monitor_mode(iface: str, *, enable: bool) -> CommandResult:
    mode = "monitor" if enable else "managed"
    steps = [
        ["ip", "link", "set", iface, "down"],
        ["iw", "dev", iface, "set", "type", mode],
        ["ip", "link", "set", iface, "up"],
    ]
    last: CommandResult | None = None
    for argv in steps:
        last = run(argv, check=False)
        if not last.ok:
            return last
    return last  # type: ignore[return-value]


def scan_networks(iface: str) -> list[Network]:
    if plat.is_linux():
        return _scan_linux(iface)
    if plat.is_macos():
        return _scan_macos(iface)
    return []


def _scan_linux(iface: str) -> list[Network]:
    # Prefer iw when available
    if which("iw"):
        run(["ip", "link", "set", iface, "up"], check=False)
        result = run(["iw", "dev", iface, "scan"], timeout=30)
        if result.ok:
            return _parse_iw_scan(result.stdout)

    # Fallback nmcli
    if which("nmcli"):
        result = run(
            [
                "nmcli",
                "-f",
                "SSID,BSSID,CHAN,SIGNAL,SECURITY",
                "dev",
                "wifi",
                "list",
                "ifname",
                iface,
            ],
            timeout=30,
        )
        if result.ok:
            return _parse_nmcli_scan(result.stdout)

    return []


def _parse_iw_scan(text: str) -> list[Network]:
    networks: list[Network] = []
    blocks = text.split("BSS ")
    for block in blocks[1:]:
        bssid_m = re.match(r"([0-9a-f:]{17})", block, re.I)
        ssid_m = re.search(r"SSID: (.+)", block)
        freq_m = re.search(r"freq: (\d+)", block)
        signal_m = re.search(r"signal: ([-\d.]+)", block)
        if not bssid_m or not ssid_m:
            continue
        ssid = ssid_m.group(1).strip()
        if not ssid:
            continue
        channel = _freq_to_channel(int(freq_m.group(1))) if freq_m else None
        rssi = int(float(signal_m.group(1))) if signal_m else None
        networks.append(
            Network(
                ssid=ssid,
                bssid=bssid_m.group(1).upper(),
                channel=channel,
                rssi=rssi,
                security="unknown",
            )
        )
    return networks


def _parse_nmcli_scan(text: str) -> list[Network]:
    networks: list[Network] = []
    for line in text.splitlines()[1:]:
        parts = line.split()
        if len(parts) < 4:
            continue
        ssid = parts[0]
        if ssid == "--" or not ssid:
            continue
        bssid = parts[1].upper()
        try:
            channel = int(parts[2])
            rssi = int(parts[3])
        except ValueError:
            channel, rssi = None, None
        security = parts[4] if len(parts) > 4 else "unknown"
        networks.append(
            Network(ssid=ssid, bssid=bssid, channel=channel, rssi=rssi, security=security)
        )
    return networks


def _scan_macos(iface: str) -> list[Network]:
    airport = airport_path()
    if airport:
        result = run([str(airport), "-s"], timeout=30)
        if result.ok:
            return _parse_airport_scan(result.stdout)

    if which("system_profiler"):
        result = run(["system_profiler", "SPAirPortDataType"], timeout=60)
        if result.ok:
            return _parse_system_profiler(result.stdout)

    return []


def _parse_airport_scan(text: str) -> list[Network]:
    networks: list[Network] = []
    for line in text.splitlines()[1:]:
        if not line.strip():
            continue
        # SSID BSSID RSSI CHANNEL HT CC SECURITY (auth/unicast/group)
        parts = line.split()
        if len(parts) < 7:
            continue
        ssid = parts[0]
        bssid = parts[1].upper()
        try:
            rssi = int(parts[2])
            channel = int(parts[3])
        except ValueError:
            rssi, channel = None, None
        security = " ".join(parts[6:]) if len(parts) > 6 else "unknown"
        networks.append(
            Network(ssid=ssid, bssid=bssid, channel=channel, rssi=rssi, security=security)
        )
    return networks


def _parse_system_profiler(text: str) -> list[Network]:
    """Parse `system_profiler SPAirPortDataType` output.

    Modern macOS (14+) shows networks in two formats:
    1. Current Network Information:
            <SSID>:                ← indented, no colon-field
              PHY Mode: 802.11ax
              Channel: 44 (5GHz, 160MHz)
              ...
    2. Other Local Wi-Fi Networks:
            <SSID>:                ← indented, no colon-field
              Channel: 1 (2GHz, 20MHz)
              ...
              Security: WPA2 Personal
              Signal / Noise: -45 dBm / -92 dBm
              BSSID: aa:bb:cc:dd:ee:ff
              MCS Index: 6
    """
    networks: list[Network] = []
    current_ssid: str | None = None
    pending_ssid: str | None = None
    pending_channel: int | None = None
    pending_signal: int | None = None
    pending_security: str | None = None
    pending_bssid: str | None = None

    def _flush() -> None:
        """Commit a parsed record."""
        nonlocal pending_ssid, pending_channel, pending_signal, pending_security, pending_bssid
        # macOS 14+ system_profiler no longer exposes BSSID for nearby networks.
        # We still record the SSID + channel + signal — just with bssid=None.
        if pending_ssid:
            networks.append(
                Network(
                    ssid=pending_ssid,
                    bssid=pending_bssid,  # None on modern macOS
                    channel=pending_channel,
                    rssi=pending_signal,
                    security=pending_security or "unknown",
                )
            )
        pending_ssid = None
        pending_channel = None
        pending_signal = None
        pending_security = None
        pending_bssid = None

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()

        # Header style 1: explicit SSID: field (legacy)
        if stripped.startswith("SSID_STR:") or stripped.startswith("SSID:"):
            _flush()
            current_ssid = stripped.split(":", 1)[1].strip()
            pending_ssid = current_ssid
            continue

        # Header style 2: indented "<SSID>:" line in modern macOS
        # e.g. "            MyWiFi:" — ends with ":", no other colon, not a field
        # Must be a section header (not a key: value field)
        # Skip interface names like en0, en1, awdl0, llw0
        stripped_no_colon = stripped[:-1] if stripped.endswith(":") else stripped
        looks_like_interface = (
            # Has trailing digits (e.g. en0, awdl0) and short name
            (any(c.isdigit() for c in stripped_no_colon) and len(stripped_no_colon) <= 6)
            # Or matches known interface prefixes
            or any(
                stripped_no_colon.startswith(prefix)
                for prefix in ("en", "awdl", "llw", "utun", "bridge", "ap", "lo", "pd", "awdl0")
            )
        )
        if (
            line
            and line.endswith(":")
            and ":" not in line[:-1]  # only the trailing colon
            and stripped
            and not stripped.startswith(
                (
                    "Interfaces:",
                    "Software Versions:",
                    "Current ",
                    "Other ",
                    "Wi-Fi:",
                    "Other Local",
                )
            )
            and (line.startswith(" ") or line.startswith("\t"))
            and not looks_like_interface
        ):
            # This is a network name header; flush previous record and start new
            _flush()
            current_ssid = stripped_no_colon
            pending_ssid = current_ssid
            continue

        # Field lines
        if stripped.startswith("BSSID:"):
            bssid = stripped.split(":", 1)[1].strip().upper()
            if bssid and ":" in bssid:
                pending_bssid = bssid
        elif stripped.startswith("Channel:"):
            ch_text = stripped.split(":", 1)[1].strip()
            # Channel: 44 (5GHz, 160MHz) → 44
            ch = ch_text.split()[0]
            try:
                pending_channel = int(ch)
            except ValueError:
                pass
        elif stripped.startswith("Signal / Noise:") or stripped.startswith("RSSI:"):
            txt = stripped.split(":", 1)[1].strip()
            num = txt.split()[0]
            try:
                pending_signal = int(num)
            except ValueError:
                pass
        elif stripped.startswith("Security:"):
            pending_security = stripped.split(":", 1)[1].strip()

    _flush()
    return networks


def _freq_to_channel(freq_mhz: int) -> int | None:
    if 2412 <= freq_mhz <= 2484:
        return (freq_mhz - 2407) // 5
    if 5170 <= freq_mhz <= 5825:
        return (freq_mhz - 5000) // 5
    return None


def validate_eapol(capture_path: Path) -> bool:
    from handshakelab.eapol import has_eapol_handshake

    return has_eapol_handshake(capture_path)

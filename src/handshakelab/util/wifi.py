"""WiFi interface helpers for Linux and macOS."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from handshakelab.util import platform as plat
from handshakelab.util.proc import CommandResult, run, which


MAC_AIRPORT = (
    "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport"
)


@dataclass
class Network:
    ssid: str
    bssid: str
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
            ["nmcli", "-f", "SSID,BSSID,CHAN,SIGNAL,SECURITY", "dev", "wifi", "list", "ifname", iface],
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
    networks: list[Network] = []
    current_ssid = None
    for line in text.splitlines():
        if "SSID_STR:" in line or "SSID:" in line:
            current_ssid = line.split(":", 1)[1].strip()
        if "BSSID:" in line and current_ssid:
            bssid = line.split(":", 1)[1].strip().upper()
            networks.append(
                Network(
                    ssid=current_ssid,
                    bssid=bssid,
                    channel=None,
                    rssi=None,
                    security="unknown",
                )
            )
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
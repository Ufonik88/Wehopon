"""Preflight checks for toolchain, privileges, and adapter."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from handshakelab.config import load_config
from handshakelab.util import platform as plat
from handshakelab.util.proc import run, which
from handshakelab.util.wifi import (
    airport_path,
    has_root,
    interface_exists,
    is_builtin_wifi,
    linux_supports_monitor,
    tool_paths,
)


@dataclass
class Check:
    name: str
    ok: bool
    detail: str


def run_doctor(
    *,
    iface: str | None = None,
    config_path: Path | None = None,
) -> tuple[list[Check], bool]:
    config = load_config(config_path)
    iface = iface or config.capture.default_adapter
    checks: list[Check] = []

    checks.append(
        Check(
            "platform",
            plat.is_supported(),
            plat.platform_label() if plat.is_supported() else f"Unsupported: {plat.system()}",
        )
    )

    tools = tool_paths()
    for name in ("hcxpcapngtool", "hashcat"):
        path = tools.get(name)
        checks.append(Check(name, bool(path), path or "not found in PATH"))

    tcpdump = which("tcpdump")
    if tcpdump:
        checks.append(Check("tcpdump", True, f"{tcpdump} (built-in sniffer)"))

    capture_ok = bool(tools.get("hcxdumptool") or tcpdump)
    capture_parts: list[str] = [
        f"tcpdump={tcpdump or 'n/a'}",
        f"hcxdumptool={tools.get('hcxdumptool') or 'n/a'}",
    ]
    if plat.is_macos():
        airport = airport_path()
        if plat.is_modern_macos(14) and airport is None:
            capture_parts.append("airport=removed (macOS 14+ has no CLI; use USB adapter)")
        else:
            capture_parts.append(f"airport={airport or 'n/a'}")
    capture_detail = ", ".join(capture_parts)

    # On macOS, tcpdump-on-en0 alone is not enough for raw 802.11 EAPOL capture.
    # Flag this so users know they need hcxdumptool + a USB adapter.
    capture_ok_for_handshake = bool(tcpdump) and not (
        plat.is_macos() and not tools.get("hcxdumptool")
    )
    checks.append(
        Check(
            "capture_backend",
            capture_ok_for_handshake,
            capture_detail
            + (
                " | macOS: install hcxdumptool for monitor-mode capture (see docs/HARDWARE.md)"
                if plat.is_macos() and not tools.get("hcxdumptool")
                else ""
            )
            if capture_ok
            else "install tcpdump",
        )
    )

    if tools.get("tshark"):
        checks.append(Check("tshark", True, tools["tshark"] or ""))
    else:
        checks.append(
            Check(
                "tshark",
                True,
                "optional — not found; EAPOL check falls back to hcxpcapngtool",
            )
        )

    if iface:
        exists = interface_exists(iface)
        checks.append(Check(f"interface:{iface}", exists, "present" if exists else "not found"))

        if exists and plat.is_linux():
            mon = linux_supports_monitor(iface)
            checks.append(
                Check(
                    f"monitor_mode:{iface}",
                    mon,
                    "supported" if mon else "not supported — need USB adapter with monitor mode",
                )
            )
        elif exists and plat.is_macos():
            if is_builtin_wifi(iface):
                # Apple kernel restriction on Broadcom built-in WiFi
                builtin = "Built-in macOS WiFi (Broadcom) cannot do monitor mode — kernel-level Apple restriction. Captures only frames to/from this Mac's MAC. Use a USB adapter (Alfa AWUS036ACH) for real handshake capture."
            elif plat.is_modern_macos(14):
                builtin = "macOS built-in WiFi cannot do raw 802.11 monitor frames. Use a USB adapter + hcxdumptool for handshake capture."
            else:
                builtin = (
                    "macOS: built-in WiFi uses airport sniff; external USB + hcxdumptool for PMKID"
                )
            checks.append(Check(f"monitor_mode:{iface}", False, builtin))

    checks.append(
        Check(
            "root_privilege",
            has_root(),
            "running as root" if has_root() else "not root — capture requires sudo",
        )
    )

    if config.path.exists():
        checks.append(
            Check("lab.toml", True, f"loaded ({len(config.allowed_targets)} allowed target(s))")
        )
    else:
        checks.append(
            Check(
                "lab.toml",
                False,
                "missing — copy lab.toml.example to lab.toml for authorized capture",
            )
        )

    for name, path in tools.items():
        if path and name in ("hashcat", "hcxpcapngtool", "hcxdumptool"):
            ver = run([path, "-V" if name == "hashcat" else "-v"], check=False)
            if ver.ok or ver.stderr:
                version_line = (ver.stdout or ver.stderr).splitlines()[0][:80]
                checks.append(Check(f"{name}_version", True, version_line))

    all_ok = all(c.ok for c in checks if c.name not in ("root_privilege", "lab.toml", "tshark"))
    return checks, all_ok

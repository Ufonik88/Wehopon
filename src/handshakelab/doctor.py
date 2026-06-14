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
    capture_detail = ", ".join(
        x
        for x in [
            f"tcpdump={tcpdump or 'n/a'}",
            f"hcxdumptool={tools.get('hcxdumptool') or 'n/a'}",
            f"airport={airport_path() or 'n/a'}" if plat.is_macos() else None,
        ]
        if x
    )
    checks.append(Check("capture_backend", capture_ok, capture_detail or "install tcpdump"))

    if tools.get("tshark"):
        checks.append(Check("tshark", True, tools["tshark"]))
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
            checks.append(
                Check(
                    f"monitor_mode:{iface}",
                    True,
                    "macOS: built-in WiFi uses airport sniff; external USB + hcxdumptool for PMKID",
                )
            )

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
"""lab.toml configuration loader."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class AllowedTarget:
    ssid: str
    bssid: str | None = None
    owner: str = ""
    authorization_ref: str = ""


@dataclass
class CaptureConfig:
    default_adapter: str = "wlan0"
    default_duration_sec: int = 300
    deauth_enabled: bool = False


@dataclass
class UiConfig:
    trust_operator_ack: bool = True
    default_port: int = 8765


@dataclass
class CrackConfig:
    hashcat_bin: str = "hashcat"
    wordlist: str = ""
    workload_profile: int = 2


@dataclass
class LabConfig:
    path: Path
    name: str = "Lab"
    operator: str = ""
    require_authorization: bool = True
    allowed_targets: list[AllowedTarget] = field(default_factory=list)
    capture: CaptureConfig = field(default_factory=CaptureConfig)
    crack: CrackConfig = field(default_factory=CrackConfig)
    ui: UiConfig = field(default_factory=UiConfig)

    def find_target(self, ssid: str, bssid: str | None = None) -> AllowedTarget | None:
        ssid_lower = ssid.lower()
        bssid_norm = _norm_bssid(bssid) if bssid else None
        for target in self.allowed_targets:
            if target.ssid.lower() != ssid_lower:
                continue
            if bssid_norm and target.bssid:
                if _norm_bssid(target.bssid) != bssid_norm:
                    continue
            return target
        return None


def _norm_bssid(bssid: str) -> str:
    return bssid.replace("-", ":").upper()


def load_config(path: Path | None) -> LabConfig:
    if path is None:
        path = Path("lab.toml")
    if not path.exists():
        return LabConfig(path=path, require_authorization=False)

    raw = tomllib.loads(path.read_text())
    lab = raw.get("lab", {})
    capture_raw = raw.get("capture", {})
    crack_raw = raw.get("crack", {})
    ui_raw = raw.get("ui", {})

    targets: list[AllowedTarget] = []
    for entry in raw.get("allowed_targets", []):
        targets.append(
            AllowedTarget(
                ssid=entry["ssid"],
                bssid=entry.get("bssid"),
                owner=entry.get("owner", ""),
                authorization_ref=entry.get("authorization_ref", ""),
            )
        )

    return LabConfig(
        path=path,
        name=lab.get("name", "Lab"),
        operator=lab.get("operator", ""),
        require_authorization=lab.get("require_authorization", True),
        allowed_targets=targets,
        capture=CaptureConfig(
            default_adapter=capture_raw.get("default_adapter", "wlan0"),
            default_duration_sec=int(capture_raw.get("default_duration_sec", 120)),
            deauth_enabled=bool(capture_raw.get("deauth_enabled", False)),
        ),
        crack=CrackConfig(
            hashcat_bin=crack_raw.get("hashcat_bin", "hashcat"),
            wordlist=crack_raw.get("wordlist", ""),
            workload_profile=int(crack_raw.get("workload_profile", 2)),
        ),
        ui=UiConfig(
            trust_operator_ack=bool(ui_raw.get("trust_operator_ack", True)),
            default_port=int(ui_raw.get("default_port", 8765)),
        ),
    )

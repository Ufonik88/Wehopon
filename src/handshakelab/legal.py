"""Authorization gate for capture and import operations."""

from __future__ import annotations

from handshakelab.config import LabConfig


class AuthorizationError(Exception):
    """Raised when a target is not authorized in lab.toml."""


def assert_authorized(
    ssid: str,
    bssid: str | None,
    config: LabConfig,
    *,
    ack: bool = False,
) -> None:
    if not config.require_authorization:
        return

    if not ack:
        raise AuthorizationError(
            "Capture/import requires --ack-authorized. "
            "Confirm you have permission to test this network. "
            "See docs/LEGAL_AND_ETHICS.md."
        )

    if not config.allowed_targets:
        raise AuthorizationError(
            f"No allowed_targets in {config.path}. "
            "Copy lab.toml.example to lab.toml and list authorized APs."
        )

    if config.find_target(ssid, bssid) is None:
        hint = f"SSID={ssid}"
        if bssid:
            hint += f", BSSID={bssid}"
        raise AuthorizationError(
            f"Target not in allow-list ({hint}). "
            f"Add it to {config.path} before capture."
        )
import pytest

from handshakelab.config import AllowedTarget, LabConfig
from handshakelab.legal import AuthorizationError, assert_authorized


def test_requires_ack():
    cfg = LabConfig(
        path=__import__("pathlib").Path("lab.toml"),
        require_authorization=True,
        allowed_targets=[AllowedTarget(ssid="LAB", bssid="AA:BB:CC:DD:EE:FF")],
    )
    with pytest.raises(AuthorizationError, match="ack-authorized"):
        assert_authorized("LAB", "AA:BB:CC:DD:EE:FF", cfg, ack=False)


def test_allow_list():
    cfg = LabConfig(
        path=__import__("pathlib").Path("lab.toml"),
        require_authorization=True,
        allowed_targets=[AllowedTarget(ssid="LAB")],
    )
    assert_authorized("LAB", None, cfg, ack=True)
    with pytest.raises(AuthorizationError):
        assert_authorized("OTHER", None, cfg, ack=True)
from pathlib import Path

from handshakelab.config import load_config


def test_load_config_example(tmp_path: Path):
    toml = tmp_path / "lab.toml"
    toml.write_text(
        """
[lab]
name = "Test Lab"
operator = "tester"
require_authorization = true

[[allowed_targets]]
ssid = "LAB-AP"
bssid = "AA:BB:CC:DD:EE:FF"
authorization_ref = "QA-1"

[capture]
default_adapter = "wlan1"
default_duration_sec = 60

[crack]
wordlist = "/tmp/words.txt"
"""
    )
    cfg = load_config(toml)
    assert cfg.name == "Test Lab"
    assert cfg.capture.default_adapter == "wlan1"
    assert cfg.find_target("LAB-AP", "AA:BB:CC:DD:EE:FF") is not None
    assert cfg.find_target("OTHER") is None


def test_missing_config():
    cfg = load_config(Path("/nonexistent/lab.toml"))
    assert cfg.require_authorization is False
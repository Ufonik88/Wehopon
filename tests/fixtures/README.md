# Test Fixtures

This directory contains test fixtures for HandshakeLab tests.

## Required Fixtures

To run the full test suite, create the following synthetic PCAP files:

### `handshake.pcapng`
A minimal pcapng file containing WPA2 EAPOL handshake frames.
Create with:
```bash
# Capture a real handshake (for testing only)
sudo tcpdump -i wlan0 -c 100 -w tests/fixtures/handshake.pcapng
```

### `empty.pcapng`
An empty or non-WiFi pcapng file for negative testing.
```bash
# Create minimal valid pcapng
echo "" > tests/fixtures/empty.pcapng
```

### `test_config.toml`
A test configuration file:
```toml
[lab]
name = "test-lab"

[capture]
default_duration_sec = 5

[vault]
path = "/tmp/handshakelab-test-vault"
```

## Notes

- Never commit real capture files with actual network data
- Use synthetic or sanitized data only
- Fixtures should be minimal but valid enough for testing

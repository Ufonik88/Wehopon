# HandshakeLab — Hardware Guide

## Minimum requirements

| Component | Requirement |
| --- | --- |
| Host OS | Linux (kernel 5.x+, your 6.17 bench is fine) |
| CPU | 4+ cores; cracking is CPU/GPU bound |
| RAM | 8 GB minimum; 16 GB for large wordlists |
| USB | USB 3.0 port for modern adapters |
| WiFi adapter | **Must support monitor mode** (see below) |
| Privileges | `sudo` for capture commands |

## Recommended USB adapters

Always verify on your kernel before buying. Community favorites:

| Adapter | Chipset | Monitor | Injection | Notes |
| --- | --- | --- | --- | --- |
| Alfa AWUS036ACH | RTL8812AU | Yes | Yes | 802.11ac; common lab choice |
| Alfa AWUS036NHA | AR9271 | Yes | Yes | 802.11n; very stable |
| TP-Link TL-WN722N v1 | AR9271 | Yes | Yes | Cheap; **v2/v3 often NOT compatible** |
| Panda PAU09 | Ralink RT5372 | Yes | Yes | Compact |

### Verify your adapter

```bash
# Plug in adapter, then:
iw list | grep -A5 "Supported interface modes"
# Must include: * monitor

# Check driver
lsusb
dmesg | tail -20
```

## Two-adapter setup (recommended)

Use **one adapter for capture** (monitor mode) and **another for internet/management** (managed mode). Sharing one radio between monitor + your SSH session is painful.

```
┌─────────────┐     wlan0 (built-in)  ──> internet / SSH
│ Linux bench │
└─────────────┘     wlan1 (USB Alfa)  ──> monitor capture only
```

## GPU acceleration (optional)

Hashcat benefits significantly from GPU:

| Vendor | Setup |
| --- | --- |
| NVIDIA | Install proprietary driver + OpenCL/CUDA runtime |
| AMD | ROCm or OpenCL |
| CPU only | Works; use smaller wordlists for smoke tests |

Check: `hashcat -I` should list your compute device.

## Lab AP setup

Dedicated test AP isolated from production:

- WPA2-PSK for v1 testing
- Configurable SSID per test case
- Known password rotation schedule
- No client devices except DUT + capture machine

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| `Operation not permitted` | Run with `sudo` |
| Adapter not found | `ip link`; check USB power |
| Monitor mode fails | Kill NetworkManager on iface: `nmcli dev set wlan1 managed no` |
| No handshake captured | Wait for client association; extend duration; confirm channel |
| Driver disconnects | Try powered USB hub; different USB port |

## Hardware-in-the-loop checklist

Before each release:

- [ ] `handshakelab doctor` green
- [ ] Passive scan lists lab SSID
- [ ] 120s capture produces non-empty pcapng
- [ ] Convert extracts ≥1 hash
- [ ] Crack succeeds with known password in wordlist
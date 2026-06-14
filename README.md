# HandshakeLab

**Offline WiFi handshake capture & crack for authorized product testing.**

> Capture once → save locally → crack offline → reveal password → manually join the device under test.  
> **Linux and macOS supported.**

**Repository:** [github.com/Ufonik88/Wehopon](https://github.com/Ufonik88/Wehopon)  
**Status:** v0.2.0 — Web UI + one-click auto-crack  
**Docs:** [`docs/USER_GUIDE.md`](docs/USER_GUIDE.md)

## One-click UI (recommended)

```bash
pip install -e .
sudo handshakelab ui    # needs sudo for capture; opens http://127.0.0.1:8765
```

1. Click **Scan** → pick an SSID  
2. Check **I am authorized…**  
3. Click **Start Auto-Crack** → password appears in plaintext  

Optional: set `HANDSHAKELAB_AI_API_KEY` for AI-assisted wordlist generation.

---

## Quick start

### Linux

```bash
sudo apt install hcxdumptool hcxtools hashcat iw wireshark-common
pip install -e .
cp lab.toml.example lab.toml   # add your authorized lab APs

sudo handshakelab doctor -i wlan1
sudo handshakelab capture -i wlan1 --ssid LAB-AP --channel 6 --ack-authorized
handshakelab convert latest
handshakelab crack latest --wordlist ./wordlists/qa.txt
handshakelab show latest --reveal
```

### macOS

```bash
brew install hcxtools hashcat wireshark
pip install -e .
cp lab.toml.example lab.toml

handshakelab doctor -i en0
# Option A: import a Wireshark capture
handshakelab import capture.pcapng --ssid LAB-AP --ack-authorized
# Option B: live capture (sudo)
sudo handshakelab capture -i en0 --ssid LAB-AP --channel 6 --ack-authorized

handshakelab convert latest
handshakelab crack latest --wordlist ./wordlists/qa.txt
handshakelab show latest --reveal
```

---

## Commands

| Command | Description |
| --- | --- |
| `doctor` | Preflight toolchain + adapter checks |
| `scan` | Passive WiFi scan |
| `capture` | Live handshake capture (sudo) |
| `import` | Import existing `.pcap` / `.pcapng` |
| `convert` | pcapng → Hashcat `.22000` |
| `crack` | Offline Hashcat (never hits the AP) |
| `show` | Display result (`--reveal` for plaintext) |
| `report` | QA report (md/json) |
| `list` | List vault runs |

---

## Documentation

| Doc | Description |
| --- | --- |
| [`docs/USER_GUIDE.md`](docs/USER_GUIDE.md) | Install & workflow (Linux + Mac) |
| [`docs/PROJECT_PLAN.md`](docs/PROJECT_PLAN.md) | Full project plan |
| [`docs/TECHNICAL_BLUEPRINT.md`](docs/TECHNICAL_BLUEPRINT.md) | Technical design |
| [`docs/LEGAL_AND_ETHICS.md`](docs/LEGAL_AND_ETHICS.md) | **Read before use** |
| [`MASTER_TODO.md`](MASTER_TODO.md) | Task ledger |

---

## Legal

**Authorized lab use only.** See [`docs/LEGAL_AND_ETHICS.md`](docs/LEGAL_AND_ETHICS.md).

## License

MIT
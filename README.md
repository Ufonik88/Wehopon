# HandshakeLab

**Offline WiFi handshake capture & crack for authorized product testing.**

> Capture once → save locally → crack offline → reveal password → manually join the device under test.  
> **Linux and macOS supported.**

**Repository:** [github.com/Ufonik88/Wehopon](https://github.com/Ufonik88/Wehopon)  
**Status:** v0.3.1 — Hardening, security, dev tooling
**Docs:** [`docs/USER_GUIDE.md`](docs/USER_GUIDE.md)

## One-click UI (recommended)

```bash
pip install -e .
sudo handshakelab ui    # needs sudo for capture; opens http://127.0.0.1:8765
```

1. Click **Scan** → pick an SSID (password unknown is fine)  
2. Check **I am authorized…**  
3. Click **Start Auto-Crack** → built-in sniffer captures handshake → crack → plaintext password  

**You never join the WiFi.** We passively sniff the air while any device connects to that AP.

Optional: set `HANDSHAKELAB_AI_API_KEY` for AI-assisted wordlist generation.

---

## Quick start

### Linux
```bash
sudo apt install tcpdump hcxdumptool hcxtools hashcat iw
make dev                      # creates .venv, pip install -e ".[dev]"
cp lab.toml.example lab.toml  # add your authorized lab APs

sudo handshakelab doctor -i wlan1
sudo handshakelab capture -i wlan1 --ssid LAB-AP --channel 6 --ack-authorized
handshakelab convert latest
handshakelab crack latest --wordlist ./wordlists/qa.txt
handshakelab show latest --reveal
```

### macOS
```bash
brew install tcpdump hcxtools hashcat
# hcxdumptool is NOT in Homebrew — build from source for monitor-mode capture:
#   git clone https://github.com/ZerBea/hcxdumptool && cd hcxdumptool && make && sudo make install
make dev                      # creates .venv, pip install -e ".[dev]"
cp lab.toml.example lab.toml

handshakelab doctor -i en0
# Note: macOS 14+ (Sonoma) removed the `airport` CLI. Built-in en0 cannot do
# raw 802.11 monitor frames. Use a USB adapter + hcxdumptool for capture.

# Option A: import a Wireshark capture
handshakelab import capture.pcapng --ssid LAB-AP --ack-authorized
# Option B: live capture with USB adapter (sudo)
sudo handshakelab capture -i en1 --ssid LAB-AP --channel 6 --ack-authorized

handshakelab convert latest
handshakelab crack latest --wordlist ./wordlists/qa.txt
handshakelab show latest --reveal
```

### Common install issues

| Problem | Fix |
| --- | --- |
| `pip install -e ".[dev]"` times out | `pip install -r requirements-dev.txt && pip install -e .` (pinned, faster resolve). Or `make reinstall`. |
| `ModuleNotFoundError: No module named 'handshakelab'` after editing code | `make reinstall` |
| `handshakelab --version` says "No such option" | Fixed in v0.3.1 — use `handshakelab --version` or `handshakelab version` |
| `airport=n/a` in doctor on macOS | Expected on macOS 14+. Use a USB adapter. |

### macOS

```bash
brew install tcpdump hcxtools hashcat
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
| `ui` | **Launch web UI** (scan → auto-crack → password) |
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

## What's done vs what's left

See **[`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md)** for the full breakdown.

**Done (v0.3.1):** Web UI, built-in sniffer, EAPOL detection, auto-crack pipeline, enhanced offline crack, AI wordlist option, CLI, tests, CI, passphrase masking, tool version audit, dev tooling (mypy, pytest-cov, pre-commit), shared test fixtures.

**Still needed (your side):** Install `tcpdump` + `hcxtools` + `hashcat`, USB adapter with monitor mode (Linux), end-to-end test on a lab AP you own, complete [`docs/HIL_CHECKLIST.md`](docs/HIL_CHECKLIST.md).

---

## Documentation

| Doc | Description |
| --- | --- |
| [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md) | **What's done + what's left** |
| [`docs/USER_GUIDE.md`](docs/USER_GUIDE.md) | Install & workflow (Linux + Mac) |
| [`docs/HIL_CHECKLIST.md`](docs/HIL_CHECKLIST.md) | Bench verification checklist |
| [`docs/PROJECT_PLAN.md`](docs/PROJECT_PLAN.md) | Full project plan |
| [`docs/TECHNICAL_BLUEPRINT.md`](docs/TECHNICAL_BLUEPRINT.md) | Technical design |
| [`docs/LEGAL_AND_ETHICS.md`](docs/LEGAL_AND_ETHICS.md) | **Read before use** |
| [`MASTER_TODO.md`](MASTER_TODO.md) | Live task ledger |

---

## Legal

**Authorized lab use only.** See [`docs/LEGAL_AND_ETHICS.md`](docs/LEGAL_AND_ETHICS.md).

## License

MIT
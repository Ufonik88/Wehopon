# HandshakeLab

**Offline WiFi handshake capture & crack workstation for authorized product testing.**

> Capture once → save locally → crack offline → reveal password → manually join the device under test.  
> No repeated failed logins against the AP.

**Repository:** [github.com/Ufonik88/Wehopon](https://github.com/Ufonik88/Wehopon)  
**Status:** Phase 0 — Planning complete; implementation starting Phase 1  
**Platform:** Linux + monitor-mode USB WiFi adapter

---

## What this is

HandshakeLab helps QA and security testers validate WiFi devices **on lab networks they own or are authorized to test**:

1. **Capture** a WPA handshake or PMKID from the air
2. **Save** `capture.pcapng` and a Hashcat-ready `.22000` hash file
3. **Crack offline** with Hashcat (CPU/GPU) — the router is not hammered with wrong passwords
4. **Show** the recovered passphrase so you type it manually into the device under test

## What this is NOT

- Not a cloud app or phone app
- Not for use on networks you do not own or have permission to test
- Not an auto-connect tool (manual entry by design)

**Read [`docs/LEGAL_AND_ETHICS.md`](docs/LEGAL_AND_ETHICS.md) before use.**

---

## Documentation

| Document | Description |
| --- | --- |
| [`docs/PROJECT_PLAN.md`](docs/PROJECT_PLAN.md) | Full project plan (start here) |
| [`docs/TECHNICAL_BLUEPRINT.md`](docs/TECHNICAL_BLUEPRINT.md) | Technical design & CLI spec |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Module architecture & data flow |
| [`docs/PHASE_ROADMAP.md`](docs/PHASE_ROADMAP.md) | Implementation phases & exit criteria |
| [`docs/HARDWARE.md`](docs/HARDWARE.md) | Adapter & lab hardware guide |
| [`docs/LEGAL_AND_ETHICS.md`](docs/LEGAL_AND_ETHICS.md) | Authorized use policy |
| [`docs/architecture.html`](docs/architecture.html) | Visual architecture diagram |
| [`MASTER_TODO.md`](MASTER_TODO.md) | Live task ledger |

---

## Quick start (after Phase 1 implementation)

```bash
# System dependencies (Ubuntu/Debian example)
sudo apt install hcxdumptool hcxtools hashcat iw wireshark-common

# Python package
pip install -e ".[dev]"

# Configure lab allow-list
cp lab.toml.example lab.toml
# Edit lab.toml — add your lab AP SSID/BSSID

# Preflight
sudo handshakelab doctor

# Full workflow
sudo handshakelab scan -i wlan1
sudo handshakelab capture -i wlan1 --ssid LAB-AP-01 --channel 6 --duration 120 --ack-authorized
handshakelab convert latest
handshakelab crack latest --wordlist ./wordlists/your-qa-list.txt
handshakelab show latest --reveal
```

---

## Project layout

```
.
├── docs/                    # Project plan & technical documentation
├── src/handshakelab/        # Python package (CLI + services)
├── tests/                   # Unit tests (fixtures only, no real captures in git)
├── lab.toml.example         # Authorized target allow-list template
├── pyproject.toml
├── MASTER_TODO.md           # Cross-session task ledger
└── README.md
```

---

## Stack

- **Python 3.11+** — orchestration CLI
- **hcxdumptool / hcxtools** — capture & convert to `.22000`
- **Hashcat** — offline WPA cracking
- **SQLite** — local run metadata vault

---

## License

MIT — see [`LICENSE`](LICENSE). Use responsibly and only on authorized networks.
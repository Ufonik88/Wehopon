# HandshakeLab — Project Status

**Version:** 0.3.1  
**Last updated:** 2026-06-15  
**Repository:** [github.com/Ufonik88/Wehopon](https://github.com/Ufonik88/Wehopon)  
**Product:** HandshakeLab — passive WiFi handshake capture + offline crack

> **Start here** for a full picture of what exists, what works, and what still needs doing.

---

## 1. Original brief (what you asked for)

Build a tool for **authorized product testing** that:

1. Captures WiFi authentication material from the air (handshake / PMKID)
2. Saves it locally
3. Cracks it **offline** — no repeated failed logins against the router/AP
4. Shows the recovered password in **plaintext** so you can manually join the device under test

**Key clarification:** You do **not** need the WiFi password to capture. You do **not** join the network. The tool passively sniffs the air (like Wireshark) and waits for any device to connect to the target AP.

**Platforms:** Linux + macOS.

---

## 2. Project history (how we got here)

| Date | Event |
| --- | --- |
| 2026-06-14 | Repo created with **wrong project** (WeHopOn travel planner — Next.js + Supabase) |
| 2026-06-14 | User clarified actual brief → full redesign to HandshakeLab |
| 2026-06-14 | **v0.1.0** — Python CLI: doctor, scan, capture, convert, crack, show, report |
| 2026-06-14 | **v0.2.0** — Web UI (`handshakelab ui`), one-click auto-crack, enhanced multi-stage cracking, optional AI wordlist |
| 2026-06-14 | **v0.3.0** — Built-in passive sniffer (tcpdump/hcxdumptool/airport), EAPOL detection, live packet counters in UI |
| 2026-06-15 | **v0.3.1** — Hardening & UX gap fixes: optional `--interface`, passphrase masking in `report.json`, tool versions in `meta.json`, lab context in UI, test coverage 17 → 40 |

---

## 3. What has been built (complete)

### 3.1 Core application (`src/handshakelab/`)

| Module | Purpose | Status |
| --- | --- | --- |
| `cli.py` | Typer CLI + `ui` command | ✅ Done |
| `server.py` | FastAPI local web server (127.0.0.1:8765) | ✅ Done |
| `pipeline.py` | Automated scan → capture → convert → crack job runner | ✅ Done |
| `sniffer.py` | Built-in passive capture (tcpdump / hcxdumptool / airport) | ✅ Done |
| `eapol.py` | Handshake / EAPOL frame detection (no Wireshark GUI needed) | ✅ Done |
| `capture.py` | Capture orchestration + import external pcaps | ✅ Done |
| `convert.py` | pcapng → Hashcat `.22000` via hcxpcapngtool | ✅ Done |
| `crack.py` | Offline Hashcat wrapper | ✅ Done |
| `crack_enhanced.py` | Multi-stage attack (SSID heuristics, mutations, AI, lab wordlist) | ✅ Done |
| `wordlist_gen.py` | Smart wordlist from SSID/BSSID patterns | ✅ Done |
| `ai_wordlist.py` | Optional OpenAI-compatible API for password candidates | ✅ Done |
| `vault.py` | SQLite metadata + per-run artifact folders | ✅ Done |
| `config.py` | `lab.toml` loader | ✅ Done |
| `legal.py` | Authorization gate + UI trust checkbox | ✅ Done |
| `doctor.py` | Preflight checks (tools, adapter, monitor mode) | ✅ Done |
| `report.py` | QA reports (Markdown / JSON) | ✅ Done |
| `util/wifi.py` | Scan, interfaces, monitor mode (Linux + macOS) | ✅ Done |
| `util/platform.py` | Cross-platform paths and detection | ✅ Done |
| `data/common-lab.txt` | Built-in weak-password list for product QA | ✅ Done |

### 3.2 Web UI (`src/handshakelab/web/`)

| Feature | Status |
| --- | --- |
| Scan button → list SSIDs | ✅ Done |
| Click to select target network | ✅ Done |
| One-click **Start Auto-Crack** | ✅ Done |
| Live progress bar + SSE streaming | ✅ Done |
| Built-in sniffer stats (packets / EAPOL / engine) | ✅ Done |
| Plaintext password display + copy button | ✅ Done |
| Authorization checkbox | ✅ Done |
| AI wordlist toggle | ✅ Done |
| “You never join the WiFi” explainer banner | ✅ Done |

### 3.3 CLI commands

| Command | Description | Status |
| --- | --- | --- |
| `handshakelab ui` | Launch web UI (recommended) | ✅ |
| `handshakelab doctor` | Preflight toolchain check | ✅ |
| `handshakelab scan` | Passive WiFi scan | ✅ |
| `handshakelab capture` | Live handshake capture (sudo) | ✅ |
| `handshakelab import` | Import existing `.pcap` / `.pcapng` | ✅ |
| `handshakelab convert` | pcapng → `.22000` | ✅ |
| `handshakelab crack` | Offline Hashcat | ✅ |
| `handshakelab show --reveal` | Plaintext password | ✅ |
| `handshakelab report` | QA report md/json | ✅ |
| `handshakelab list` | List vault runs | ✅ |

### 3.4 Enhanced offline crack stages (automatic in UI)

1. SSID heuristics + built-in `common-lab.txt`
2. AI-assisted candidates (if `HANDSHAKELAB_AI_API_KEY` set)
3. Custom wordlist from `lab.toml` (if configured)
4. SSID mutation pass

### 3.5 Documentation

| Document | Status |
| --- | --- |
| `README.md` | ✅ |
| `docs/USER_GUIDE.md` | ✅ |
| `docs/PROJECT_PLAN.md` | ✅ |
| `docs/TECHNICAL_BLUEPRINT.md` | ✅ |
| `docs/ARCHITECTURE.md` | ✅ |
| `docs/PHASE_ROADMAP.md` | ✅ (updated below) |
| `docs/LEGAL_AND_ETHICS.md` | ✅ |
| `docs/HARDWARE.md` | ✅ |
| `docs/PROJECT_STATUS.md` | ✅ (this file) |
| `MASTER_TODO.md` | ✅ |
| `AGENTS.md` | ✅ |
| `lab.toml.example` | ✅ |

### 3.6 Tests & CI

| Item | Status |
| --- | --- |
| pytest unit tests (40 tests) | ✅ Green |
| ruff lint | ✅ Green |
| GitHub Actions (Python 3.11, ruff, pytest) | ✅ |

### 3.7 Artifact storage

| Platform | Vault location |
| --- | --- |
| Linux | `~/.local/share/handshakelab/captures/` |
| macOS | `~/Library/Application Support/handshakelab/captures/` |

Each run folder contains: `capture.pcapng`, `crack.22000`, `crack.log`, `meta.json`, optional `report.md`.

---

## 4. What must still be done

### 4.1 Required before first real-world use (user / bench)

| # | Task | Owner | Priority |
| --- | --- | --- | --- |
| 1 | Install system tools: `tcpdump`, `hcxtools`, `hashcat` | User | **High** |
| 2 | `pip install -e .` in project venv | User | **High** |
| 3 | Copy `lab.toml.example` → `lab.toml` | User | Medium |
| 4 | Run `sudo handshakelab doctor -i <adapter>` and fix any red checks | User | **High** |
| 5 | **Hardware:** USB WiFi adapter with monitor mode on Linux (e.g. Alfa AWUS036ACH) | User | **High** on Linux |
| 6 | End-to-end test: scan → auto-crack → plaintext password on **lab AP you own** | User | **High** |
| 7 | Add internal QA wordlist path to `lab.toml` `[crack] wordlist` | User | Medium |
| 8 | Optional: set `HANDSHAKELAB_AI_API_KEY` for smarter guesses | User | Low |

### 4.2 Software improvements (future versions)

| # | Task | Priority | Notes |
| --- | --- | --- | --- |
| 1 | `docs/HIL_CHECKLIST.md` — formal hardware-in-loop release checklist | Medium | After first successful bench run |
| 2 | Hardware-in-loop verification documented with evidence | Medium | Adapter model, capture log, crack time |
| 3 | Hashcat GPU detection in `doctor` | Low | Faster cracks on NVIDIA/AMD |
| 4 | WPA3-SAE capture/crack notes and tooling | Low | Different attack surface |
| 5 | Controlled deauth module (lab-only, off by default) | Low | Forces handshake when no clients |
| 6 | Download artifacts from web UI | Low | |
| 7 | `.deb` / Homebrew formula packaging | Low | Easier install |
| 8 | Rename GitHub repo `Wehopon` → `HandshakeLab` | Low | Cosmetic |
| 9 | Tag release `v0.3.0` on GitHub | Low | |

### 4.3 Known limitations (not bugs — physics)

| Limitation | Explanation |
| --- | --- |
| **Handshake requires traffic** | Another device must connect to the target AP while we listen. No traffic = no handshake. |
| **Linux needs monitor mode** | Built-in laptop WiFi often cannot sniff. USB adapter required. |
| **macOS built-in WiFi is limited** | `airport sniff` works on a channel; USB adapter + hcxdumptool is more reliable. |
| **Strong passwords won't crack** | Offline dictionary attack only finds weak/common passwords. |
| **AI doesn't break WPA math** | AI generates guess candidates; Hashcat verifies them. |
| **sudo required for capture** | Monitor mode needs root: `sudo handshakelab ui` |

---

## 5. How to run (quick reference)

```bash
# Linux — install deps
sudo apt install tcpdump hcxdumptool hcxtools hashcat iw

# macOS
brew install tcpdump hcxtools hashcat

# Python app
cd Wehopon
python3 -m venv .venv && source .venv/bin/activate
pip install -e .

# Launch UI (sudo for capture)
sudo handshakelab ui
# → http://127.0.0.1:8765
```

**Workflow:** Scan → select SSID → check authorized → Start Auto-Crack → copy plaintext password.

---

## 6. Version changelog

### v0.3.1 (2026-06-15)
- CLI: `--interface` is now optional for `scan`, `capture`, and `import`; falls back to `lab.toml`
- Security: `report.json` no longer contains the plaintext passphrase — only a first+last-char mask; `report.md` instructs operators to use `handshakelab show <run> --reveal`
- Audit: per-run `meta.json` now records installed tool versions (hashcat, hcxdumptool, hcxpcapngtool, tcpdump, tshark) per TECHNICAL_BLUEPRINT §4.3
- UX: web UI shows lab name, operator, and default adapter; footer shows `version · platform · lab name`
- Sniffer: backend preference order now matches docs — **tcpdump first**, then hcxdumptool, then macOS airport
- Tests: added 23 unit tests (17 → 40) covering `doctor`, `report`, `convert`, `crack`, `pipeline`, `ai_wordlist`

### v0.3.0 (2026-06-14)
- Built-in passive sniffer (`sniffer.py`) — tcpdump, hcxdumptool, macOS airport
- EAPOL handshake detection (`eapol.py`) without Wireshark GUI
- Live packet/EAPOL counters in web UI
- Default capture duration 300s
- Clarified: no WiFi join required for unknown passwords

### v0.2.0 (2026-06-14)
- Web UI at `handshakelab ui` (FastAPI + vanilla JS)
- One-click auto-crack pipeline
- Enhanced multi-stage cracking
- Optional AI wordlist generation

### v0.1.0 (2026-06-14)
- Full Python CLI
- Linux + macOS capture backends
- SQLite vault, lab.toml authorization
- 17 unit tests, GitHub Actions CI

### v0.0.x (removed)
- WeHopOn travel planner (wrong brief) — deleted

---

## 7. Repository layout

```
Wehopon/
├── src/handshakelab/       # Python application
│   ├── web/                # Web UI (HTML/CSS/JS)
│   ├── data/               # Built-in wordlist
│   ├── cli.py              # CLI entry
│   ├── server.py           # FastAPI UI server
│   ├── pipeline.py         # Auto-crack orchestrator
│   ├── sniffer.py          # Built-in capture
│   ├── eapol.py            # Handshake detection
│   └── …                   # capture, crack, vault, etc.
├── docs/                   # All documentation
├── tests/                  # pytest (17 tests)
├── lab.toml.example        # Config template
├── MASTER_TODO.md          # Live task ledger
├── README.md
└── pyproject.toml
```

---

## 8. Related docs

- **Install & use:** [`USER_GUIDE.md`](USER_GUIDE.md)
- **Architecture:** [`ARCHITECTURE.md`](ARCHITECTURE.md)
- **Hardware:** [`HARDWARE.md`](HARDWARE.md)
- **Legal:** [`LEGAL_AND_ETHICS.md`](LEGAL_AND_ETHICS.md)
- **Live tasks:** [`../MASTER_TODO.md`](../MASTER_TODO.md)
# HandshakeLab — Agent Instructions

## Project

**HandshakeLab** — passive WiFi handshake capture + offline crack for **authorized product testing**.

**Repo:** [github.com/Ufonik88/Wehopon](https://github.com/Ufonik88/Wehopon)  
**Version:** 0.3.0  
**Status doc:** [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md) — **read this first** for done vs remaining work.

## Original brief

Capture handshake passively (no WiFi join) → save locally → crack offline → show plaintext password.

## Read first (every session)

1. [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md) — what's built, what's left
2. [`MASTER_TODO.md`](MASTER_TODO.md) — live task ledger
3. [`docs/LEGAL_AND_ETHICS.md`](docs/LEGAL_AND_ETHICS.md) — authorized use only

## Stack

- **Python 3.11+** — Typer CLI, FastAPI web UI
- **Built-in sniffer** — tcpdump, hcxdumptool, macOS airport (`sniffer.py`)
- **EAPOL detection** — `eapol.py` (no Wireshark GUI required)
- **Crack** — Hashcat offline + enhanced stages + optional AI wordlist
- **Vault** — SQLite + filesystem artifacts
- **Platforms** — Linux + macOS

## Key commands

```bash
sudo handshakelab ui      # recommended — web UI
sudo handshakelab doctor  # preflight
handshakelab scan -i wlan1
```

## What is done (v0.3.0)

- Full CLI, web UI, auto-crack pipeline, built-in sniffer, enhanced crack, tests, CI, docs

## What remains

- User bench verification (`docs/HIL_CHECKLIST.md`)
- Future: GPU doctor, WPA3, packaging, repo rename

## Rules

- Never commit captures, wordlists, passphrases, or real `lab.toml`
- Offline crack only — never online brute force against AP
- User does NOT join WiFi to capture — passive sniff only
- Verify with command output before marking tasks done

## GitHub CLI on this machine

```bash
export PATH="/home/linuxbrew/.linuxbrew/bin:$PATH"
```
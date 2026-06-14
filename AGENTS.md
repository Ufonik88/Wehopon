# HandshakeLab — Agent Instructions

## Project

**HandshakeLab** — offline WiFi handshake capture & crack for **authorized product testing only**.

Repository: `github.com/Ufonik88/Wehopon` (product name HandshakeLab; repo rename TBD).

## Read first (every session)

1. [`MASTER_TODO.md`](MASTER_TODO.md) — live task ledger
2. [`docs/PROJECT_PLAN.md`](docs/PROJECT_PLAN.md) — what we are building
3. [`docs/LEGAL_AND_ETHICS.md`](docs/LEGAL_AND_ETHICS.md) — authorized use only

## What we are NOT building

- Travel planner / WeHopOn (removed — wrong brief)
- Next.js web app for capture (impossible — needs Linux monitor mode + root)
- Online brute force against APs
- Auto-join to cracked networks

## Stack

- Python 3.11+ CLI (`typer`, `rich`)
- External tools: `hcxdumptool`, `hcxpcapngtool`, `hashcat`, `iw`
- SQLite vault for run metadata
- Linux only for capture

## Implementation order

Follow [`docs/PHASE_ROADMAP.md`](docs/PHASE_ROADMAP.md):

1. `doctor` → 2. `capture` → 3. `convert` → 4. `crack` → 5. `show` / `report`

## Rules

- Never commit captures, wordlists, passphrases, or `lab.toml` with real targets.
- Always enforce `lab.toml` allow-list before capture code runs.
- Offline crack only — never call `wpa_supplicant` / `nmcli connect` with guessed passwords.
- Verify with real command output before marking tasks done in `MASTER_TODO.md`.

## GitHub CLI on this machine

`gh` may be shadowed by a Python package. Use:

```bash
export PATH="/home/linuxbrew/.linuxbrew/bin:$PATH"
```
# HandshakeLab — Phase Roadmap

**Current version:** 0.3.0  
**Current phase:** 8 — Bench verification (user)  
**Status overview:** [`PROJECT_STATUS.md`](PROJECT_STATUS.md)

---

## Phase 0 — Planning & documentation ✅

- [x] Replace wrong travel-app plan
- [x] Full docs in `docs/`
- [x] `MASTER_TODO.md`, `README.md`, blueprint, architecture, legal, hardware

---

## Phase 1 — Lab toolchain bootstrap ✅

- [x] `handshakelab doctor`
- [x] `lab.toml.example`
- [x] Package docs in `USER_GUIDE.md`

---

## Phase 2 — Capture pipeline ✅

- [x] `config.py` + `legal.py` authorization gate
- [x] Passive scan (Linux + macOS)
- [x] `capture.py` + `import` command
- [x] Monitor mode helpers (Linux)

---

## Phase 3 — Convert + vault ✅

- [x] `vault.py` — SQLite + artifact folders
- [x] `convert.py` — hcxpcapngtool → `.22000`
- [x] `handshakelab list`

---

## Phase 4 — Offline crack engine ✅

- [x] `crack.py` — Hashcat wrapper
- [x] Potfile parser, crack logging
- [x] Zero online auth attempts (offline only)

---

## Phase 5 — CLI polish + QA reports ✅

- [x] `report.py` — Markdown + JSON
- [x] Rich CLI output
- [x] `docs/USER_GUIDE.md`

---

## Phase 6 — Web UI + auto-crack ✅ (v0.2.0)

- [x] FastAPI server on 127.0.0.1:8765
- [x] Scan button, network selection
- [x] One-click auto-crack pipeline
- [x] SSE live progress
- [x] Plaintext password + copy
- [x] Enhanced multi-stage crack
- [x] Optional AI wordlist

**Exit:** `sudo handshakelab ui` → scan → select → auto-crack → password shown.

---

## Phase 7 — Built-in sniffer ✅ (v0.3.0)

- [x] `sniffer.py` — tcpdump / hcxdumptool / airport backends
- [x] `eapol.py` — handshake detection without Wireshark GUI
- [x] Live packet/EAPOL counters in UI
- [x] 300s default capture window
- [x] “No WiFi join required” workflow documented

**Exit:** Passive capture works; EAPOL detected when client joins AP.

---

## Phase 8 — Bench verification ⬜ (current)

**Goal:** Prove end-to-end on real hardware.

| Task | Owner | Status |
| --- | --- | --- |
| Install tcpdump + hcxtools + hashcat | User | ⬜ |
| `sudo handshakelab doctor` green | User | ⬜ |
| USB monitor-mode adapter (Linux) | User | ⬜ |
| E2E auto-crack on owned lab AP | User | ⬜ |
| Complete `docs/HIL_CHECKLIST.md` | User | ⬜ |
| Tag GitHub release v0.3.0 | Agent | ⬜ |

---

## Phase 9 — Future enhancements ⬜

| Task | Priority |
| --- | --- |
| GPU hashcat detection in doctor | Low |
| WPA3-SAE documentation + tooling | Low |
| Controlled deauth module (lab-only, off by default) | Low |
| Artifact download in web UI | Low |
| `.deb` / Homebrew formula | Low |
| Rename repo `Wehopon` → `HandshakeLab` | Low |

---

## Timeline (actual)

| Phase | Completed |
| --- | --- |
| 0–7 | 2026-06-14 (same day — v0.1.0 → v0.3.0) |
| 8 | Pending user bench test |
| 9 | Backlog |
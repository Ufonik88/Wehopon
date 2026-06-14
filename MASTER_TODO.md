# HandshakeLab — MASTER_TODO.md

> **Product:** HandshakeLab — offline WiFi handshake capture & crack (authorized product testing)  
> **Repo:** [github.com/Ufonik88/Wehopon](https://github.com/Ufonik88/Wehopon)  
> **Last updated:** 2026-06-14  
> **Version:** 0.1.0

---

## 1. Original brief

Capture WiFi handshake → save locally → crack offline → show password for manual device join.  
**Platforms:** Linux + macOS.

---

## 2. Status snapshot

| Area | State | Evidence |
| --- | --- | --- |
| CLI: doctor, scan, capture, import, convert, crack, show, report, list | ✅ | `src/handshakelab/cli.py` |
| Linux capture (hcxdumptool + iw monitor) | ✅ | `src/handshakelab/capture.py` |
| macOS capture (airport sniff + hcxdumptool) | ✅ | `src/handshakelab/capture.py` |
| Import external pcap | ✅ | `handshakelab import` |
| SQLite vault + artifact dirs | ✅ | `src/handshakelab/vault.py` |
| Authorization gate (lab.toml) | ✅ | `src/handshakelab/legal.py` |
| Unit tests | ✅ | `tests/` — pytest green |
| User guide (Linux + Mac) | ✅ | `docs/USER_GUIDE.md` |
| Hardware-in-loop on real adapter | ⬜ | Needs bench verification |
| Optional local web UI | ⬜ | Phase 6 |

---

## 3. Phase plan

### Phase 1 — Toolchain bootstrap ✅
- ✅ `handshakelab doctor`
- ✅ `lab.toml.example`

### Phase 2 — Capture ✅
- ✅ `scan`, `capture`, `import`
- ✅ Authorization gate

### Phase 3 — Convert + vault ✅
- ✅ `convert`, `list`, SQLite vault

### Phase 4 — Offline crack ✅
- ✅ `crack`, `show`

### Phase 5 — Reports ✅
- ✅ `report` md/json
- ✅ `docs/USER_GUIDE.md`

### Phase 6 — Optional web UI ⬜
### Phase 7 — HIL checklist on real hardware ⬜

---

## 4. Active backlog

- [ ] **[user]** Run `sudo handshakelab doctor` on bench (Linux + Mac if available)
- [ ] **[user]** End-to-end test against lab AP with known password
- [ ] **[user]** Confirm USB adapter model for Linux PMKID capture
- [ ] **[agent]** HIL_CHECKLIST.md after first successful bench run

---

## 5. Done

- 2026-06-14 — Full MVP implementation v0.1.0 (Linux + macOS)
- 2026-06-14 — Planning docs + redesign from travel-app correction
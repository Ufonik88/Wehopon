# HandshakeLab Current State

**Version:** 0.3.0  
**Current Phase:** 8 — Bench verification (user must test on real hardware)  
**Last Updated:** 2026-06-14  
**Product:** HandshakeLab — passive WiFi capture + offline crack (Linux + macOS)

---

## Summary

Software is **feature-complete for v0.3.0**. All core code, web UI, built-in sniffer, enhanced cracking, tests, and documentation are implemented and pushed to GitHub.

**What remains is user-side:** install system tools, verify on real WiFi adapter + lab AP, complete HIL checklist.

---

## Completed

- Built-in passive sniffer (`sniffer.py`) — tcpdump / hcxdumptool / macOS airport
- EAPOL detection (`eapol.py`) — no Wireshark GUI required
- Web UI (`handshakelab ui`) — scan, select, one-click auto-crack, plaintext password
- Enhanced multi-stage offline crack + optional AI wordlist
- Full CLI + SQLite vault + CI (17 tests green)
- Comprehensive docs including `docs/PROJECT_STATUS.md`

---

## Next (user action required)

1. Install: `tcpdump`, `hcxtools`, `hashcat`
2. Run: `sudo handshakelab doctor -i <adapter>`
3. Run: `sudo handshakelab ui` → test on **lab AP you own**
4. Complete: `docs/HIL_CHECKLIST.md`

---

## Key docs

| Doc | Purpose |
| --- | --- |
| [`docs/PROJECT_STATUS.md`](../docs/PROJECT_STATUS.md) | **What’s done + what’s left** |
| [`docs/USER_GUIDE.md`](../docs/USER_GUIDE.md) | Install & workflow |
| [`docs/HIL_CHECKLIST.md`](../docs/HIL_CHECKLIST.md) | Bench verification |
| [`MASTER_TODO.md`](../MASTER_TODO.md) | Live task ledger |
# HandshakeLab — Technical Blueprint

**Date:** 2026-06-14  
**Status:** v0.3.1 — Implementation complete; bench verification pending. See [`PROJECT_STATUS.md`](PROJECT_STATUS.md).
**Approach:** Linux-native, CLI-first, offline cracking workstation

---

## 1. Discovery & research

### 1.1 Problem validation

Your brief maps directly to the standard **offline WPA-PSK audit** workflow used in penetration testing and hardware QA:

| Brief requirement | Industry equivalent |
| --- | --- |
| Capture a packet | 802.11 EAPOL 4-way handshake or PMKID capture |
| Save locally | `.pcapng` evidence store |
| Crack there (offline) | Hashcat mode 22000 / aircrack-ng |
| Show password | Post-crack passphrase reveal |
| Avoid failed logins | No online PSK brute force against AP |

This is the **correct** approach for product testing: the AP is not subjected to repeated authentication failures.

### 1.2 Feasibility

| Component | Maturity | Risk |
| --- | --- | --- |
| Monitor mode capture | High (linux `mac80211`) | Medium — driver-dependent |
| hcxdumptool PMKID | High | Low on WPA2 |
| Hashcat WPA | High | Low |
| WPA3-SAE cracking | Low/Medium | High — different attack surface |
| Python orchestration | High | Low |

**Feasibility score:** High for WPA2-PSK lab networks. WPA3-only targets need explicit lab policy.

### 1.3 WPA2 vs WPA3 notes

- **WPA2-PSK:** Capture EAPOL frames → PBKDF2-HMAC-SHA1 (4096 iterations) → Hashcat cracks offline.
- **WPA3-SAE:** Dragonfly handshake; dictionary attacks still possible for **weak passwords** but capture format and tools differ. v1 focuses WPA2-PSK; WPA3 documented as Phase 2 stretch.

### 1.4 Toolchain survey

| Tool | Role | Verdict |
| --- | --- | --- |
| **hcxdumptool** | Live capture → pcapng | Primary capture |
| **hcxpcapngtool** | pcapng → .22000 | Primary converter |
| **Hashcat** | Offline cracking | Primary cracker |
| aircrack-ng | Legacy capture/crack | Fallback |
| Wireshark/tshark | Inspection | Debug only |
| wifite2 | Orchestrator | Reference only; too opinionated for QA |

---

## 2. System architecture

### 2.1 Component diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                        Linux lab workstation                      │
│  ┌────────────┐  ┌─────────────┐  ┌──────────┐  ┌─────────────┐ │
│  │ handshakelab│  │  SQLite     │  │ captures/│  │  wordlists/ │ │
│  │ CLI (Python)│  │  vault DB   │  │  artifacts│  │  (local)    │ │
│  └──────┬─────┘  └─────────────┘  └──────────┘  └─────────────┘ │
│         │ orchestrates                                            │
│         v                                                         │
│  ┌──────────────┐   ┌───────────────┐   ┌─────────────────────┐  │
│  │ hcxdumptool  │   │ hcxpcapngtool │   │ hashcat             │  │
│  │ (capture)    │   │ (convert)     │   │ (offline crack)     │  │
│  └──────┬───────┘   └───────────────┘   └─────────────────────┘  │
│         │ requires root + monitor mode                              │
│         v                                                         │
│  ┌──────────────────────────────────────────────────────────────┐│
│  │ USB WiFi adapter (nl80211)  ──RF──>  Lab AP under test       ││
│  └──────────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────┘
```

### 2.2 Data flow

1. **Preflight** (`handshakelab doctor`)
   - Verify root/sudo, adapter present, `iw phy` shows monitor mode, hashcat/hcxtools installed.
   - Load `lab.toml` allow-listed BSSIDs.

2. **Scan** (`handshakelab scan -i wlan1`)
   - Passive scan; no injection.

3. **Capture** (`handshakelab capture --ssid LAB-AP --channel 36 --duration 120`)
   - Set monitor mode on `wlan1`.
   - Run `hcxdumptool -i wlan1 -o capture.pcapng --filterlist_ap=...`.
   - Validate EAPOL present via `tshark` filter.

4. **Convert** (`handshakelab convert capture.pcapng`)
   - `hcxpcapngtool -o crack.22000 capture.pcapng`
   - Abort if zero hashes extracted.

5. **Crack** (`handshakelab crack crack.22000 --wordlist qa-wordlist.txt`)
   - `hashcat -m 22000 -a 0 crack.22000 qa-wordlist.txt`
   - Stream progress to `crack.log`.

6. **Reveal** (`handshakelab show <run-id>`)
   - Print passphrase to terminal (masked by default, `--reveal` to show).

7. **Report** (`handshakelab report <run-id> --format markdown`)
   - QA artifact for test case attachment.

### 2.3 Database schema (SQLite)

```sql
CREATE TABLE runs (
  id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL,
  operator TEXT,
  ssid TEXT,
  bssid TEXT,
  channel INTEGER,
  adapter TEXT,
  capture_path TEXT,
  hash_path TEXT,
  status TEXT,  -- captured | converted | cracked | failed
  authorized_by TEXT
);

CREATE TABLE crack_results (
  run_id TEXT PRIMARY KEY REFERENCES runs(id),
  cracked_at TEXT,
  method TEXT,       -- hashcat:22000:wordlist
  duration_ms INTEGER,
  passphrase TEXT,   -- optional AES-GCM blob
  success INTEGER
);
```

### 2.4 Configuration (`lab.toml`)

```toml
[lab]
name = "Ajax Randburg Bench"
operator = "ufonik"
require_authorization = true

[[allowed_targets]]
ssid = "LAB-AP-01"
bssid = "AA:BB:CC:DD:EE:FF"
owner = "Ajax Systems QA"
authorization_ref = "QA-2026-014"

[capture]
default_adapter = "wlan1"
default_duration_sec = 120
deauth_enabled = false

[crack]
hashcat_bin = "/usr/bin/hashcat"
wordlist = "/opt/handshakelab/wordlists/qa-internal.txt"
workload_profile = 2
```

---

## 3. CLI specification

### 3.1 Commands (v1)

```
handshakelab doctor                    # toolchain + adapter preflight
handshakelab scan -i wlan1             # list networks (passive)
handshakelab capture -i wlan1 --ssid SSID [--channel N] [--duration SEC]
handshakelab convert RUN_ID|FILE       # pcapng -> 22000
handshakelab crack RUN_ID [--wordlist PATH] [--rules PATH]
handshakelab show RUN_ID [--reveal]    # display result
handshakelab report RUN_ID [-f md|json]
handshakelab list                      # show all runs in vault
```

### 3.2 Example session

```bash
sudo handshakelab doctor
sudo handshakelab scan -i wlan1
sudo handshakelab capture -i wlan1 --ssid LAB-CAM-TEST --channel 6 --duration 180
handshakelab convert latest
handshakelab crack latest --wordlist ./wordlists/ajax-qa.txt
handshakelab show latest --reveal
# Tester manually enters password into device under test
```

---

## 4. Implementation modules

### 4.1 Package layout

```
src/handshakelab/
├── __init__.py
├── __main__.py
├── cli.py              # Typer entrypoints
├── config.py           # lab.toml loader + validation
├── doctor.py           # preflight checks
├── scan.py             # iw/nmcli passive scan
├── capture.py          # hcxdumptool wrapper
├── convert.py          # hcxpcapngtool wrapper
├── crack.py            # hashcat wrapper + potfile parser
├── vault.py            # SQLite + filesystem paths
├── report.py           # markdown/json export
├── legal.py            # authorization gate
└── util/
    ├── proc.py         # subprocess runner with logging
    └── wifi.py         # monitor mode helpers
```

### 4.2 Error handling

| Error | User message | Recovery |
| --- | --- | --- |
| Not root | "Capture requires root. Re-run with sudo." | Exit 1 |
| No monitor mode | "Adapter wlan1 does not support monitor mode." | Link to HARDWARE.md |
| SSID not allow-listed | "SSID not in lab.toml. Refusing capture." | Exit 2 |
| No EAPOL in capture | "No handshake found. Retry capture or enable passive wait." | Exit 3 |
| Hashcat missing | "Install hashcat: apt install hashcat" | Exit 1 |

### 4.3 Logging

- Structured JSON logs to `~/.local/share/handshakelab/logs/`
- Per-run `meta.json` includes tool versions (`hashcat -V`, `hcxdumptool -v`)

---

## 5. Security architecture

### 5.1 Threat model

| Threat | Control |
| --- | --- |
| Misuse on public WiFi | `lab.toml` allow-list + legal acknowledgment flag |
| Passphrase leakage | Masked display; optional encryption; no network join |
| Tampered captures | SHA-256 of pcapng in `meta.json` |
| Privilege escalation | Minimal sudo surface; only capture module needs root |

### 5.2 Authorization gate

Before `capture`:

```python
def assert_authorized(ssid: str, bssid: str, config: LabConfig) -> None:
    if not config.require_authorization:
        return
    if not config.find_target(ssid, bssid):
        raise AuthorizationError(
            f"Target {ssid}/{bssid} not in lab.toml. "
            "Add explicit authorization before capture."
        )
```

CLI adds `--ack-authorized` for interactive sessions.

---

## 6. Testing blueprint

### 6.1 Fixtures

- `tests/fixtures/sample.eapol.pcapng` — synthetic handshake (generated in lab)
- `tests/fixtures/known-password.txt` — single entry matching fixture
- `tests/fixtures/lab.toml` — test allow-list

### 6.2 CI strategy

GitHub Actions:

- **lint:** `ruff check`, `mypy` (no hardware)
- **unit:** convert/crack parsing with mocked hashcat
- **integration:** skipped on CI; manual `HIL_CHECKLIST.md` on release

---

## 7. Deployment model

- **Not deployed to cloud.** Installed on lab machines only.
- `pip install -e ".[dev]"` from repo.
- Optional `.deb` wrapper later.
- Hashcat GPU drivers installed separately (NVIDIA/CUDA or ROCm).

---

## 8. Future enhancements (post-MVP)

| Feature | Priority |
| --- | --- |
| FastAPI localhost dashboard | Medium |
| WPA3-SAE capture notes | Medium |
| Automatic report upload to test management | Low |
| Distributed cracking | Out of scope |
| Mobile app | Out of scope |

---

## 9. Acceptance criteria (MVP)

1. `handshakelab doctor` passes on bench machine with compatible adapter.
2. Capture + convert + crack succeeds against lab AP with known 8+ char password.
3. Zero online authentication attempts sent to AP during crack phase.
4. `handshakelab show` displays passphrase; tester manually joins DUT.
5. `report` generates Markdown suitable for QA ticket attachment.
6. All operations logged; unauthorized SSID blocked.

---

*This blueprint replaces the previous travel-planner document entirely.*
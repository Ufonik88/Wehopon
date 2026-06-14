# HandshakeLab — Hardware-in-the-Loop Checklist

Use this checklist before claiming a release works on real hardware.  
Fill in evidence columns after each test run.

**Version under test:** ___________  
**Date:** ___________  
**Tester:** ___________  
**Machine OS:** ___________  
**WiFi adapter:** ___________  
**Interface name:** ___________

---

## A. Preflight

| # | Check | Pass? | Evidence |
| --- | --- | --- | --- |
| A1 | `pip install -e .` succeeds | ☐ | |
| A2 | `sudo handshakelab doctor -i <iface>` all critical checks green | ☐ | |
| A3 | `tcpdump --version` available | ☐ | |
| A4 | `hashcat -V` available | ☐ | |
| A5 | `hcxpcapngtool -v` available | ☐ | |
| A6 | Monitor mode supported on adapter (Linux: `iw list` shows `* monitor`) | ☐ | |

---

## B. Scan

| # | Check | Pass? | Evidence |
| --- | --- | --- | --- |
| B1 | `handshakelab ui` opens http://127.0.0.1:8765 | ☐ | |
| B2 | Scan button lists ≥1 SSID | ☐ | Screenshot or SSID list |
| B3 | Target lab AP appears with correct channel/BSSID | ☐ | |

---

## C. Capture (built-in sniffer)

| # | Check | Pass? | Evidence |
| --- | --- | --- | --- |
| C1 | Auto-crack starts without joining target WiFi | ☐ | |
| C2 | Packet counter increases during capture | ☐ | |
| C3 | EAPOL counter reaches ≥1 when client connects to AP | ☐ | |
| C4 | `capture.pcapng` saved under vault captures folder | ☐ | Path: |
| C5 | Capture backend recorded (tcpdump / hcxdumptool / airport) | ☐ | |

---

## D. Convert + crack

| # | Check | Pass? | Evidence |
| --- | --- | --- | --- |
| D1 | `crack.22000` generated with ≥1 hash | ☐ | |
| D2 | Enhanced crack stages run (check `crack.log`) | ☐ | |
| D3 | Plaintext password displayed in UI for **known weak lab password** | ☐ | Do not commit password |
| D4 | Zero online auth attempts sent to AP during crack | ☐ | Confirm offline only |

---

## E. Failure modes (verify messages are helpful)

| # | Check | Pass? | Evidence |
| --- | --- | --- | --- |
| E1 | No-client-on-AP scenario shows clear “wait for device to connect” message | ☐ | |
| E2 | Missing hashcat shows install hint in doctor | ☐ | |
| E3 | No sudo shows “run with sudo” message | ☐ | |

---

## F. Sign-off

| Field | Value |
| --- | --- |
| Lab AP SSID tested | |
| Known password verified (y/n) | |
| Crack duration | |
| Release approved (y/n) | |
| Notes | |

---

*Complete this checklist on a lab AP you own or are authorized to test. Do not use on third-party networks.*
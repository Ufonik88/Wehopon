# HandshakeLab — Testing Checklist

> Version: 0.3.1 · Last updated: 2026-06-25  
> Use this checklist to identify bugs, required patches, and remaining development tasks.  
> Append new steps at the bottom as testing reveals gaps.

---

## 1. Environment Setup

1. **System dependencies installed**
   - **Test:** Run `tcpdump --version && hashcat -V && hcxpcapngtool -v` (Linux: also `hcxdumptool --version`, `iw version`)
   - **Expected:** All commands return version strings without error. Install missing tools via `apt` (Linux) or `brew` (macOS).

2. **Python venv created & dependencies installed**
   - **Test:** `python3 -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"`
   - **Expected:** No errors. `handshakelab --help` prints usage.

3. **lab.toml configured**
   - **Test:** `cp lab.toml.example lab.toml` then edit to match your lab AP SSID, interface, operator name.
   - **Expected:** `lab.toml` exists with valid `[ui]`, `[capture]`, `[crack]` sections.

4. **Monitor mode available (Linux)**
   - **Test:** `iw list 2>/dev/null | grep -A5 "Supported interface modes" | grep monitor`
   - **Expected:** `* monitor` listed. If not, a USB adapter with monitor mode is required.

5. **WiFi adapter inserted & recognised**
   - **Test:** `iwconfig` (Linux) or `networksetup -listallhardwareports` (macOS)
   - **Expected:** Interface name (e.g. `wlan1`, `en0`) is visible.

---

## 2. Developer Toolchain & CI

6. **ruff lint passes**
   - **Test:** `ruff check src/ tests/`
   - **Expected:** No errors.

7. **mypy strict type check passes**
   - **Test:** `mypy src/handshakelab/`
   - **Expected:** No type errors.

8. **pytest unit tests pass with coverage**
   - **Test:** `pytest`
   - **Expected:** All 40+ tests pass. Coverage ≥ 80% (fails if below threshold).

9. **pre-commit hooks installed & run**
   - **Test:** `pre-commit run --all-files`
   - **Expected:** All hooks (ruff, mypy, etc.) pass.

10. **GitHub Actions CI green (if pushed)**
    - **Test:** Push to branch, open Actions tab.
    - **Expected:** Python 3.11 → ruff → pytest workflow completes successfully.

---

## 3. Preflight (doctor)

11. **doctor runs without sudo (partial checks)**
    - **Test:** `handshakelab doctor -i <iface>` (no sudo)
    - **Expected:** Reports tool versions, adapter info. Capture-related checks show "requires sudo" but do not crash.

12. **doctor runs with sudo (full checks)**
    - **Test:** `sudo handshakelab doctor -i <iface>`
    - **Expected:** All critical checks green: tool versions, adapter, monitor mode, tcpdump capture test.

13. **doctor output includes GPU info (future)**
    - **Test:** Visual scan of doctor output.
    - **Expected:** If implemented, shows `hashcat_gpu:` row. Otherwise no crash.

---

## 4. Passive Scan

14. **CLI scan lists APs**
    - **Test:** `sudo handshakelab scan -i <iface>`
    - **Expected:** Table of SSIDs with BSSID, channel, signal strength. Your lab AP is present.

15. **CLI scan without `--interface` falls back to lab.toml**
    - **Test:** Remove `-i` flag; `sudo handshakelab scan`
    - **Expected:** Uses adapter from `lab.toml` `[capture] interface`. Same output as step 14.

16. **Scan shows no false positives**
    - **Test:** Compare listed SSIDs with known nearby networks.
    - **Expected:** No phantom or malformed SSID entries.

---

## 5. Passive Capture (built-in sniffer)

17. **CLI capture starts and produces pcapng**
    - **Test:** `sudo handshakelab capture -i <iface> --ssid <YOUR_LAB_SSID> --channel <CH> --duration 30 --ack-authorized`
    - **Expected:** Capture starts, counter ticks. After 30s a run folder appears under vault with `capture.pcapng`.

18. **EAPOL handshake detected when client connects**
    - **Test:** While capture runs, connect a client device to the lab AP.
    - **Expected:** Capture log/output shows "EAPOL frames detected" and counter ≥ 1.

19. **Capture without `--iface` falls back to lab.toml**
    - **Test:** `sudo handshakelab capture --ssid <SSID> --channel <CH> --duration 10 --ack-authorized`
    - **Expected:** Uses default interface from config, succeeds.

20. **Sniffer backend order (tcpdump first)**
    - **Test:** Run capture with verbose output. Check `meta.json` after.
    - **Expected:** Backend recorded is `tcpdump` (if installed), falling to `hcxdumptool`, then `airport`.

---

## 6. Import External Captures

21. **Import .pcap/.pcapng file**
    - **Test:** `handshakelab import /path/to/capture.pcapng --ssid <SSID> --ack-authorized`
    - **Expected:** File copied to vault, run registered, `list` shows it.

22. **Import rejects missing file**
    - **Test:** `handshakelab import /nonexistent.pcap --ssid <SSID>`
    - **Expected:** File-not-found error with clear message.

---

## 7. Convert (pcapng → .22000)

23. **Convert latest run**
    - **Test:** `handshakelab convert latest`
    - **Expected:** `crack.22000` file created in run folder; output shows how many hashes were extracted.

24. **Convert specific run ID**
    - **Test:** `handshakelab list` to get a run ID, then `handshakelab convert <run-id>`
    - **Expected:** Same as step 23, targeting the correct run.

25. **Convert run with no handshake produces zero-hash file**
    - **Test:** Capture a period with no client connecting, then `convert latest`.
    - **Expected:** `crack.22000` created but empty / zero hashes; tool warns "no handshake captured".

---

## 8. Offline Crack (hashcat)

26. **CLI crack runs against .22000 hash**
    - **Test:** `handshakelab crack latest --wordlist tests/fixtures/common-lab.txt`
    - **Expected:** Hashcat runs; `crack.log` created. If password is in wordlist, result shows "password recovered".

27. **CLI crack with no match fails gracefully**
    - **Test:** `handshakelab crack latest --wordlist /dev/null`
    - **Expected:** Hashcat exits; `crack.log` contains "Exhausted" or "no passwords recovered". No crash.

28. **Enhanced crack pipeline (multi-stage)**
    - **Test:** `handshakelab crack latest --enhanced`
    - **Expected:** Stages run in order: built-in wordlist → SSID heuristics → mutations. `crack.log` records each stage.

29. **AI wordlist stage (if configured)**
    - **Test:** Set `HANDSHAKELAB_AI_API_KEY`, run `handshakelab crack latest --enhanced --ai`
    - **Expected:** AI candidates generated and fed to hashcat. Stage logged in `crack.log`.

---

## 9. Plaintext Password Display

30. **`show` requires `--reveal` for plaintext**
    - **Test:** `handshakelab show latest`
    - **Expected:** Shows run metadata and masked passphrase (e.g. `F***d`).

31. **`show --reveal` shows full password**
    - **Test:** `handshakelab show latest --reveal`
    - **Expected:** Plaintext password printed to stdout.

32. **`show` on uncracked run shows "not yet cracked"**
    - **Test:** Run against a capture not yet cracked.
    - **Expected:** `show` reports no password available.

---

## 10. Reports

33. **Generate markdown report**
    - **Test:** `handshakelab report latest --format md`
    - **Expected:** `report.md` written to run folder. Plaintext passphrase is masked (not exposed).

34. **Generate JSON report**
    - **Test:** `handshakelab report latest --format json`
    - **Expected:** `report.json` written. Passphrase field is masked (first+last char only).

35. **Report for uncracked run**
    - **Test:** `handshakelab report latest --format md` on a run with no crack result.
    - **Expected:** Report generated with "not cracked" status, no crash.

---

## 11. Web UI End-to-End

36. **UI launches and is accessible**
    - **Test:** `sudo handshakelab ui` then open `http://127.0.0.1:8765`
    - **Expected:** Page loads. Footer shows version, platform, lab name. No 500 errors.

37. **Lab context displayed in UI**
    - **Test:** Check header/footer for lab name, operator, default adapter from `lab.toml`.
    - **Expected:** Values from config are visible.

38. **Scan from UI**
    - **Test:** Click "Scan" button.
    - **Expected:** Table populates with SSIDs. Lab AP visible.

39. **Authorization checkbox enforced**
    - **Test:** Click "Start Auto-Crack" without checking "I am authorized".
    - **Expected:** Button disabled or error shown. Crack does not start.

40. **Auto-crack pipeline runs from UI**
    - **Test:** Select SSID → check authorization → set duration → click Start Auto-Crack.
    - **Expected:** Progress bar updates live via SSE. Stages: capture → convert → crack. Final result shows password.

41. **Live packet counters during capture**
    - **Test:** Observe "Packets" and "EAPOL" counters during auto-crack capture phase.
    - **Expected:** Counters increment in real time. EAPOL ≥ 1 when a client connects.

42. **Plaintext password copy button works**
    - **Test:** After successful crack, click "Copy" next to plaintext password.
    - **Expected:** Password copied to clipboard.

43. **AI toggle present & functional**
    - **Test:** Check for AI wordlist toggle in UI. Toggle on/off.
    - **Expected:** Toggle exists. When on, pipeline includes AI stage (requires `HANDSHAKELAB_AI_API_KEY`).

44. **UI shows "never join WiFi" banner**
    - **Test:** Load UI.
    - **Expected:** Explainer banner visible, reassuring operator no network join occurs.

---

## 12. Vault & Artifacts

45. **`handshakelab list` shows all runs**
    - **Test:** `handshakelab list`
    - **Expected:** Table of all runs with run ID, SSID, timestamp, status, cracked status.

46. **Run folder contains all artifacts**
    - **Test:** `ls -la ~/.local/share/handshakelab/captures/<run-id>/` (Linux) or `~/Library/Application Support/...` (macOS)
    - **Expected:** Contains `capture.pcapng`, `crack.22000`, `crack.log`, `meta.json`, optional `report.md`.

47. **meta.json records tool versions**
    - **Test:** Read `meta.json` from a completed run.
    - **Expected:** Contains `tool_versions` hash with `hashcat`, `hcxdumptool`, `hcxpcapngtool`, `tcpdump`, `tshark` versions.

48. **meta.json records lab context**
    - **Test:** Read `meta.json`.
    - **Expected:** Contains `lab_name`, `operator`, `adapter` fields from `lab.toml`.

---

## 13. Security & Authorization

49. **Plaintext passphrase never written to report.json**
    - **Test:** `grep -r '<plaintext-password>' report.json` (replace with actual)
    - **Expected:** Not found. Only masked form present.

50. **Plaintext passphrase never written to crack.log**
    - **Test:** `grep '<plaintext-password>' crack.log`
    - **Expected:** Not found. Pipeline logs "SUCCESS: password recovered" instead.

51. **`show --reveal` is the only way to see plaintext**
    - **Test:** Inspect `report.md`, `report.json`, `crack.log`, vault DB for plaintext.
    - **Expected:** Plaintext only appears via `show --reveal`.

52. **Authorization gate blocks uncertified targets**
    - **Test:** Attempt to capture a SSID not in `lab.toml` `[ui] authorized_ssids` without `--ack-authorized`.
    - **Expected:** Command aborts with legal warning.

53. **UI trust checkbox satisfies auth for ad-hoc testing**
    - **Test:** Start auto-crack on an SSID not in `lab.toml` but with checkbox checked.
    - **Expected:** Pipeline proceeds.

---

## 14. CLI Command Completeness

54. **All CLI commands work**
    - **Test:** Run each: `handshakelab doctor`, `handshakelab scan`, `handshakelab capture`, `handshakelab import`, `handshakelab convert`, `handshakelab crack`, `handshakelab show`, `handshakelab report`, `handshakelab list`, `handshakelab ui`.
    - **Expected:** No crashes. Each command prints help or runs its function.

55. **`--help` on every command**
    - **Test:** `handshakelab --help`, `handshakelab scan --help`, etc.
    - **Expected:** Help text describes usage, options, examples.

---

## 15. Failure Modes & Edge Cases

56. **No sudo → clear error message**
    - **Test:** Run `handshakelab capture -i <iface> --ssid <SSID>` (as non-root).
    - **Expected:** Error: "run with sudo" or similar. Not a crash or traceback.

57. **Missing hashcat → install hint**
    - **Test:** Temporarily remove hashcat from PATH or rename binary. Run `handshakelab crack latest`.
    - **Expected:** Error message suggests installing hashcat.

58. **Missing tcpdump → fallback to hcxdumptool**
    - **Test:** Temporarily rename `tcpdump` binary. Run capture.
    - **Expected:** Sniffer falls back to next backend. Warning logged.

59. **No handshake captured → informative message**
    - **Test:** Capture on an idle channel with no client traffic, then crack.
    - **Expected:** Pipeline reports "no handshake captured" / "wait for device to connect".

60. **Empty wordlist → no crash**
    - **Test:** `handshakelab crack latest --wordlist /dev/null`
    - **Expected:** Hashcat runs, no crash, log shows zero matches.

61. **Invalid interface → clear error**
    - **Test:** `sudo handshakelab scan -i nonexistent0`
    - **Expected:** Error: "interface nonexistent0 not found".

62. **Interrupted capture → partial artifacts saved**
    - **Test:** Start capture, Ctrl+C after 5 seconds.
    - **Expected:** Partial `capture.pcapng` saved. Run is registered in vault with "interrupted" status.

63. **Very long SSID name handled**
    - **Test:** Create a lab AP with SSID of 32 characters, run scan + capture.
    - **Expected:** SSID displayed and stored without truncation or encoding errors.

---

## 16. Cross-Platform Parity (Linux vs macOS)

64. **`handshakelab doctor` on macOS**
    - **Test:** Run on macOS with `en0`.
    - **Expected:** Tool versions OK. Capture backend shows `airport` (or `tcpdump` if installed).

65. **`handshakelab scan` on macOS**
    - **Test:** `sudo handshakelab scan -i en0`
    - **Expected:** SSID list from `airport` scan. Same format as Linux.

66. **Capture on macOS (airport backend)**
    - **Test:** `sudo handshakelab capture -i en0 --ssid <SSID> --duration 30 --ack-authorized`
    - **Expected:** Capture succeeds via `airport sniff`. `meta.json` backend = `airport`.

---

## 17. Future Feature Acceptance (v0.4.0+)

67. **GPU hashcat detection in doctor (future)**
    - **Test:** `handshakelab doctor` shows `hashcat_gpu` row.
    - **Expected:** Row present. Shows device name or "not detected".

68. **Artifact download in web UI (future)**
    - **Test:** Open run details in UI, click Download.
    - **Expected:** File downloads with correct `Content-Disposition`.

69. **Controlled deauth module (future)**
    - **Test:** Set `capture.deauth_enabled = true` in `lab.toml`. Start capture on AP with no clients.
    - **Expected:** Deauth frames sent. Handshake captured. `meta.json` records `deauth=true`.

70. **Encrypted passphrase at rest (future)**
    - **Test:** Crack a password. Inspect `vault.db` directly.
    - **Expected:** Passphrase column contains ciphertext, not plaintext. `show --reveal` decrypts correctly.

---

## 18. Regression Testing (repeat after changes)

71. **Full regression run**
    - **Test:** After any code change, run: `ruff check src/ tests/ && mypy src/handshakelab/ && pytest`
    - **Expected:** All pass. Coverage ≥ 80%.

72. **Package re-install**
    - **Test:** `pip install -e .` after changes.
    - **Expected:** Install succeeds. `handshakelab --help` works.

---

*Add new test items below this line as testing reveals additional scenarios.*

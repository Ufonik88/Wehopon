# HandshakeLab User Guide

## Install

### Linux (Debian/Ubuntu)

```bash
sudo apt update
sudo apt install -y hcxdumptool hcxtools hashcat iw wireshark-common python3-venv

git clone https://github.com/Ufonik88/Wehopon.git
cd Wehopon
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### macOS

```bash
brew install hcxtools hashcat wireshark

git clone https://github.com/Ufonik88/Wehopon.git
cd Wehopon
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

**macOS capture notes:**

- **Import workflow** (recommended): capture with Wireshark or `airport sniff`, then `handshakelab import capture.pcapng ...`
- **Live capture:** `sudo handshakelab capture` uses `airport sniff` on built-in WiFi, or `hcxdumptool` with a USB adapter that supports monitor mode
- Built-in Mac WiFi has limited monitor mode — external Alfa adapters are more reliable for PMKID capture

---

## Configure

```bash
cp lab.toml.example lab.toml
```

Edit `lab.toml` — list every AP you are **authorized** to test:

```toml
[[allowed_targets]]
ssid = "LAB-AP-01"
bssid = "AA:BB:CC:DD:EE:FF"
authorization_ref = "QA-TICKET-001"

[crack]
wordlist = "/path/to/your-qa-wordlist.txt"
```

Never commit `lab.toml` or wordlists to git.

---

## Workflow

### 1. Preflight

```bash
handshakelab doctor
sudo handshakelab doctor -i wlan1   # Linux USB adapter
sudo handshakelab doctor -i en0     # macOS built-in
```

### 2. Scan

```bash
# Linux
sudo handshakelab scan -i wlan1

# macOS
handshakelab scan -i en0
```

### 3. Capture (live)

A WiFi client must associate with the AP during capture (natural handshake).

```bash
sudo handshakelab capture -i wlan1 \
  --ssid LAB-AP-01 \
  --channel 6 \
  --duration 180 \
  --ack-authorized
```

### 3b. Import (macOS / external tools)

If you already have a `.pcap`, `.pcapng`, or `.cap` file:

```bash
handshakelab import ./capture.pcapng \
  --ssid LAB-AP-01 \
  --bssid AA:BB:CC:DD:EE:FF \
  --ack-authorized
```

### 4. Convert

```bash
handshakelab convert latest
```

Produces `crack.22000` in the run folder.

### 5. Crack (offline)

The AP is **not** contacted during this step.

```bash
handshakelab crack latest --wordlist ./wordlists/qa.txt
```

### 6. Reveal

```bash
handshakelab show latest --reveal
```

Copy the passphrase and **manually enter it** on your device under test.

### 7. Report

```bash
handshakelab report latest --format md
```

---

## Run storage

| Platform | Location |
| --- | --- |
| Linux | `~/.local/share/handshakelab/captures/` |
| macOS | `~/Library/Application Support/handshakelab/captures/` |

Each run folder contains:

- `capture.pcapng` — raw evidence
- `crack.22000` — hashcat input
- `crack.log` — hashcat output
- `meta.json` — run metadata
- `report.md` — optional QA report

---

## Troubleshooting

| Problem | Fix |
| --- | --- |
| `Capture requires root` | Prefix with `sudo` |
| `Target not in allow-list` | Add SSID to `lab.toml` |
| `No EAPOL handshake` | Wait for a device to connect to the AP during capture; extend `--duration` |
| `hcxdumptool not found` | `apt install hcxdumptool` or `brew install hcxtools` |
| macOS empty capture | Use `import` with Wireshark, or USB adapter + hcxdumptool |

---

## Legal

Authorized testing only. See [`LEGAL_AND_ETHICS.md`](LEGAL_AND_ETHICS.md).
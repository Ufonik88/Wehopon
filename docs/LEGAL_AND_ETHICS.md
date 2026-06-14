# HandshakeLab — Legal & Ethics Policy

**Read this before installing or running capture commands.**

---

## Purpose

HandshakeLab exists for **authorized security testing and product quality assurance** on wireless equipment and networks where you have **explicit permission** to test.

It is designed to:

- Reduce load on access points during credential testing (offline cracking).
- Produce auditable artifacts for QA records.
- Support validation of WPA implementations in lab environments.

---

## Authorized use

You may use HandshakeLab when **all** of the following are true:

1. You own the access point / router under test, **or**
2. You have **written authorization** from the network owner (ticket, contract, signed scope), **and**
3. Testing stays within the physical lab or designated test facility, **and**
4. Targets are listed in your `lab.toml` allow-list.

### Examples of authorized use

- Ajax Systems QA bench testing WiFi cameras with a known-weak provisioning password.
- Pre-sales demo kit verification before shipping to a customer.
- Penetration test engagement with signed rules of engagement.

### Examples of prohibited use

- Capturing handshakes at coffee shops, airports, hotels, neighbors.
- Cracking networks to obtain free internet access.
- Testing client infrastructure without written scope.
- Using captured credentials to access systems beyond the test plan.

---

## Legal notice

Unauthorized interception of communications and unauthorized access to computer systems is criminal in many countries, including but not limited to:

- **South Africa:** Electronic Communications and Transactions Act (ECTA), Criminal Law Amendment Act
- **United Kingdom:** Computer Misuse Act 1990
- **United States:** Computer Fraud and Abuse Act (CFAA)
- **EU:** national implementations of EU Directive 2013/40/EU

**You are solely responsible for compliance with applicable law.**

The authors and maintainers of HandshakeLab provide tooling for legitimate security research and product testing. Misuse is not endorsed.

---

## Technical safeguards in the software

| Safeguard | Description |
| --- | --- |
| Allow-list | `lab.toml` must list SSID/BSSID before capture |
| `--ack-authorized` | Interactive acknowledgment required |
| No auto-join | Tool never connects to cracked networks automatically |
| Audit trail | Runs logged with operator, timestamp, BSSID |
| Deauth off by default | Reduces risk of disruptive testing |

---

## Controlled deauthentication (optional, lab only)

Forcing a 4-way handshake sometimes requires a **deauthentication frame** when no clients are actively associating. This can disrupt WiFi briefly on the target channel.

**Policy:**

- Disabled by default (`deauth_enabled = false` in `lab.toml`).
- Enable only on isolated lab APs with no production clients.
- Document in QA report when deauth was used.

---

## Data handling

- Capture files may contain identifiable BSSIDs and frame metadata.
- Store artifacts on encrypted lab disks where policy requires.
- Do not commit captures, wordlists, or passphrases to git.
- Delete captures after QA retention period per company policy.

---

## Acknowledgment

By running `handshakelab capture` with `--ack-authorized`, you confirm:

> I have authorization to test the target network(s) defined in my lab configuration. I will not use HandshakeLab on networks I do not own or have permission to test.

---

*If you are unsure whether your use case is authorized, stop and obtain written approval from the network owner and your legal/compliance team.*
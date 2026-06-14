import struct
from pathlib import Path

from handshakelab.eapol import _analyze_pcap_builtin, _frame_has_eapol


def _make_pcap_with_eapol(tmp_path: Path) -> Path:
    path = tmp_path / "test.pcap"
    # PCAP little-endian, snaplen 65535
    global_hdr = struct.pack("<IHHIIII", 0xA1B2C3D4, 2, 4, 0, 0, 65535, 1)
    # EAPOL ethernet frame
    frame = b"\xff" * 6 + b"\x00" * 6 + struct.pack("!H", 0x888E) + b"\x01\x02\x03"
    pkt_hdr = struct.pack("<IIII", 0, 0, len(frame), len(frame))
    path.write_bytes(global_hdr + pkt_hdr + frame)
    return path


def test_frame_has_eapol():
    frame = b"\xff" * 6 + b"\x00" * 6 + b"\x88\x8e" + b"data"
    assert _frame_has_eapol(frame)


def test_analyze_builtin_pcap(tmp_path: Path):
    pcap = _make_pcap_with_eapol(tmp_path)
    analysis = _analyze_pcap_builtin(pcap, pcap.stat().st_size)
    assert analysis.total_packets >= 1
    assert analysis.has_handshake
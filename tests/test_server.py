from fastapi.testclient import TestClient

from handshakelab.server import create_app


def test_health_endpoint():
    client = TestClient(create_app())
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert "version" in data
    assert "platform" in data


def test_index_html():
    client = TestClient(create_app())
    res = client.get("/")
    assert res.status_code == 200
    assert "HandshakeLab" in res.text


def test_autocrack_requires_ack():
    client = TestClient(create_app())
    res = client.post(
        "/api/autocrack",
        json={
            "iface": "wlan0",
            "ssid": "Test",
            "bssid": "AA:BB:CC:DD:EE:FF",
            "ack_authorized": False,
        },
    )
    assert res.status_code == 400

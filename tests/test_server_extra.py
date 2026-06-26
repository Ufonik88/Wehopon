"""Tests for handshakelab.server — FastAPI web server endpoints."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from handshakelab.pipeline import JobStatus, jobs
from handshakelab.server import create_app


@pytest.fixture
def client():
    return TestClient(create_app())


def test_health_endpoint(client):
    """GET /api/health returns 200 with health info."""
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert "version" in data
    assert "platform" in data
    assert "doctor_ok" in data
    assert "ai_available" in data
    assert "lab" in data
    assert "checks" in data


def test_health_endpoint_with_config_path():
    """GET /api/health with a config_path works."""
    client = TestClient(create_app(config_path=Path("/tmp/lab.toml")))
    res = client.get("/api/health")
    assert res.status_code == 200


def test_interfaces_endpoint(client):
    """GET /api/interfaces returns list of interface names."""
    res = client.get("/api/interfaces")
    assert res.status_code == 200
    data = res.json()
    assert "interfaces" in data
    assert "default" in data
    assert isinstance(data["interfaces"], list)


def test_interfaces_includes_default_even_if_missing():
    """Default interface from config is prepended even if not in ifconfig."""
    with patch("handshakelab.server.list_interfaces", return_value=["en1"]):
        with patch("handshakelab.server.load_config") as mock_load:
            from handshakelab.config import CaptureConfig, LabConfig
            mock_load.return_value = LabConfig(
                path=Path("/tmp/lab.toml"),
                capture=CaptureConfig(default_adapter="wlan99"),
            )
            client = TestClient(create_app())
            res = client.get("/api/interfaces")
            data = res.json()
            assert "wlan99" in data["interfaces"]
            assert data["interfaces"][0] == "wlan99"


def test_scan_endpoint(client):
    """POST /api/scan returns networks."""
    from handshakelab.util.wifi import Network

    with patch("handshakelab.server.scan_networks") as mock_scan:
        mock_scan.return_value = [
            Network(
                ssid="LAB-AP",
                bssid="AA:BB:CC:DD:EE:FF",
                channel=6,
                rssi=-50,
                security="WPA2",
            )
        ]
        res = client.post("/api/scan", json={"iface": "en0"})
        assert res.status_code == 200
        data = res.json()
        assert data["iface"] == "en0"
        assert data["count"] == 1
        assert data["networks"][0]["ssid"] == "LAB-AP"


def test_scan_endpoint_empty(client):
    """POST /api/scan with no networks returns empty list."""
    with patch("handshakelab.server.scan_networks", return_value=[]):
        res = client.post("/api/scan", json={"iface": "en0"})
        assert res.status_code == 200
        data = res.json()
        assert data["count"] == 0
        assert data["networks"] == []


def test_autocrack_requires_authorization(client):
    """POST /api/autocrack without ack_authorized returns 400."""
    res = client.post(
        "/api/autocrack",
        json={
            "iface": "en0",
            "ssid": "Test",
            "bssid": "AA:BB:CC:DD:EE:FF",
            "ack_authorized": False,
        },
    )
    assert res.status_code == 400
    assert "authorization" in res.json()["detail"].lower()


def test_autocrack_creates_job(client):
    """POST /api/autocrack with ack_authorized returns job info."""
    with patch("handshakelab.server.start_auto_pipeline") as mock_start:
        # Make start_auto_pipeline return a fake job
        from handshakelab.pipeline import jobs as job_mgr

        job = job_mgr.create(ssid="Test", bssid="AA:BB:CC:DD:EE:FF")
        mock_start.return_value = job

        res = client.post(
            "/api/autocrack",
            json={
                "iface": "en0",
                "ssid": "Test",
                "bssid": "AA:BB:CC:DD:EE:FF",
                "channel": 6,
                "ack_authorized": True,
                "use_ai": False,
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["ssid"] == "Test"
        assert data["bssid"] == "AA:BB:CC:DD:EE:FF"


def test_get_job_404(client):
    """GET /api/job/<unknown> returns 404."""
    res = client.get("/api/job/nonexistent-id")
    assert res.status_code == 404


def test_get_job_success(client):
    """GET /api/job/<id> returns the job dict."""
    job = jobs.create(ssid="LAB", bssid="AA:BB:CC:DD:EE:FF")
    res = client.get(f"/api/job/{job.id}")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == job.id
    assert data["ssid"] == "LAB"


def test_job_events_404(client):
    """GET /api/job/<unknown>/events returns 404."""
    res = client.get("/api/job/nonexistent-id/events")
    assert res.status_code == 404


def test_job_events_stream_terminates_on_completion(client):
    """GET /api/job/<id>/events returns SSE stream and terminates on completion."""
    job = jobs.create()
    job.status = JobStatus.SUCCESS
    res = client.get(f"/api/job/{job.id}/events")
    assert res.status_code == 200
    # Read the SSE stream
    text = res.text
    assert "data:" in text
    # payload is JSON
    for line in text.splitlines():
        if line.startswith("data:"):
            payload = json.loads(line.split(":", 1)[1].strip())
            assert "id" in payload


def test_index_serves_html(client):
    """GET / serves the index.html page."""
    res = client.get("/")
    assert res.status_code == 200
    assert "HandshakeLab" in res.text


def test_create_app_returns_fastapi():
    """create_app() returns a FastAPI instance."""
    from fastapi import FastAPI

    app = create_app()
    assert isinstance(app, FastAPI)


def test_ai_available_reflected_in_health(client):
    """ai_available value reflects HANDSHAKELAB_AI_API_KEY env."""
    import os

    with patch.dict(os.environ, {"HANDSHAKELAB_AI_API_KEY": "test-key"}):
        res = client.get("/api/health")
        assert res.json()["ai_available"] is True


def test_doctor_ok_reflects_health(client):
    """doctor_ok in /api/health is a boolean."""
    res = client.get("/api/health")
    assert isinstance(res.json()["doctor_ok"], bool)

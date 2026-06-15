"""Tests for the auto-crack pipeline orchestration."""

import time

from handshakelab.pipeline import JobManager, JobStatus, start_auto_pipeline
from handshakelab.util.wifi import Network


def test_job_manager_lifecycle():
    mgr = JobManager()
    job = mgr.create(ssid="LAB", bssid="00:11:22:33:44:55", channel=6)
    assert job.status == JobStatus.PENDING

    mgr.update(job.id, status=JobStatus.RUNNING, stage="capture", percent=42)
    loaded = mgr.get(job.id)
    assert loaded is not None
    assert loaded.status == JobStatus.RUNNING
    assert loaded.percent == 42
    assert loaded.stage == "capture"

    mgr.append_log(job.id, "tick 1")
    mgr.append_log(job.id, "tick 2")
    assert mgr.get(job.id).logs == ["tick 1", "tick 2"]


def test_job_to_dict_roundtrip():
    mgr = JobManager()
    job = mgr.create(ssid="LAB")
    mgr.update(job.id, capture_packets=10, capture_eapol=2, capture_backend="tcpdump")
    data = job.to_dict()
    assert data["ssid"] == "LAB"
    assert data["capture_packets"] == 10
    assert data["capture_eapol"] == 2
    assert data["capture_backend"] == "tcpdump"
    assert data["status"] == "pending"


def test_start_auto_pipeline_emits_job():
    net = Network(ssid="S", bssid="00:11:22:33:44:55", channel=6, rssi=-50, security="WPA2")
    job = start_auto_pipeline(
        iface="wlan0",
        network=net,
        duration_sec=1,
        ack_authorized=True,
        use_ai=False,
    )
    # Job is returned immediately and starts in PENDING or RUNNING
    assert job.ssid == "S"
    assert job.bssid == "00:11:22:33:44:55"
    # Wait briefly for the thread to settle (it will fail on the missing root check)
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        if job.status in (JobStatus.SUCCESS, JobStatus.FAILED):
            break
        time.sleep(0.05)
    assert job.status == JobStatus.FAILED  # no root, no monitor mode in test env

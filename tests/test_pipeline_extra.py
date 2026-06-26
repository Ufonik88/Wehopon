"""Tests for handshakelab.pipeline — auto-crack pipeline."""

from __future__ import annotations

import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from handshakelab.config import LabConfig
from handshakelab.crack_enhanced import EnhancedCrackResult
from handshakelab.eapol import CaptureAnalysis
from handshakelab.pipeline import (
    Job,
    JobManager,
    JobStatus,
    jobs,
    run_auto_pipeline,
    start_auto_pipeline,
)
from handshakelab.util.wifi import Network


@pytest.fixture(autouse=True)
def _clear_jobs():
    """Reset the global JobManager between tests."""
    jobs._jobs.clear()
    yield
    jobs._jobs.clear()


def _wait_for_job(job_id: str, timeout: float = 2.0) -> Job | None:
    """Poll job status until it leaves PENDING/RUNNING or timeout."""
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        j = jobs.get(job_id)
        if j and j.status in (JobStatus.SUCCESS, JobStatus.FAILED):
            return j
        time.sleep(0.01)
    return jobs.get(job_id)


def test_job_status_enum_values():
    """JobStatus enum has expected values."""
    assert JobStatus.PENDING.value == "pending"
    assert JobStatus.RUNNING.value == "running"
    assert JobStatus.SUCCESS.value == "success"
    assert JobStatus.FAILED.value == "failed"


def test_job_to_dict_default():
    """Job.to_dict() returns all fields with sensible defaults."""
    job = Job(id="abc")
    d = job.to_dict()
    assert d["id"] == "abc"
    assert d["status"] == "pending"
    assert d["stage"] == "queued"
    assert d["percent"] == 0
    assert d["logs"] == []
    assert d["capture_packets"] == 0
    assert d["capture_eapol"] == 0
    assert "created_at" in d


def test_job_to_dict_truncates_logs():
    """Job.to_dict() only returns the last 50 logs."""
    job = Job(id="abc")
    job.logs = [f"line {i}" for i in range(100)]
    d = job.to_dict()
    assert len(d["logs"]) == 50
    assert d["logs"][0] == "line 50"
    assert d["logs"][-1] == "line 99"


def test_job_manager_create():
    """JobManager.create() creates and stores a new job."""
    mgr = JobManager()
    job = mgr.create(ssid="LAB", bssid="AA:BB:CC:DD:EE:FF")
    assert job.id is not None
    assert mgr.get(job.id) is job
    assert job.ssid == "LAB"


def test_job_manager_get_nonexistent():
    """JobManager.get() returns None for unknown job_id."""
    mgr = JobManager()
    assert mgr.get("nonexistent") is None


def test_job_manager_update():
    """JobManager.update() modifies fields of an existing job."""
    mgr = JobManager()
    job = mgr.create()
    mgr.update(job.id, status=JobStatus.RUNNING, percent=50)
    assert mgr.get(job.id).status == JobStatus.RUNNING
    assert mgr.get(job.id).percent == 50


def test_job_manager_update_missing_job_is_noop():
    """JobManager.update() with unknown job_id is a no-op."""
    mgr = JobManager()
    mgr.update("nope", status=JobStatus.SUCCESS)  # no error


def test_job_manager_append_log():
    """JobManager.append_log() appends to the job's logs."""
    mgr = JobManager()
    job = mgr.create()
    mgr.append_log(job.id, "line 1")
    mgr.append_log(job.id, "line 2")
    assert mgr.get(job.id).logs == ["line 1", "line 2"]


def test_job_manager_append_log_missing_job():
    """JobManager.append_log() with unknown job_id is a no-op."""
    mgr = JobManager()
    mgr.append_log("nope", "x")  # no error


def test_start_auto_pipeline_creates_job():
    """start_auto_pipeline() creates a PENDING job and starts a thread."""
    network = Network(ssid="LAB", bssid="AA:BB:CC:DD:EE:FF", channel=6, rssi=-50, security="WPA2")
    cfg = LabConfig(path=Path("/tmp/lab.toml"), require_authorization=False)

    with patch("handshakelab.pipeline.run_auto_pipeline"):
        job = start_auto_pipeline(
            iface="en0", network=network, config=cfg, ack_authorized=True
        )
    assert job.status == JobStatus.PENDING
    assert job.ssid == "LAB"
    assert job.bssid == "AA:BB:CC:DD:EE:FF"
    assert job.channel == 6


def test_run_auto_pipeline_with_missing_job():
    """run_auto_pipeline returns silently if job_id doesn't exist."""
    cfg = LabConfig(path=Path("/tmp/lab.toml"), require_authorization=False)
    network = Network(ssid="X", bssid=None, channel=1, rssi=-50, security="WPA2")
    # Should not raise
    run_auto_pipeline("nonexistent", iface="en0", network=network, config=cfg)


def test_run_auto_pipeline_success_path():
    """run_auto_pipeline runs through capture → convert → crack successfully."""
    network = Network(ssid="LAB-AP", bssid="AA:BB:CC:DD:EE:FF", channel=6, rssi=-50, security="WPA2")
    cfg = LabConfig(path=Path("/tmp/lab.toml"), require_authorization=False)

    fake_cap = MagicMock()
    fake_cap.run_id = "test-run-1"
    fake_cap.backend = "tcpdump"
    fake_cap.analysis = CaptureAnalysis(100, 4, 50, 50, True, 4096)

    fake_conv = MagicMock()
    fake_conv.hash_count = 1

    fake_crack = EnhancedCrackResult(
        success=True, passphrase="recovered", method="hashcat:22000:ssid", stages_run=1
    )

    job = jobs.create(ssid=network.ssid, bssid=network.bssid, channel=network.channel)

    with (
        patch("handshakelab.pipeline.capture_handshake", return_value=fake_cap),
        patch("handshakelab.pipeline.convert_run", return_value=fake_conv),
        patch("handshakelab.pipeline.enhanced_crack", return_value=fake_crack),
    ):
        run_auto_pipeline(
            job.id, iface="en0", network=network, config=cfg, ack_authorized=True, use_ai=False
        )
        # Wait for completion
        time.sleep(0.1)

    final = jobs.get(job.id)
    assert final.status == JobStatus.SUCCESS
    assert final.password == "recovered"
    assert final.method == "hashcat:22000:ssid"
    assert final.run_id == "test-run-1"
    # log should mention success
    assert any("SUCCESS" in log for log in final.logs)


def test_run_auto_pipeline_failure_path():
    """run_auto_pipeline marks job FAILED when crack doesn't recover password."""
    network = Network(ssid="LAB", bssid=None, channel=1, rssi=-50, security="WPA2")
    cfg = LabConfig(path=Path("/tmp/lab.toml"), require_authorization=False)

    fake_cap = MagicMock()
    fake_cap.run_id = "r1"
    fake_cap.backend = "tcpdump"
    fake_cap.analysis = CaptureAnalysis(50, 0, 0, 0, False, 1024)

    fake_conv = MagicMock()
    fake_conv.hash_count = 0

    fake_crack = EnhancedCrackResult(
        success=False, passphrase=None, method="", stages_run=1
    )

    job = jobs.create()

    with (
        patch("handshakelab.pipeline.capture_handshake", return_value=fake_cap),
        patch("handshakelab.pipeline.convert_run", return_value=fake_conv),
        patch("handshakelab.pipeline.enhanced_crack", return_value=fake_crack),
    ):
        run_auto_pipeline(job.id, iface="en0", network=network, config=cfg)
        time.sleep(0.1)

    final = jobs.get(job.id)
    assert final.status == JobStatus.FAILED
    assert final.error == "No password match"


def test_run_auto_pipeline_capture_error():
    """run_auto_pipeline marks FAILED on CaptureError."""
    from handshakelab.capture import CaptureError

    network = Network(ssid="LAB", bssid=None, channel=1, rssi=-50, security="WPA2")
    cfg = LabConfig(path=Path("/tmp/lab.toml"), require_authorization=False)

    job = jobs.create()

    with patch(
        "handshakelab.pipeline.capture_handshake",
        side_effect=CaptureError("adapter down"),
    ):
        run_auto_pipeline(job.id, iface="en0", network=network, config=cfg)
        time.sleep(0.1)

    final = jobs.get(job.id)
    assert final.status == JobStatus.FAILED
    assert "adapter down" in final.error
    assert any("ERROR" in log for log in final.logs)


def test_run_auto_pipeline_authorization_error():
    """run_auto_pipeline marks FAILED on AuthorizationError."""
    from handshakelab.legal import AuthorizationError

    network = Network(ssid="UNAUTHORIZED", bssid=None, channel=1, rssi=-50, security="WPA2")
    cfg = LabConfig(path=Path("/tmp/lab.toml"), require_authorization=True)

    job = jobs.create()

    with patch(
        "handshakelab.pipeline.capture_handshake",
        side_effect=AuthorizationError("not authorized"),
    ):
        run_auto_pipeline(job.id, iface="en0", network=network, config=cfg)
        time.sleep(0.1)

    final = jobs.get(job.id)
    assert final.status == JobStatus.FAILED
    assert "not authorized" in final.error


def test_run_auto_pipeline_unexpected_error():
    """run_auto_pipeline catches generic exceptions and marks FAILED."""
    network = Network(ssid="LAB", bssid=None, channel=1, rssi=-50, security="WPA2")
    cfg = LabConfig(path=Path("/tmp/lab.toml"), require_authorization=False)

    job = jobs.create()

    with patch(
        "handshakelab.pipeline.capture_handshake",
        side_effect=RuntimeError("something exploded"),
    ):
        run_auto_pipeline(job.id, iface="en0", network=network, config=cfg)
        time.sleep(0.1)

    final = jobs.get(job.id)
    assert final.status == JobStatus.FAILED
    assert "something exploded" in final.error


def test_run_auto_pipeline_logs_progress():
    """run_auto_pipeline appends progress logs to the job."""
    network = Network(ssid="LAB", bssid=None, channel=1, rssi=-50, security="WPA2")
    cfg = LabConfig(path=Path("/tmp/lab.toml"), require_authorization=False)

    fake_cap = MagicMock()
    fake_cap.run_id = "r1"
    fake_cap.backend = "tcpdump"
    fake_cap.analysis = CaptureAnalysis(10, 2, 0, 0, True, 1024)

    fake_conv = MagicMock()
    fake_conv.hash_count = 1

    fake_crack = EnhancedCrackResult(
        success=True, passphrase="pw", method="x", stages_run=1
    )

    job = jobs.create()
    with (
        patch("handshakelab.pipeline.capture_handshake", return_value=fake_cap),
        patch("handshakelab.pipeline.convert_run", return_value=fake_conv),
        patch("handshakelab.pipeline.enhanced_crack", return_value=fake_crack),
    ):
        run_auto_pipeline(job.id, iface="en0", network=network, config=cfg)
        time.sleep(0.1)

    final = jobs.get(job.id)
    # At least the auth and success logs
    log_text = "\n".join(final.logs)
    assert "auth" in log_text
    assert "SUCCESS" in log_text

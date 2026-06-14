"""Fully automated scan → capture → convert → enhanced crack pipeline."""

from __future__ import annotations

import threading
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from handshakelab.capture import CaptureError, capture_handshake
from handshakelab.config import LabConfig, load_config
from handshakelab.convert import ConvertError, convert_run
from handshakelab.crack_enhanced import enhanced_crack
from handshakelab.legal import AuthorizationError
from handshakelab.util.wifi import Network

ProgressFn = Callable[[dict[str, Any]], None]


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


@dataclass
class Job:
    id: str
    status: JobStatus = JobStatus.PENDING
    stage: str = "queued"
    message: str = "Waiting…"
    percent: int = 0
    ssid: str = ""
    bssid: str | None = None
    channel: int | None = None
    run_id: str | None = None
    password: str | None = None
    method: str | None = None
    error: str | None = None
    logs: list[str] = field(default_factory=list)
    capture_packets: int = 0
    capture_eapol: int = 0
    capture_backend: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "status": self.status.value,
            "stage": self.stage,
            "message": self.message,
            "percent": self.percent,
            "ssid": self.ssid,
            "bssid": self.bssid,
            "channel": self.channel,
            "run_id": self.run_id,
            "password": self.password,
            "method": self.method,
            "error": self.error,
            "logs": self.logs[-50:],
            "capture_packets": self.capture_packets,
            "capture_eapol": self.capture_eapol,
            "capture_backend": self.capture_backend,
            "created_at": self.created_at,
        }


class JobManager:
    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()

    def get(self, job_id: str) -> Job | None:
        with self._lock:
            return self._jobs.get(job_id)

    def create(self, **kwargs: Any) -> Job:
        job = Job(id=str(uuid.uuid4()), **kwargs)
        with self._lock:
            self._jobs[job.id] = job
        return job

    def update(self, job_id: str, **kwargs: Any) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return
            for k, v in kwargs.items():
                setattr(job, k, v)

    def append_log(self, job_id: str, line: str) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                job.logs.append(line)


# Global singleton for local UI server
jobs = JobManager()


def run_auto_pipeline(
    job_id: str,
    *,
    iface: str,
    network: Network,
    config: LabConfig | None = None,
    duration_sec: int | None = None,
    ack_authorized: bool = True,
    use_ai: bool = True,
) -> None:
    cfg = config or load_config(None)
    job = jobs.get(job_id)
    if not job:
        return

    def progress(stage: str, message: str, percent: int) -> None:
        jobs.update(job_id, stage=stage, message=message, percent=percent, status=JobStatus.RUNNING)
        jobs.append_log(job_id, f"[{percent}%] {stage}: {message}")

    try:
        jobs.update(job_id, status=JobStatus.RUNNING, stage="auth", message="Checking authorization…", percent=5)
        progress("auth", f"Target: {network.ssid}", 8)

        jobs.update(
            job_id,
            stage="capture",
            message="Built-in sniffer listening (you do NOT join the network)…",
            percent=12,
        )

        def on_capture_tick(analysis, msg: str) -> None:
            jobs.update(
                job_id,
                capture_packets=analysis.total_packets,
                capture_eapol=analysis.eapol_frames,
                message=msg,
                percent=min(12 + int(23 * (analysis.eapol_frames / 4)), 34),
            )
            jobs.append_log(job_id, msg)

        cap = capture_handshake(
            iface=iface,
            ssid=network.ssid,
            config=cfg,
            bssid=network.bssid,
            channel=network.channel,
            duration_sec=duration_sec or cfg.capture.default_duration_sec,
            ack_authorized=ack_authorized,
            on_tick=on_capture_tick,
        )
        jobs.update(
            job_id,
            run_id=cap.run_id,
            percent=35,
            message="Handshake captured",
            capture_packets=cap.analysis.total_packets,
            capture_eapol=cap.analysis.eapol_frames,
            capture_backend=cap.backend,
        )
        progress(
            "capture",
            f"{cap.backend}: {cap.analysis.eapol_frames} EAPOL frames in {cap.analysis.total_packets} packets",
            35,
        )

        jobs.update(job_id, stage="convert", message="Converting to Hashcat format…", percent=42)
        conv = convert_run(cap.run_id)
        progress("convert", f"{conv.hash_count} hash(es) ready", 50)

        def crack_progress(stage: str, msg: str, pct: int) -> None:
            progress(stage, msg, pct)

        jobs.update(job_id, stage="crack", message="Running enhanced offline attacks…", percent=55)
        result = enhanced_crack(cap.run_id, cfg, use_ai=use_ai, on_progress=crack_progress)

        if result.success and result.passphrase:
            jobs.update(
                job_id,
                status=JobStatus.SUCCESS,
                stage="done",
                message="Password recovered",
                percent=100,
                password=result.passphrase,
                method=result.method,
            )
            jobs.append_log(job_id, f"SUCCESS: {result.passphrase}")
        else:
            jobs.update(
                job_id,
                status=JobStatus.FAILED,
                stage="done",
                message="Could not crack with available wordlists",
                percent=100,
                error="No password match",
            )
    except (CaptureError, ConvertError, AuthorizationError) as exc:
        jobs.update(
            job_id,
            status=JobStatus.FAILED,
            stage="error",
            message=str(exc),
            error=str(exc),
        )
        jobs.append_log(job_id, f"ERROR: {exc}")
    except Exception as exc:  # noqa: BLE001 — surface to UI
        jobs.update(
            job_id,
            status=JobStatus.FAILED,
            stage="error",
            message=str(exc),
            error=str(exc),
        )
        jobs.append_log(job_id, f"ERROR: {exc}")


def start_auto_pipeline(**kwargs: Any) -> Job:
    network: Network = kwargs.pop("network")
    job = jobs.create(
        ssid=network.ssid,
        bssid=network.bssid,
        channel=network.channel,
        status=JobStatus.PENDING,
    )
    thread = threading.Thread(
        target=run_auto_pipeline,
        kwargs={"job_id": job.id, "network": network, **kwargs},
        daemon=True,
    )
    thread.start()
    return job
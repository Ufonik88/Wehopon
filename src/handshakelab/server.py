"""Local web UI server — localhost only."""

from __future__ import annotations

import asyncio
import json
import webbrowser
from pathlib import Path
from typing import Any, AsyncIterator

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from handshakelab import __version__
from handshakelab.ai_wordlist import ai_available
from handshakelab.config import load_config
from handshakelab.doctor import run_doctor
from handshakelab.pipeline import JobStatus, jobs, start_auto_pipeline
from handshakelab.util import platform as plat
from handshakelab.util.wifi import Network, list_interfaces, scan_networks

WEB_DIR = Path(__file__).parent / "web"


class ScanRequest(BaseModel):
    iface: str


class AutoCrackRequest(BaseModel):
    iface: str
    ssid: str
    bssid: str
    channel: int | None = None
    ack_authorized: bool = False
    use_ai: bool = True
    duration_sec: int | None = None


def create_app(config_path: Path | None = None) -> FastAPI:
    app = FastAPI(title="HandshakeLab", version=__version__)
    cfg_path = config_path

    @app.get("/api/health")
    def health() -> dict[str, Any]:
        config = load_config(cfg_path)
        checks, ok = run_doctor(iface=config.capture.default_adapter, config_path=cfg_path)
        return {
            "version": __version__,
            "platform": plat.platform_label(),
            "doctor_ok": ok,
            "ai_available": ai_available(),
            "require_authorization": config.require_authorization,
            "lab": {
                "name": config.name,
                "operator": config.operator,
                "default_adapter": config.capture.default_adapter,
                "default_duration_sec": config.capture.default_duration_sec,
                "ui_port": config.ui.default_port,
            },
            "checks": [{"name": c.name, "ok": c.ok, "detail": c.detail} for c in checks],
        }

    @app.get("/api/interfaces")
    def interfaces() -> dict[str, list[str] | str | None]:
        ifaces: list[str] = list_interfaces()
        config = load_config(cfg_path)
        default = config.capture.default_adapter
        if default and default not in ifaces:
            ifaces = [default, *ifaces]
        return {"interfaces": ifaces, "default": default}

    @app.post("/api/scan")
    def scan(req: ScanRequest) -> dict[str, Any]:
        networks = scan_networks(req.iface)
        return {
            "iface": req.iface,
            "count": len(networks),
            "networks": [
                {
                    "ssid": n.ssid,
                    "bssid": n.bssid,
                    "channel": n.channel,
                    "rssi": n.rssi,
                    "security": n.security,
                }
                for n in networks
            ],
        }

    @app.post("/api/autocrack")
    def autocrack(req: AutoCrackRequest) -> dict[str, Any]:
        if not req.ack_authorized:
            raise HTTPException(
                400,
                "You must confirm authorization to test this network.",
            )
        network = Network(
            ssid=req.ssid,
            bssid=req.bssid,
            channel=req.channel,
            rssi=None,
            security="unknown",
        )
        config = load_config(cfg_path)
        job = start_auto_pipeline(
            iface=req.iface,
            network=network,
            config=config,
            duration_sec=req.duration_sec,
            ack_authorized=True,
            use_ai=req.use_ai,
        )
        return job.to_dict()

    @app.get("/api/job/{job_id}")
    def get_job(job_id: str) -> dict[str, Any]:
        job = jobs.get(job_id)
        if not job:
            raise HTTPException(404, "Job not found")
        return job.to_dict()

    @app.get("/api/job/{job_id}/events")
    async def job_events(job_id: str) -> StreamingResponse:
        job = jobs.get(job_id)
        if not job:
            raise HTTPException(404, "Job not found")

        async def stream() -> AsyncIterator[str]:
            last_len = 0
            while True:
                j = jobs.get(job_id)
                if not j:
                    break
                payload = j.to_dict()
                if len(j.logs) > last_len:
                    payload["new_logs"] = j.logs[last_len:]
                    last_len = len(j.logs)
                else:
                    payload["new_logs"] = []
                yield f"data: {json.dumps(payload)}\n\n"
                if j.status in (JobStatus.SUCCESS, JobStatus.FAILED):
                    break
                await asyncio.sleep(0.5)

        return StreamingResponse(stream(), media_type="text/event-stream")

    if WEB_DIR.exists():
        app.mount("/assets", StaticFiles(directory=WEB_DIR), name="assets")

        @app.get("/")
        def index() -> FileResponse:
            return FileResponse(WEB_DIR / "index.html")

    return app


def run_server(
    *,
    host: str = "127.0.0.1",
    port: int = 8765,
    config_path: Path | None = None,
    open_browser: bool = True,
) -> None:
    import uvicorn

    url = f"http://{host}:{port}"
    if open_browser:
        webbrowser.open(url)
    uvicorn.run(create_app(config_path), host=host, port=port, log_level="info")
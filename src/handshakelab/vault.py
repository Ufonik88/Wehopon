"""SQLite vault and per-run artifact directories."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from handshakelab.util import platform as plat


@dataclass
class RunRecord:
    id: str
    created_at: str
    operator: str
    ssid: str
    bssid: str | None
    channel: int | None
    adapter: str | None
    capture_path: str
    hash_path: str | None
    status: str
    authorized_by: str | None
    platform: str
    capture_sha256: str | None = None


@dataclass
class CrackResult:
    run_id: str
    cracked_at: str
    method: str
    duration_ms: int
    passphrase: str | None
    success: bool


SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
  id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL,
  operator TEXT,
  ssid TEXT,
  bssid TEXT,
  channel INTEGER,
  adapter TEXT,
  capture_path TEXT,
  hash_path TEXT,
  status TEXT,
  authorized_by TEXT,
  platform TEXT,
  capture_sha256 TEXT
);

CREATE TABLE IF NOT EXISTS crack_results (
  run_id TEXT PRIMARY KEY REFERENCES runs(id),
  cracked_at TEXT,
  method TEXT,
  duration_ms INTEGER,
  passphrase TEXT,
  success INTEGER
);
"""


class Vault:
    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or plat.vault_db_path()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        """Yield a sqlite3 connection, commit on clean exit, always close.

        The sqlite3 Connection `__exit__` only commits/rolls back; it does
        NOT close the connection. Without explicit close we leak file
        handles and get `ResourceWarning: unclosed database` in
        long-running processes and tests.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(SCHEMA)

    def create_run_dir(self, run_id: str | None = None) -> tuple[str, Path]:
        rid = run_id or str(uuid.uuid4())
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        path = plat.captures_dir() / f"{stamp}_{rid[:8]}"
        path.mkdir(parents=True, exist_ok=True)
        return rid, path

    def insert_run(self, record: RunRecord) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO runs (
                  id, created_at, operator, ssid, bssid, channel, adapter,
                  capture_path, hash_path, status, authorized_by, platform, capture_sha256
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.id,
                    record.created_at,
                    record.operator,
                    record.ssid,
                    record.bssid,
                    record.channel,
                    record.adapter,
                    record.capture_path,
                    record.hash_path,
                    record.status,
                    record.authorized_by,
                    record.platform,
                    record.capture_sha256,
                ),
            )

    def update_run_status(
        self,
        run_id: str,
        status: str,
        *,
        hash_path: str | None = None,
    ) -> None:
        with self._connect() as conn:
            if hash_path is not None:
                conn.execute(
                    "UPDATE runs SET status = ?, hash_path = ? WHERE id = ?",
                    (status, hash_path, run_id),
                )
            else:
                conn.execute("UPDATE runs SET status = ? WHERE id = ?", (status, run_id))

    def get_run(self, run_id: str) -> RunRecord | None:
        with self._connect() as conn:
            if run_id == "latest":
                row = conn.execute(
                    "SELECT * FROM runs ORDER BY created_at DESC LIMIT 1"
                ).fetchone()
            else:
                row = conn.execute(
                    "SELECT * FROM runs WHERE id = ? OR id LIKE ? ORDER BY created_at DESC LIMIT 1",
                    (run_id, f"{run_id}%"),
                ).fetchone()
        if not row:
            return None
        return RunRecord(**dict(row))

    def list_runs(self) -> list[RunRecord]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM runs ORDER BY created_at DESC").fetchall()
        return [RunRecord(**dict(r)) for r in rows]

    def save_crack_result(self, result: CrackResult) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO crack_results
                  (run_id, cracked_at, method, duration_ms, passphrase, success)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    result.run_id,
                    result.cracked_at,
                    result.method,
                    result.duration_ms,
                    result.passphrase,
                    int(result.success),
                ),
            )
            status = "cracked" if result.success else "failed"
            conn.execute("UPDATE runs SET status = ? WHERE id = ?", (status, result.run_id))

    def get_crack_result(self, run_id: str) -> CrackResult | None:
        run = self.get_run(run_id)
        if not run:
            return None
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM crack_results WHERE run_id = ?", (run.id,)
            ).fetchone()
        if not row:
            return None
        data = dict(row)
        return CrackResult(
            run_id=data["run_id"],
            cracked_at=data["cracked_at"],
            method=data["method"],
            duration_ms=data["duration_ms"],
            passphrase=data["passphrase"],
            success=bool(data["success"]),
        )

    def write_meta(self, run_dir: Path, meta: dict) -> Path:
        path = run_dir / "meta.json"
        path.write_text(json.dumps(meta, indent=2))
        return path


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def run_dir_for(record: RunRecord) -> Path:
    return Path(record.capture_path).parent
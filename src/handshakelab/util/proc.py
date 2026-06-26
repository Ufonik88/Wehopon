"""Subprocess helpers with logging."""

from __future__ import annotations

import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CommandResult:
    argv: list[str]
    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0


def which(name: str) -> str | None:
    from shutil import which as _which

    return _which(name)


def run(
    argv: list[str],
    *,
    timeout: int | None = None,
    cwd: Path | None = None,
    check: bool = False,
) -> CommandResult:
    proc = subprocess.run(
        argv,
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=str(cwd) if cwd else None,
    )
    result = CommandResult(
        argv=argv,
        returncode=proc.returncode,
        stdout=proc.stdout or "",
        stderr=proc.stderr or "",
    )
    if check and not result.ok:
        raise subprocess.CalledProcessError(
            proc.returncode,
            argv,
            output=proc.stdout,
            stderr=proc.stderr,
        )
    return result


def format_cmd(argv: list[str]) -> str:
    return " ".join(shlex.quote(a) for a in argv)

"""HandshakeLab CLI — Phase 1+ commands will be implemented per docs/PHASE_ROADMAP.md."""

from __future__ import annotations

import typer
from rich.console import Console

from handshakelab import __version__

app = typer.Typer(
    name="handshakelab",
    help="Offline WiFi handshake capture & crack for authorized product testing.",
    no_args_is_help=True,
)
console = Console()


@app.command()
def version() -> None:
    """Show installed version."""
    console.print(f"handshakelab {__version__}")


@app.command()
def doctor() -> None:
    """Preflight: verify toolchain and adapter (Phase 1 — not yet implemented)."""
    console.print("[yellow]Phase 1:[/yellow] `doctor` not implemented yet.")
    console.print("See docs/PHASE_ROADMAP.md and docs/HARDWARE.md.")
    raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
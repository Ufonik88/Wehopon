"""HandshakeLab CLI."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.table import Table

from handshakelab import __version__
from handshakelab.capture import CaptureError, capture_handshake, import_capture
from handshakelab.config import load_config
from handshakelab.convert import ConvertError, convert_file, convert_run
from handshakelab.crack import CrackError, crack_run
from handshakelab.doctor import run_doctor
from handshakelab.legal import AuthorizationError
from handshakelab.report import write_report
from handshakelab.util import platform as plat
from handshakelab.util.wifi import scan_networks
from handshakelab.vault import Vault

app = typer.Typer(
    name="handshakelab",
    help="Offline WiFi handshake capture & crack for authorized product testing.",
    no_args_is_help=True,
)
console = Console()


def _config_opt(config: Path | None) -> Path | None:
    if config and config.exists():
        return config
    if Path("lab.toml").exists():
        return Path("lab.toml")
    return config


def _version_callback(value: bool) -> None:
    if value:
        console.print(f"handshakelab {__version__} ({plat.platform_label()})")
        raise typer.Exit()


@app.callback()
def main(
    ctx: typer.Context,
    config: Annotated[
        Optional[Path],
        typer.Option("--config", "-c", help="Path to lab.toml"),
    ] = None,
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            callback=_version_callback,
            is_eager=True,
            help="Show installed version and exit.",
        ),
    ] = False,
) -> None:
    ctx.ensure_object(dict)
    ctx.obj["config"] = _config_opt(config)


@app.command()
def version() -> None:
    """Show installed version."""
    console.print(f"handshakelab {__version__} ({plat.platform_label()})")


@app.command()
def doctor(
    ctx: typer.Context,
    iface: Annotated[
        Optional[str],
        typer.Option("--interface", "-i", help="WiFi interface to check"),
    ] = None,
) -> None:
    """Preflight: verify toolchain, adapter, and lab.toml."""
    config_path = ctx.obj.get("config")
    checks, ok = run_doctor(iface=iface, config_path=config_path)

    table = Table(title="HandshakeLab Doctor")
    table.add_column("Check")
    table.add_column("Status")
    table.add_column("Detail")

    for check in checks:
        status = "[green]OK[/green]" if check.ok else "[red]FAIL[/red]"
        table.add_row(check.name, status, check.detail)

    console.print(table)
    if not ok:
        raise typer.Exit(code=1)


@app.command()
def scan(
    ctx: typer.Context,
    iface: Annotated[
        Optional[str],
        typer.Option("--interface", "-i", help="WiFi interface (defaults to lab.toml)"),
    ] = None,
) -> None:
    """Passively scan for nearby networks."""
    config = load_config(ctx.obj.get("config"))
    iface = iface or config.capture.default_adapter

    networks = scan_networks(iface)
    if not networks:
        console.print("[yellow]No networks found.[/yellow] Check interface name and permissions.")
        raise typer.Exit(code=1)

    table = Table(title=f"Networks on {iface}")
    table.add_column("SSID")
    table.add_column("BSSID")
    table.add_column("Ch")
    table.add_column("RSSI")
    table.add_column("Security")

    for net in networks:
        table.add_row(
            net.ssid,
            net.bssid,
            str(net.channel or ""),
            str(net.rssi or ""),
            net.security,
        )
    console.print(table)


@app.command()
def capture(
    ctx: typer.Context,
    ssid: Annotated[str, typer.Option("--ssid", "-s", help="Target SSID (authorized)")],
    iface: Annotated[
        Optional[str],
        typer.Option("--interface", "-i", help="WiFi interface (defaults to lab.toml)"),
    ] = None,
    bssid: Annotated[Optional[str], typer.Option("--bssid", "-b")] = None,
    channel: Annotated[Optional[int], typer.Option("--channel")] = None,
    duration: Annotated[
        Optional[int],
        typer.Option("--duration", "-d", help="Capture seconds"),
    ] = None,
    ack_authorized: Annotated[
        bool,
        typer.Option(
            "--ack-authorized",
            help="Confirm you are authorized to test this network",
        ),
    ] = False,
) -> None:
    """Capture WPA handshake to a local pcapng file (requires sudo)."""
    config = load_config(ctx.obj.get("config"))
    try:
        result = capture_handshake(
            iface=iface or config.capture.default_adapter,
            ssid=ssid,
            config=config,
            bssid=bssid,
            channel=channel,
            duration_sec=duration,
            ack_authorized=ack_authorized,
        )
    except (CaptureError, AuthorizationError) as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    console.print("[green]Capture saved.[/green]")
    console.print(f"  Run ID:  {result.run_id}")
    console.print(f"  File:    {result.capture_path}")
    console.print(f"  SSID:    {result.ssid}")
    console.print(f"  BSSID:   {result.bssid or 'auto'}")
    console.print(f"  Channel: {result.channel}")
    console.print("\nNext: handshakelab convert latest")


@app.command("import")
def import_cmd(
    ctx: typer.Context,
    file: Annotated[Path, typer.Argument(help="Existing .pcap / .pcapng / .cap file")],
    ssid: Annotated[str, typer.Option("--ssid", "-s")],
    iface: Annotated[
        Optional[str],
        typer.Option("--interface", "-i", help="Recorded on interface (for record)"),
    ] = None,
    bssid: Annotated[Optional[str], typer.Option("--bssid", "-b")] = None,
    channel: Annotated[Optional[int], typer.Option("--channel")] = None,
    ack_authorized: Annotated[bool, typer.Option("--ack-authorized")] = False,
) -> None:
    """Import an existing capture file (Linux/macOS — no live capture needed)."""
    config = load_config(ctx.obj.get("config"))
    try:
        result = import_capture(
            source=file,
            ssid=ssid,
            config=config,
            iface=iface or config.capture.default_adapter,
            bssid=bssid,
            channel=channel,
            ack_authorized=ack_authorized,
        )
    except (CaptureError, AuthorizationError) as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    console.print(f"[green]Imported[/green] → run {result.run_id}")
    console.print(f"  {result.capture_path}")
    console.print("\nNext: handshakelab convert latest")


@app.command()
def convert(
    ctx: typer.Context,
    target: Annotated[str, typer.Argument(help="Run ID, 'latest', or path to .pcapng")],
) -> None:
    """Convert capture to Hashcat .22000 hash file."""
    try:
        path = Path(target)
        if path.exists():
            result = convert_file(path)
        else:
            result = convert_run(target)
    except ConvertError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    console.print(f"[green]Converted[/green] {result.hash_count} hash(es)")
    console.print(f"  {result.hash_path}")
    console.print("\nNext: handshakelab crack latest --wordlist <file>")


@app.command()
def crack(
    ctx: typer.Context,
    run_id: Annotated[str, typer.Argument(help="Run ID or 'latest'")],
    wordlist: Annotated[
        Optional[Path],
        typer.Option("--wordlist", "-w", help="Wordlist path"),
    ] = None,
) -> None:
    """Crack offline with Hashcat (never contacts the AP)."""
    config = load_config(ctx.obj.get("config"))
    try:
        result = crack_run(run_id, wordlist=wordlist, crack_config=config.crack)
    except CrackError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    if result.success:
        console.print(f"[green]Cracked[/green] in {result.duration_ms} ms")
        console.print(f"  Passphrase: {'*' * min(8, len(result.passphrase or ''))}")
        console.print("  Use: handshakelab show latest --reveal")
    else:
        console.print("[yellow]No match[/yellow] in wordlist.")
        raise typer.Exit(code=2)


@app.command()
def show(
    run_id: Annotated[str, typer.Argument(help="Run ID or 'latest'")],
    reveal: Annotated[bool, typer.Option("--reveal", help="Show plaintext passphrase")] = False,
) -> None:
    """Display crack result (masked by default)."""
    vault = Vault()
    record = vault.get_run(run_id)
    if not record:
        console.print(f"[red]Run not found:[/red] {run_id}")
        raise typer.Exit(code=1)

    crack = vault.get_crack_result(record.id)
    console.print(f"Run:    {record.id}")
    console.print(f"SSID:   {record.ssid}")
    console.print(f"Status: {record.status}")

    if not crack:
        console.print("[yellow]Not cracked yet.[/yellow]")
        raise typer.Exit(code=1)

    if crack.success and crack.passphrase:
        if reveal:
            console.print(f"[green]Passphrase:[/green] {crack.passphrase}")
            console.print("\nEnter this manually on your device under test.")
        else:
            masked = "*" * len(crack.passphrase)
            console.print(f"Passphrase: {masked}  (use --reveal to show)")
    else:
        console.print("Passphrase: [not recovered]")


@app.command("list")
def list_runs() -> None:
    """List all vault runs."""
    vault = Vault()
    runs = vault.list_runs()
    if not runs:
        console.print("No runs yet.")
        return

    table = Table(title="Vault runs")
    table.add_column("ID")
    table.add_column("Created")
    table.add_column("SSID")
    table.add_column("Status")

    for run in runs:
        table.add_row(run.id[:8] + "…", run.created_at[:19], run.ssid, run.status)
    console.print(table)


@app.command()
def report(
    run_id: Annotated[str, typer.Argument(help="Run ID or 'latest'")],
    fmt: Annotated[
        str,
        typer.Option("--format", "-f", help="md or json"),
    ] = "md",
) -> None:
    """Generate QA report artifact."""
    if fmt not in ("md", "json"):
        console.print("[red]Format must be md or json[/red]")
        raise typer.Exit(code=1)
    try:
        path = write_report(run_id, fmt)
    except ValueError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1) from exc
    console.print(f"[green]Report written:[/green] {path}")


@app.command()
def ui(
    ctx: typer.Context,
    host: Annotated[str, typer.Option(help="Bind host")] = "127.0.0.1",
    port: Annotated[Optional[int], typer.Option(help="Port")] = None,
    open_browser: Annotated[bool, typer.Option("--open/--no-open")] = True,
) -> None:
    """Launch the local web UI (scan → select → auto-crack)."""
    from handshakelab.server import run_server

    config = load_config(ctx.obj.get("config"))
    run_server(
        host=host,
        port=port or config.ui.default_port,
        config_path=ctx.obj.get("config"),
        open_browser=open_browser,
    )


if __name__ == "__main__":
    app()

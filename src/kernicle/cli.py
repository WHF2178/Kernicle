"""Kernicle CLI (Sprint 1)."""

from __future__ import annotations

from datetime import timezone
from pathlib import Path
import platform

import typer
from rich.console import Console
from rich.table import Table

from kernicle import __version__
from kernicle.config import get_paths
from kernicle.services.archive import create_session, write_manifest, write_report, write_sources
from kernicle.services.journal import capture_kernel, capture_system
from kernicle.services.timeparse import parse_range


app = typer.Typer(add_completion=False, help="Kernicle reads the CHAOS; shows the CLARITY")
console = Console()


def _require_linux() -> None:
    if platform.system().lower() != "linux":
        raise typer.Exit(code=2)


@app.command()
def push(
    range: str = typer.Option(..., "--range", help="last:<n><s|m|h|d> OR ISO datetime like 2025-12-30T12:00:00Z"),
    kernel_only: bool = typer.Option(True, "--kernel-only/--all", help="Capture kernel-only (default) or kernel+system"),
) -> None:
    """Capture logs and write a structured session folder."""

    if platform.system().lower() != "linux":
        console.print("[bold red]Kernicle is Linux-only (systemd journal required).[/bold red]")
        console.print(f"Detected platform: {platform.system()}")
        raise typer.Exit(code=2)

    paths = get_paths()

    try:
        tr = parse_range(range)
    except ValueError as exc:
        console.print(f"[bold red]Invalid --range:[/bold red] {exc}")
        raise typer.Exit(code=2) from exc

    since_iso = tr.since_utc.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

    console.print("[bold]Kernicle[/bold] Sprint 1 capture")
    console.print(f"range_input: {tr.range_input}")
    console.print(f"since_utc:   {since_iso}")

    session = create_session(paths.archives_dir)

    warnings: list[str] = []
    errors: list[str] = []

    kernel_res = capture_kernel(since_arg=tr.since_arg)
    if not kernel_res.ok:
        msg = (
            f"journalctl kernel capture failed (rc={kernel_res.returncode}). "
            f"stderr: {kernel_res.stderr.strip() or '(empty)'}"
        )
        warnings.append(msg)

    system_log: str | None = None
    if not kernel_only:
        sys_res = capture_system(since_arg=tr.since_arg)
        system_log = sys_res.stdout
        if not sys_res.ok:
            msg = (
                f"journalctl system capture failed (rc={sys_res.returncode}). "
                f"stderr: {sys_res.stderr.strip() or '(empty)'}"
            )
            warnings.append(msg)

    sources_mapping = write_sources(
        session.sources_dir,
        kernel_log=kernel_res.stdout,
        system_log=system_log,
    )

    write_report(
        session.report_path,
        tool="kernicle",
        version=__version__,
        range_input=tr.range_input,
        since_utc_iso=since_iso,
        sources_mapping=sources_mapping,
        warnings=warnings,
    )

    write_manifest(
        session.manifest_path,
        tool="kernicle",
        version=__version__,
        range_input=tr.range_input,
        since_utc_iso=since_iso,
        kernel_only=kernel_only,
        sources_mapping=sources_mapping,
        warnings=warnings,
        errors=errors,
    )

    console.print("")
    console.print(f"Session written: [bold]{session.session_dir}[/bold]")
    console.print(f"- sources:   {session.sources_dir}")
    console.print(f"- report:    {session.report_path}")
    console.print(f"- manifest:  {session.manifest_path}")

    if warnings:
        console.print("")
        console.print("[yellow]Warnings were recorded in report/manifest.[/yellow]")
        console.print("If journalctl failed, try `sudo` or add user to `systemd-journal` group.")


@app.command()
def show(
    limit: int = typer.Option(10, "--limit", min=1, max=200, help="How many recent sessions to list"),
) -> None:
    """List recent sessions under ~/.kernicle/archives."""

    if platform.system().lower() != "linux":
        console.print("[bold red]Kernicle is Linux-only (systemd journal required).[/bold red]")
        console.print(f"Detected platform: {platform.system()}")
        raise typer.Exit(code=2)

    paths = get_paths()
    archives = paths.archives_dir

    sessions = [p for p in archives.iterdir() if p.is_dir() and p.name.startswith("session-")]
    sessions.sort(key=lambda p: p.name, reverse=True)
    sessions = sessions[:limit]

    table = Table(title="Kernicle sessions")
    table.add_column("Session", style="bold")
    table.add_column("Path")

    for s in sessions:
        table.add_row(s.name, str(s))

    if not sessions:
        console.print(f"No sessions found in {archives}")
        return

    console.print(table)

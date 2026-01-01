"""Session archive creation + writing.

Session layout (Sprint 1):
  ~/.kernicle/archives/session-<timestamp>/
    sources/
      journalctl-kernel.log
      journalctl-system.log  (only if --all)
    report.txt
    manifest.json

No zip/git/background/encryption in Sprint 1.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class SessionPaths:
    session_dir: Path
    sources_dir: Path
    report_path: Path
    manifest_path: Path


def session_timestamp_utc() -> str:
    """Return a filesystem-safe UTC timestamp."""

    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def create_session(archives_dir: Path, *, timestamp: str | None = None) -> SessionPaths:
    """Create and return a new session folder structure."""

    if timestamp is None:
        timestamp = session_timestamp_utc()

    session_dir = archives_dir / f"session-{timestamp}"
    sources_dir = session_dir / "sources"
    sources_dir.mkdir(parents=True, exist_ok=False)

    report_path = session_dir / "report.txt"
    manifest_path = session_dir / "manifest.json"

    return SessionPaths(
        session_dir=session_dir,
        sources_dir=sources_dir,
        report_path=report_path,
        manifest_path=manifest_path,
    )


def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_sources(sources_dir: Path, *, kernel_log: str, system_log: str | None) -> dict[str, str]:
    """Write source logs and return manifest mapping (source_name -> file name)."""

    mapping: dict[str, str] = {}

    kernel_name = "journalctl-kernel.log"
    (sources_dir / kernel_name).write_text(kernel_log, encoding="utf-8")
    mapping["journalctl_kernel"] = kernel_name

    if system_log is not None:
        system_name = "journalctl-system.log"
        (sources_dir / system_name).write_text(system_log, encoding="utf-8")
        mapping["journalctl_system"] = system_name

    return mapping


def write_report(
    report_path: Path,
    *,
    tool: str,
    version: str,
    range_input: str,
    since_utc_iso: str,
    sources_mapping: dict[str, str],
    warnings: list[str],
) -> None:
    """Write a plain text Sprint 1 report."""

    lines: list[str] = []
    lines.append(f"{tool} v{version}")
    lines.append("Sprint 1 report (capture-only)")
    lines.append("")
    lines.append(f"range_input: {range_input}")
    lines.append(f"since_utc: {since_utc_iso}")
    lines.append("")
    lines.append("sources_written:")
    for key, fname in sources_mapping.items():
        lines.append(f"  - {key}: sources/{fname}")

    lines.append("")
    lines.append("notes:")
    lines.append("  - Sprint 1 captures logs only.")
    lines.append("  - Panic/anomaly detection arrives in Sprint 2.")

    if warnings:
        lines.append("")
        lines.append("warnings:")
        for w in warnings:
            lines.append(f"  - {w}")

        lines.append("")
        lines.append("permissions_hint:")
        lines.append("  - If journalctl capture failed, try running with sudo")
        lines.append("    or add your user to the systemd-journal group.")

    write_text(report_path, "\n".join(lines) + "\n")


def planned_features_payload() -> dict[str, Any]:
    """Sprint roadmap placeholders (not implemented)."""

    return {
        "panic_detection": "Sprint 2",
        "anomaly_metrics": "Sprint 2+",
        "zip_and_git_export": "Sprint 3+",
        "background_sessions": "Sprint 3+",
        "encryption": "Sprint 4+",
    }


def write_manifest(
    manifest_path: Path,
    *,
    tool: str,
    version: str,
    range_input: str,
    since_utc_iso: str,
    kernel_only: bool,
    sources_mapping: dict[str, str],
    warnings: list[str],
    errors: list[str],
) -> None:
    payload: dict[str, Any] = {
        "tool": tool,
        "version": version,
        "range_input": range_input,
        "since_utc": since_utc_iso,
        "kernel_only": kernel_only,
        "sources": sources_mapping,
        "warnings": warnings,
        "errors": errors,
        "planned_features": planned_features_payload(),
    }
    write_json(manifest_path, payload)

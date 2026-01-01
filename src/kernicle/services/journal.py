"""systemd journal capture wrappers.

Sprint 1 only captures logs via `journalctl` and writes raw output.
No parsing/anomaly detection is implemented yet.
"""

from __future__ import annotations

from dataclasses import dataclass
from subprocess import CompletedProcess, run
from typing import Sequence


@dataclass(frozen=True)
class CaptureResult:
    ok: bool
    command: list[str]
    stdout: str
    stderr: str
    returncode: int


def _run_journalctl(args: Sequence[str]) -> CaptureResult:
    command = ["journalctl", *args]
    proc: CompletedProcess[str] = run(
        command,
        text=True,
        capture_output=True,
        check=False,
    )
    return CaptureResult(
        ok=(proc.returncode == 0),
        command=list(command),
        stdout=proc.stdout or "",
        stderr=proc.stderr or "",
        returncode=proc.returncode,
    )


def capture_kernel(*, since_arg: str) -> CaptureResult:
    """Capture kernel logs since `since_arg` in short-iso format."""

    return _run_journalctl(["-k", "--since", since_arg, "--no-pager", "--output=short-iso"])


def capture_system(*, since_arg: str) -> CaptureResult:
    """Capture system logs (all units) since `since_arg` in short-iso format."""

    return _run_journalctl(["--since", since_arg, "--no-pager", "--output=short-iso"])

"""Time range parsing for `kernicle push`.

Supported `--range` values (Sprint 1):
- Relative: last:5m, last:30m, last:2h, last:1d, last:30s
- ISO datetime treated as --since: 2025-12-30T12:00:00Z

`parse_range()` returns a TimeRange with:
- since_utc: timezone-aware UTC datetime
- since_arg: a journalctl-friendly --since argument (UTC)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import re


_REL_RE = re.compile(r"^last:(?P<value>\d+)(?P<unit>[smhd])$", re.IGNORECASE)


@dataclass(frozen=True)
class TimeRange:
    range_input: str
    since_utc: datetime
    since_arg: str


def _format_journalctl_since_arg(dt_utc: datetime) -> str:
    """Format a UTC datetime into a stable journalctl `--since` argument.

    journalctl accepts a variety of time formats. A portable option is:
    "YYYY-MM-DD HH:MM:SS UTC"
    """

    if dt_utc.tzinfo is None:
        raise ValueError("since_utc must be timezone-aware")
    dt_utc = dt_utc.astimezone(timezone.utc)
    return dt_utc.strftime("%Y-%m-%d %H:%M:%S UTC")


def parse_range(range_value: str, *, now_utc: datetime | None = None) -> TimeRange:
    """Parse a range string into a TimeRange.

    Args:
        range_value: The `--range` CLI value.
        now_utc: Injected 'now' for tests; must be timezone-aware UTC.

    Raises:
        ValueError: for invalid inputs.
    """

    if not range_value or not range_value.strip():
        raise ValueError("range must be a non-empty string")

    value = range_value.strip()

    if now_utc is None:
        now_utc = datetime.now(timezone.utc)

    if now_utc.tzinfo is None:
        raise ValueError("now_utc must be timezone-aware")

    m = _REL_RE.match(value)
    if m:
        amount = int(m.group("value"))
        unit = m.group("unit").lower()

        if amount <= 0:
            raise ValueError("relative range amount must be > 0")

        delta: timedelta
        if unit == "s":
            delta = timedelta(seconds=amount)
        elif unit == "m":
            delta = timedelta(minutes=amount)
        elif unit == "h":
            delta = timedelta(hours=amount)
        elif unit == "d":
            delta = timedelta(days=amount)
        else:
            raise ValueError(f"unsupported unit: {unit}")

        since = now_utc.astimezone(timezone.utc) - delta
        return TimeRange(range_input=value, since_utc=since, since_arg=_format_journalctl_since_arg(since))

    # ISO datetime treated as --since
    # Requirement: example `2025-12-30T12:00:00Z`.
    # Accept both ...Z and explicit offsets.
    iso = value
    if iso.endswith("Z"):
        iso = iso[:-1] + "+00:00"

    try:
        dt = datetime.fromisoformat(iso)
    except ValueError as exc:
        raise ValueError(
            "invalid range; expected last:<n><s|m|h|d> or ISO datetime like 2025-12-30T12:00:00Z"
        ) from exc

    if dt.tzinfo is None:
        raise ValueError("ISO datetime must include timezone (e.g., 'Z')")

    dt_utc = dt.astimezone(timezone.utc)
    return TimeRange(range_input=value, since_utc=dt_utc, since_arg=_format_journalctl_since_arg(dt_utc))

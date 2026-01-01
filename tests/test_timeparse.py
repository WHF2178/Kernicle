from __future__ import annotations

from datetime import datetime, timezone

import pytest

from kernicle.services.timeparse import parse_range


def test_parse_range_last_5m_fixed_now() -> None:
    now = datetime(2025, 12, 30, 12, 0, 0, tzinfo=timezone.utc)
    tr = parse_range("last:5m", now_utc=now)

    assert tr.since_utc == datetime(2025, 12, 30, 11, 55, 0, tzinfo=timezone.utc)
    assert tr.since_arg == "2025-12-30 11:55:00 UTC"


def test_parse_range_iso_datetime_z() -> None:
    tr = parse_range("2025-12-30T12:00:00Z")
    assert tr.since_utc.tzinfo is not None
    assert tr.since_utc.astimezone(timezone.utc).isoformat().startswith("2025-12-30T12:00:00")
    assert tr.since_arg == "2025-12-30 12:00:00 UTC"


def test_parse_range_invalid_raises() -> None:
    with pytest.raises(ValueError):
        parse_range("yesterday")

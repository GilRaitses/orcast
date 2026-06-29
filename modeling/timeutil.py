"""Shared time helpers for the modeling pipeline.

The pipeline works in *hours since the Unix epoch* (a float) as its continuous
time axis: it is convenient for binning, time-blocking, and integrating
intensities, and round-trips cleanly to timezone-aware UTC datetimes.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Union

_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
_SECONDS_PER_HOUR = 3600.0

TimeLike = Union[str, datetime]


def parse_dt(value: TimeLike) -> datetime:
    """Parse an ISO string or datetime into a timezone-aware UTC datetime."""
    if isinstance(value, datetime):
        dt = value
    else:
        text = value.replace("Z", "+00:00") if isinstance(value, str) else value
        dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def to_hours(value: TimeLike) -> float:
    """Hours since the Unix epoch (UTC)."""
    return (parse_dt(value) - _EPOCH).total_seconds() / _SECONDS_PER_HOUR


def from_hours(hours: float) -> datetime:
    """Inverse of :func:`to_hours`: a timezone-aware UTC datetime."""
    return _EPOCH.fromtimestamp(hours * _SECONDS_PER_HOUR, tz=timezone.utc)

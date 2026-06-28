"""Future-departure corridor ETA — a transparent, sparse-data-robust model.

The WSDOT Traffic feed is realtime-only (no history endpoint), so a future
departure ("leave SeaTac 3 pm Friday") cannot be measured; it must be MODELED.
This module fits the simplest defensible model over the self-collected corridor
history log and predicts a per-route ETA with an interval:

    day-of-week x time-of-bin median of the measured ``current_time`` readings,
    with a graceful fallback to the latest measured travel time when the
    requested bin is empty.

Design constraints (WS-TRIPS Producer B):
- No heavy ML, no promotion. Stdlib only; the whole model is inspectable.
- Reads ONLY the gitignored history log resolved via
  ``wsdot_traffic.history_path()``. Never edits the source client or the poller.
- Every result is labeled ``MODELED`` and carries a ``basis`` dict (the method,
  the sample count, and — on fallback — when the latest reading was measured) so
  the connections planner can surface honesty downstream and never present a
  modeled ETA as measured.

History-log schema (one JSON object per line, written by
``wsdot_traffic.append_history``): the parsed ``TravelTimeRoute`` shape, i.e.
``travel_time_id`` (int), ``name``, ``current_time`` (live minutes — the
observation we model), ``average_time``, ``time_updated`` (when WSDOT measured the
reading), plus a ``logged_at`` UTC stamp added on append. Binning uses
``time_updated`` when present, else ``logged_at``.

Traffic patterns are local (rush hour), so timestamps and ``depart_dt`` are bucketed
in a local timezone (default America/Los_Angeles). The history stamps are UTC; a
naive ``depart_dt`` is interpreted as already-local.
"""

from __future__ import annotations

import json
import statistics
from datetime import datetime, timezone, tzinfo
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:  # zoneinfo is stdlib (3.9+); degrade to UTC bucketing if tzdata is absent.
    from zoneinfo import ZoneInfo
except Exception:  # pragma: no cover - exercised only on a zoneinfo-less runtime
    ZoneInfo = None  # type: ignore[assignment]

# The corridor is Pacific; bucket local-time so rush-hour bins are meaningful.
DEFAULT_TZ_NAME = "America/Los_Angeles"
# Width of a time-of-day bucket, in minutes. 60 keeps bins legible and not too
# sparse for a young, slowly-accruing history log.
DEFAULT_BIN_MINUTES = 60

LABEL = "MODELED"

_DOW_NAMES = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")


# --------------------------------------------------------------------------- #
# Timezone + timestamp helpers
# --------------------------------------------------------------------------- #

def _resolve_tz(tz: Any) -> tzinfo:
    """Resolve a tz argument (name / tzinfo / None) to a concrete tzinfo.

    Falls back to UTC when zoneinfo or the named zone is unavailable, so bucketing
    never raises on a stripped-down runtime (it just becomes UTC-based).
    """
    if isinstance(tz, tzinfo):
        return tz
    name = tz or DEFAULT_TZ_NAME
    if ZoneInfo is not None:
        try:
            return ZoneInfo(name)
        except Exception:
            pass
    return timezone.utc


def _parse_ts(value: Any) -> Optional[datetime]:
    """Parse a history timestamp (ISO-8601 or ``str(datetime)``) to aware UTC.

    ``time_updated`` is serialized via ``json.dumps(default=str)`` so it arrives as
    ``"2026-06-27 02:05:00+00:00"`` (space separator); ``logged_at`` is a true
    isoformat. Both are handled. A naive parse is assumed UTC. Returns ``None`` for
    missing / unparseable values rather than raising.
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    for candidate in (text, text.replace(" ", "T", 1)):
        try:
            parsed = datetime.fromisoformat(candidate)
        except ValueError:
            continue
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    return None


def _to_local(dt: datetime, tz: tzinfo) -> datetime:
    """Project a datetime into ``tz``; a naive datetime is taken as already-local."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=tz)
    return dt.astimezone(tz)


def _bucket(dt: datetime, tz: tzinfo, bin_minutes: int) -> Tuple[int, int]:
    """Return the ``(day_of_week, time_bin_index)`` bucket for a datetime in ``tz``."""
    local = _to_local(dt, tz)
    minute_of_day = local.hour * 60 + local.minute
    return local.weekday(), minute_of_day // bin_minutes


def _bin_label(time_bin: int, bin_minutes: int) -> str:
    """Human-readable ``HH:MM-HH:MM`` window for a time-bin index."""
    start = time_bin * bin_minutes
    end = start + bin_minutes
    return f"{start // 60:02d}:{start % 60:02d}-{(end // 60) % 24:02d}:{end % 60:02d}"


# --------------------------------------------------------------------------- #
# History loading
# --------------------------------------------------------------------------- #

def _history_path(history_path: Optional[Any]) -> Path:
    """Resolve the history-log path, defaulting to the source client's location.

    Imported lazily so this offline model never forces ``requests`` (a
    ``wsdot_traffic`` import dependency) onto callers that pass an explicit path.
    """
    if history_path is not None:
        return Path(history_path)
    from src.aws_backend.sources import wsdot_traffic

    return wsdot_traffic.history_path()


def _load_samples(route_id: int, path: Path) -> List[Tuple[datetime, float]]:
    """Load ``(timestamp, current_time)`` samples for one route from the log.

    Rows without the requested ``travel_time_id``, without a numeric
    ``current_time``, or without a parseable timestamp are skipped. Returns ``[]``
    when the log is absent (the history is gitignored and may not exist yet).
    """
    if not path.exists():
        return []
    samples: List[Tuple[datetime, float]] = []
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except (ValueError, TypeError):
                continue
            if not isinstance(row, dict):
                continue
            if row.get("travel_time_id") != route_id:
                continue
            observed = row.get("current_time")
            if not isinstance(observed, (int, float)) or isinstance(observed, bool):
                continue
            if observed < 0:
                continue
            ts = _parse_ts(row.get("time_updated")) or _parse_ts(row.get("logged_at"))
            if ts is None:
                continue
            samples.append((ts, float(observed)))
    return samples


# --------------------------------------------------------------------------- #
# Interval
# --------------------------------------------------------------------------- #

def _percentile(sorted_values: List[float], pct: float) -> float:
    """Linear-interpolated percentile over a pre-sorted list (``0 <= pct <= 100``)."""
    if not sorted_values:
        raise ValueError("percentile of empty sequence")
    if len(sorted_values) == 1:
        return sorted_values[0]
    rank = (pct / 100.0) * (len(sorted_values) - 1)
    low = int(rank)
    high = min(low + 1, len(sorted_values) - 1)
    frac = rank - low
    return sorted_values[low] + (sorted_values[high] - sorted_values[low]) * frac


def _interval(values: List[float], center: float) -> Tuple[float, float]:
    """A robust prediction interval around ``center``.

    With enough samples use the empirical 25th/75th percentiles; otherwise fall
    back to a relative band around the center (at least +/- 2 min) so a thin bin
    still communicates uncertainty rather than false precision.
    """
    if len(values) >= 4:
        ordered = sorted(values)
        return (
            round(_percentile(ordered, 25.0), 1),
            round(_percentile(ordered, 75.0), 1),
        )
    band = max(0.15 * center, 2.0)
    return (round(center - band, 1), round(center + band, 1))


def _empty_result(basis_extra: Dict[str, Any]) -> Dict[str, Any]:
    basis = {"method": "no_history", "n_samples": 0}
    basis.update(basis_extra)
    return {"eta_minutes": None, "interval": None, "basis": basis, "label": LABEL}


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #

def predict_eta(
    route_id: int,
    depart_dt: datetime,
    *,
    history_path: Optional[Any] = None,
    tz: Any = DEFAULT_TZ_NAME,
    bin_minutes: int = DEFAULT_BIN_MINUTES,
) -> Dict[str, Any]:
    """Predict a future-departure ETA for one measured corridor route.

    Model: the median of the measured ``current_time`` readings that fall in the
    same day-of-week x time-of-bin bucket as ``depart_dt``. When that bucket is
    empty, fall back to the latest measured reading for the route. When the route
    has no history at all, return an honest "unknown" (``eta_minutes = None``).

    Args:
        route_id: WSDOT ``TravelTimeID`` for the measured southern-corridor route.
        depart_dt: Desired departure time. A naive datetime is interpreted as
            already in ``tz``; an aware datetime is converted into ``tz``.
        history_path: Override the history-log path (used in tests); defaults to
            ``wsdot_traffic.history_path()``.
        tz: Bucketing timezone (name, tzinfo, or None for the Pacific default).
        bin_minutes: Width of a time-of-day bucket, in minutes.

    Returns:
        ``{"eta_minutes", "interval", "basis", "label"}`` where:
          - ``eta_minutes`` is the predicted minutes (float) or ``None`` (no data);
          - ``interval`` is ``{"low_minutes", "high_minutes"}`` or ``None``;
          - ``basis`` is a dict carrying ``method``
            (``"modeled_history"`` | ``"fallback_latest_measured"`` |
            ``"no_history"``), ``n_samples``, and bucket / freshness detail;
          - ``label`` is always ``"MODELED"``.
    """
    tzinfo_obj = _resolve_tz(tz)
    path = _history_path(history_path)
    samples = _load_samples(route_id, path)

    target_dow, target_bin = _bucket(depart_dt, tzinfo_obj, bin_minutes)
    bucket_detail = {
        "route_id": route_id,
        "day_of_week": _DOW_NAMES[target_dow],
        "time_bin": _bin_label(target_bin, bin_minutes),
        "bin_minutes": bin_minutes,
    }

    if not samples:
        return _empty_result(bucket_detail)

    in_bucket = [
        observed
        for ts, observed in samples
        if _bucket(ts, tzinfo_obj, bin_minutes) == (target_dow, target_bin)
    ]

    if in_bucket:
        eta = round(statistics.median(in_bucket), 1)
        low, high = _interval(in_bucket, eta)
        basis = {"method": "modeled_history", "n_samples": len(in_bucket)}
        basis.update(bucket_detail)
        return {
            "eta_minutes": eta,
            "interval": {"low_minutes": low, "high_minutes": high},
            "basis": basis,
            "label": LABEL,
        }

    # Empty bucket -> latest measured travel time for this route, clearly flagged.
    latest_ts, latest_value = max(samples, key=lambda item: item[0])
    eta = round(latest_value, 1)
    all_values = [observed for _, observed in samples]
    low, high = _interval(all_values, eta)
    basis = {
        "method": "fallback_latest_measured",
        "n_samples": 0,
        "fallback_from_total_samples": len(samples),
        "measured_at": latest_ts.astimezone(timezone.utc).isoformat(),
    }
    basis.update(bucket_detail)
    return {
        "eta_minutes": eta,
        "interval": {"low_minutes": low, "high_minutes": high},
        "basis": basis,
        "label": LABEL,
    }

"""Multi-station acoustic ingest recipe for the extra in-region Orcasound nodes.

The production ``acoustic_detections`` stream currently carries only
``haro_strait``. Three more in-region OrcaHello/Orcasound nodes have reviewed
detections cached: ``orcasound_lab``, ``andrews_bay``,
``north_san_juan_channel``. This module turns the cached OrcaHello
reviewed-outcome index into ``acoustic_detections`` records keyed by
``record["station"]`` and feeds them through the existing
:func:`src.aws_backend.ingest_timeseries._put_grouped_by_station` grouping, so
the multi-station nodes land in the same stream/partition layout as the
production single-station ingest.

Why the cache and not ``fetch_history`` (charter B.9): the OrcaHello history API
403s / SSL-EOFs on heavy paging and ``fetch_history`` returns oldest-first
(early pages are all Haro Strait), so the reviewed-outcome endpoints plus the
cached indexes are the reliable multi-station source. The cache at
``.cca/catalogue/O0/20260627_forecast-candidates/orcahello_index.cache.json``
was built from those reviewed-outcome endpoints.

DRY RUN BY DEFAULT. ``ingest_multistation_acoustic`` defaults to
``dry_run=True`` and never writes the production store: it groups by station and
reports the per-station record counts it WOULD write (both the raw cache count
and the count that survives the store's ``(t, id)`` dedupe on write). The actual
production ``acoustic_detections`` write is operator/deploy-gated (Wave 2);
``dry_run=False`` requires an explicit store to be passed.

Run the dry run under ``.venv``::

    .venv/bin/python -m src.aws_backend.ingest_multistation
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from .ingest_timeseries import ACOUSTIC, _put_grouped_by_station
from .timeseries import MemoryTimeSeriesStore

# Repo root is three levels up from this file (src/aws_backend/<file>).
_REPO_ROOT = Path(__file__).resolve().parents[2]

# Cached OrcaHello reviewed-outcome index (charter B.9). The plain index carries
# the 3 extra nodes; the confidence variant carries per-record confidence but for
# a different (mostly haro_strait) slice, so it is an optional enrichment only.
DEFAULT_CACHE_PATH = (
    _REPO_ROOT
    / ".cca/catalogue/O0/20260627_forecast-candidates/orcahello_index.cache.json"
)
DEFAULT_CONFIDENCE_CACHE_PATH = (
    _REPO_ROOT
    / ".cca/catalogue/O0/20260627_forecast-candidates/orcahello_index.confidence.cache.json"
)

# The three in-region nodes missing from the production acoustic_detections
# stream (haro_strait is already in production and is intentionally excluded).
# Coordinates match the CAND waveset / Orcasound catalog (see
# modeling/studies/common.py STATION_COORDS).
EXTRA_NODES: Dict[str, Tuple[float, float]] = {
    "orcasound_lab": (48.5583362, -123.1735774),
    "north_san_juan_channel": (48.591294, -123.058779),
    "andrews_bay": (48.5500299, -123.1666492),
}

# Wide read window for the dry-run dedupe probe.
_WIDE0 = datetime(1970, 1, 1, tzinfo=timezone.utc)
_WIDE1 = datetime(2100, 1, 1, tzinfo=timezone.utc)


def _load_cache_records(cache_path: Path) -> List[dict]:
    """Return the raw ``records`` list from a cached OrcaHello index file."""
    path = Path(cache_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    return [row for row in data.get("records", []) if isinstance(row, dict)]


def _confidence_lookup(cache_path: Path) -> Dict[Tuple[str, str], float]:
    """Map ``(station_key, t)`` to confidence from the confidence cache, if present."""
    path = Path(cache_path)
    if not path.exists():
        return {}
    out: Dict[Tuple[str, str], float] = {}
    for row in _load_cache_records(path):
        conf = row.get("confidence")
        key = str(row.get("key") or "")
        t = row.get("t")
        if conf is None or not key or not t:
            continue
        try:
            out[(key, str(t))] = float(conf)
        except (TypeError, ValueError):
            continue
    return out


def build_acoustic_records(
    cache_path: Path = DEFAULT_CACHE_PATH,
    stations: Mapping[str, Tuple[float, float]] = EXTRA_NODES,
    outcomes: Optional[Sequence[str]] = None,
    confidence_cache_path: Optional[Path] = DEFAULT_CONFIDENCE_CACHE_PATH,
) -> List[dict]:
    """Map cached OrcaHello reviewed-outcome rows to acoustic_detections records.

    Each emitted record mirrors the production OrcaHello acoustic record shape
    (``t``, ``station``, ``latitude``, ``longitude``, ``confidence``,
    ``reviewed``, ``found``, ``confirmed``) and is keyed by ``record["station"]``
    so :func:`_put_grouped_by_station` groups it correctly. Only the stations in
    ``stations`` are emitted (haro_strait is excluded by not being in the map).

    ``outcomes`` optionally filters to a subset of reviewed outcomes
    (e.g. ``("confirmed",)``); the default ``None`` keeps every outcome, matching
    the production ``fetch_history`` ingest which stores all in-region detections
    and records the review state per record.
    """
    station_coords = dict(stations)
    conf_lookup = _confidence_lookup(confidence_cache_path) if confidence_cache_path else {}

    records: List[dict] = []
    for row in _load_cache_records(cache_path):
        key = str(row.get("key") or "")
        if key not in station_coords:
            continue
        outcome = str(row.get("outcome") or "unreviewed")
        if outcomes is not None and outcome not in outcomes:
            continue
        t = row.get("t")
        if not t:
            continue
        lat, lng = station_coords[key]
        confirmed = outcome == "confirmed"
        confidence = row.get("confidence")
        if confidence is None:
            confidence = conf_lookup.get((key, str(t)))
        records.append(
            {
                "t": t,
                "id": row.get("id"),
                "station": key,
                "latitude": lat,
                "longitude": lng,
                "confidence": confidence,
                "reviewed": outcome != "unreviewed",
                "found": "yes" if confirmed else ("no" if outcome == "false_positive" else None),
                "confirmed": confirmed,
                "outcome": outcome,
                "source": "orcahello_index_cache",
            }
        )
    return records


def ingest_multistation_acoustic(
    store: Optional[Any] = None,
    cache_path: Path = DEFAULT_CACHE_PATH,
    stations: Mapping[str, Tuple[float, float]] = EXTRA_NODES,
    outcomes: Optional[Sequence[str]] = None,
    dry_run: bool = True,
    confidence_cache_path: Optional[Path] = DEFAULT_CONFIDENCE_CACHE_PATH,
) -> Dict[str, Any]:
    """Ingest the extra in-region nodes into ``acoustic_detections``, dry-run by default.

    Reuses :func:`_put_grouped_by_station` (records keyed by
    ``record["station"]``) so the nodes land in the same stream layout as the
    production ingest.

    - ``dry_run=True`` (default): does NOT write the production store. Records are
      built and grouped, and the per-station counts that WOULD be written are
      reported, including ``stored_records_by_station`` -- the count that survives
      the store's ``(t, id)`` dedupe on write (measured against a throwaway
      ``MemoryTimeSeriesStore``).
    - ``dry_run=False``: operator/deploy-gated production path. Requires an
      explicit ``store`` and writes via ``_put_grouped_by_station``.

    Returns a summary dict with raw and post-dedupe per-station counts.
    """
    records = build_acoustic_records(
        cache_path,
        stations=stations,
        outcomes=outcomes,
        confidence_cache_path=confidence_cache_path,
    )

    raw_counts: Dict[str, int] = {}
    for record in records:
        st = record["station"]
        raw_counts[st] = raw_counts.get(st, 0) + 1

    # Probe the store's (t, id) dedupe to learn what is actually persisted.
    probe = MemoryTimeSeriesStore()
    _put_grouped_by_station(probe, ACOUSTIC, records)
    stored_counts = {
        st: len(probe.get_series(ACOUSTIC, st, _WIDE0, _WIDE1))
        for st in probe.list_stations(ACOUSTIC)
    }

    summary: Dict[str, Any] = {
        "stream": ACOUSTIC,
        "dry_run": dry_run,
        "cache_path": str(cache_path),
        "stations": sorted(raw_counts),
        "raw_records_by_station": raw_counts,
        "stored_records_by_station": stored_counts,
        "total_raw": sum(raw_counts.values()),
        "total_stored": sum(stored_counts.values()),
    }

    if dry_run:
        summary["written"] = False
        summary["note"] = (
            "DRY RUN: production store NOT written. Counts are what would be "
            "written. Production write is operator/deploy-gated (Wave 2)."
        )
        return summary

    if store is None:
        raise ValueError(
            "dry_run=False requires an explicit store; the production "
            "acoustic_detections write is operator/deploy-gated."
        )
    summary["written"] = True
    summary["put_grouped_result"] = _put_grouped_by_station(store, ACOUSTIC, records)
    return summary


def main() -> None:
    summary = ingest_multistation_acoustic(dry_run=True)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

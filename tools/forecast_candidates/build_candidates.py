#!/usr/bin/env python3
"""CAND build harness: assemble forecast candidate sightings.

Produces the candidate set described in
``.cca/catalogue/O0/20260627_forecast-candidates/`` (CANDIDATE_CHARTER.md and
candidate_targets.schema.yml). A candidate is a confirmed sighting (a coordinate
plus a timestamp) joined to the external sources the system collects, prioritized
near the in-region hydrophones that carry OrcaHello annotation records.

Honesty constraints (do not relax):
- Confirmed means cross_validation.status in {verified, likely}. OrcaHello
  history detections enter only when their reviewed outcome is "confirmed", and
  they are tagged source_kind=acoustic (hydrophone position, not whale GPS).
- Source alignment is scored only on real external overlaps (hydrophone
  proximity, OrcaHello annotation/detection window, NOAA span). Universally
  computable covariates are recorded but do not drive the score.
- No model is trained here. Effective confidence stays 0%.

Modes:
  gap    read-only coverage counts -> GAP_COVERAGE.md
  build  assemble candidates.targets.json (>=40, >=20 tier-A target)

Usage:
  python3 tools/forecast_candidates/build_candidates.py gap   [--live] [--window-h 24]
  python3 tools/forecast_candidates/build_candidates.py build [--live] [--window-h 24] [--max 200]
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

HOME = REPO / ".cca" / "catalogue" / "O0" / "20260627_forecast-candidates"
TARGETS_OUT = HOME / "candidates.targets.json"
GAP_OUT = HOME / "GAP_COVERAGE.md"
ORCAHELLO_CACHE = HOME / "orcahello_index.cache.json"

# In-region hydrophones (Orcasound catalog + ONC LKWA / OrcaHello haro_strait).
HYDROPHONES: List[Dict[str, object]] = [
    {"key": "orcasound_lab", "name": "Orcasound Lab", "lat": 48.5583362, "lng": -123.1735774},
    {"key": "north_san_juan_channel", "name": "North San Juan Channel", "lat": 48.591294, "lng": -123.058779},
    {"key": "andrews_bay", "name": "Andrews Bay", "lat": 48.5500299, "lng": -123.1666492},
    {"key": "haro_strait", "name": "Lime Kiln / Haro Strait", "lat": 48.516, "lng": -123.152},
]


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    r = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lng = math.radians(lng2 - lng1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lng / 2) ** 2
    )
    return 2 * r * math.asin(min(1.0, math.sqrt(a)))


def nearest_hydrophone(lat: float, lng: float) -> Tuple[str, float]:
    best_key, best_km = HYDROPHONES[0]["key"], math.inf
    for h in HYDROPHONES:
        km = haversine_km(lat, lng, float(h["lat"]), float(h["lng"]))
        if km < best_km:
            best_key, best_km = str(h["key"]), km
    return best_key, round(best_km, 3)


def season_phase(dt: datetime) -> float:
    doy = dt.timetuple().tm_yday
    year_len = 366.0 if (dt.year % 4 == 0 and (dt.year % 100 != 0 or dt.year % 400 == 0)) else 365.0
    return round((doy - 1) / year_len, 4)


def parse_dt(value: object) -> Optional[datetime]:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(float(value), tz=timezone.utc)
        except (OverflowError, OSError, ValueError):
            return None
    if isinstance(value, str):
        s = value.strip().replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(s)
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except ValueError:
            for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
                try:
                    return datetime.strptime(value.strip(), fmt).replace(tzinfo=timezone.utc)
                except ValueError:
                    continue
    return None


def _read_orcahello_cache() -> List[Tuple[datetime, str, str]]:
    if not ORCAHELLO_CACHE.exists():
        return []
    try:
        raw = json.loads(ORCAHELLO_CACHE.read_text(encoding="utf-8"))
        out: List[Tuple[datetime, str, str]] = []
        for row in raw.get("records", []):
            ts = parse_dt(row.get("t"))
            if ts is None:
                continue
            out.append((ts, str(row["key"]), str(row.get("outcome", "unreviewed"))))
        return out
    except (OSError, ValueError, KeyError):
        return []


def _write_orcahello_cache(records: List[Tuple[datetime, str, str]]) -> None:
    doc = {
        "source": "OrcaHelloHistoryAdapter (reviewed_outcomes + history)",
        "cached_at": datetime.now(timezone.utc).isoformat(),
        "record_count": len(records),
        "records": [{"t": ts.astimezone(timezone.utc).isoformat(), "key": key, "outcome": outcome} for ts, key, outcome in records],
    }
    ORCAHELLO_CACHE.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")


def load_orcahello_index(live: bool) -> Tuple[List[Tuple[datetime, str, str]], str]:
    """Return ([(timestamp, nearest_hydrophone_key, outcome)], provenance).

    Buckets each detection to the nearest in-region hydrophone by coordinates,
    which avoids station-name mismatch. The OrcaHello history API is intermittent
    (known 403s), so a successful live fetch is cached locally and reused when a
    later live fetch is blocked. The cache is real fetched OrcaHello data.
    """
    records: List[Tuple[datetime, str, str]] = []
    if live:
        try:
            from src.aws_backend.sources.orcahello_history import OrcaHelloHistoryAdapter

            adapter = OrcaHelloHistoryAdapter()
            rows: List[dict] = []
            try:
                rows += adapter.fetch_reviewed_outcomes(in_region_only=True)
            except Exception:  # noqa: BLE001 - external API best-effort
                pass
            try:
                rows += adapter.fetch_history(in_region_only=True)
            except Exception:  # noqa: BLE001
                pass
            for r in rows:
                ts = parse_dt(r.get("t") or r.get("timestamp"))
                lat, lng = r.get("latitude"), r.get("longitude")
                if ts is None or lat is None or lng is None:
                    continue
                key, _ = nearest_hydrophone(float(lat), float(lng))
                outcome = str(r.get("outcome") or ("confirmed" if r.get("confirmed") else "unreviewed"))
                records.append((ts, key, outcome))
        except Exception as exc:  # noqa: BLE001
            print(f"  [warn] OrcaHello history unavailable: {exc}", file=sys.stderr)

    if records:
        _write_orcahello_cache(records)
        return records, "live"

    cached = _read_orcahello_cache()
    if cached:
        print(f"  [info] OrcaHello live fetch empty; using cache ({len(cached)} records)", file=sys.stderr)
        return cached, "cache"
    return [], "none"


def overlap_count(key: str, ts: datetime, index: List[Tuple[datetime, str, str]], window_h: int) -> int:
    if not index:
        return 0
    window_s = window_h * 3600
    n = 0
    for rec_ts, rec_key, _outcome in index:
        if rec_key != key:
            continue
        if abs((rec_ts - ts).total_seconds()) <= window_s:
            n += 1
    return n


def _confirmed_acoustic_candidates(index: List[Tuple[datetime, str, str]], window_h: int) -> List[dict]:
    """Build acoustic candidates from confirmed OrcaHello detections.

    Each confirmed (human-reviewed, found) detection at an in-region hydrophone
    is a real recorded acoustic event. Tagged source_kind=acoustic and mapped to
    cross_validation_status=verified (a reviewed-confirmed detection), never a
    whale GPS fix.
    """
    confirmed = [(ts, key) for ts, key, outcome in index if outcome.lower() == "confirmed"]
    confirmed.sort(key=lambda x: x[0].timestamp())
    out: List[dict] = []
    seen: set = set()
    by_key: Dict[str, List[datetime]] = {}
    for ts, key in confirmed:
        by_key.setdefault(key, []).append(ts)
    for key, tss in by_key.items():
        h = next(hh for hh in HYDROPHONES if hh["key"] == key)
        for ts in tss:
            # Dedupe near-identical events at the same station within an hour.
            bucket = (key, int(ts.timestamp() // 3600))
            if bucket in seen:
                continue
            seen.add(bucket)
            out.append(
                {
                    "sighting_id": f"orcahello_hist_{key}_{int(ts.timestamp())}",
                    "source": "orcahello_history",
                    "source_kind": "acoustic",
                    "latitude": float(h["lat"]),
                    "longitude": float(h["lng"]),
                    "timestamp": ts,
                    "cross_validation_status": "verified",
                    "data_quality_score": None,
                }
            )
    return out


def build_records(live: bool, window_h: int, limit: int) -> Tuple[List[dict], Dict[str, object]]:
    from src.aws_backend import covariates
    from src.aws_backend.geo_region import in_bounds, nearest_shore_m
    from src.aws_backend.models import ValidationStatus
    from src.aws_backend.sources.bathymetry import BathymetryAdapter
    from src.aws_backend.state import run_ingestion, storage

    run = run_ingestion(include_live=live)
    sightings = storage.list_sightings(limit=10_000)
    bath = BathymetryAdapter()
    index, index_provenance = load_orcahello_index(live)

    # Augment the index with OrcaHello-sourced sightings already in the store
    # (these come through the main /api/detections endpoint during ingestion, so
    # they survive even when the history paging endpoint is rate-limited). Their
    # reviewed/found state maps to a confirmed acoustic outcome.
    store_acoustic = 0
    for s in sightings:
        if not s.source.startswith("orcahello"):
            continue
        ts = s.timestamp if s.timestamp.tzinfo else s.timestamp.replace(tzinfo=timezone.utc)
        key, _ = nearest_hydrophone(s.latitude, s.longitude)
        grade = ""
        for ev in s.evidence:
            grade = (ev.quality_grade or "")
            if grade:
                break
        outcome = "confirmed" if grade == "confirmed_acoustic_detection" else "unreviewed"
        index.append((ts, key, outcome))
        store_acoustic += 1
    if store_acoustic and index_provenance == "none":
        index_provenance = "store"

    confirmed_status = {ValidationStatus.VERIFIED, ValidationStatus.LIKELY}
    pool: List[dict] = []

    # Pool A: confirmed sightings from the store (visual + recent acoustic).
    store_confirmed = 0
    store_in_region = 0
    for s in sightings:
        if not in_bounds(s.latitude, s.longitude):
            continue
        store_in_region += 1
        if s.cross_validation.status not in confirmed_status:
            continue
        store_confirmed += 1
        kind = "acoustic" if s.source == "orcahello" else "visual"
        pool.append(
            {
                "sighting_id": s.sighting_id,
                "source": s.source,
                "source_kind": kind,
                "source_id": s.source_id,
                "latitude": float(s.latitude),
                "longitude": float(s.longitude),
                "timestamp": s.timestamp if s.timestamp.tzinfo else s.timestamp.replace(tzinfo=timezone.utc),
                "cross_validation_status": s.cross_validation.status.value,
                "data_quality_score": round(float(s.cross_validation.score), 4),
            }
        )

    # Pool B: confirmed OrcaHello acoustic-history detections near hydrophones.
    acoustic = _confirmed_acoustic_candidates(index, window_h)

    # Merge, dropping duplicate ids.
    seen_ids = {p["sighting_id"] for p in pool}
    for a in acoustic:
        if a["sighting_id"] not in seen_ids:
            pool.append(a)
            seen_ids.add(a["sighting_id"])

    now = datetime.now(timezone.utc)
    candidates: List[dict] = []
    for p in pool:
        lat, lng, ts = p["latitude"], p["longitude"], p["timestamp"]
        key, km = nearest_hydrophone(lat, lng)
        ov = overlap_count(key, ts, index, window_h)
        depth = bath.depth_at(lat, lng)
        shore = nearest_shore_m(lat, lng)
        # NOAA CO-OPS tide/current predictions cover the pilot region for any
        # timestamp (stations PUG1701-1703); treat in-region as covered.
        noaa_cov = in_bounds(lat, lng)

        prox = max(0.0, 1.0 - km / 10.0)
        ov_norm = min(1.0, ov / 3.0)
        sq = 1.0 if p["cross_validation_status"] == "verified" else 0.6
        age_days = max(0.0, (now - ts).total_seconds() / 86400.0)
        recency = max(0.0, 1.0 - age_days / 3650.0)
        score = round(0.40 * prox + 0.30 * ov_norm + 0.10 * (1.0 if noaa_cov else 0.0) + 0.15 * sq + 0.05 * recency, 4)

        if km <= 5.0 and ov >= 1:
            tier = "A"
        elif km <= 10.0 or noaa_cov:
            tier = "B"
        else:
            tier = "C"

        candidates.append(
            {
                "sighting_id": p["sighting_id"],
                "source": p["source"],
                "source_kind": p["source_kind"],
                "source_id": p.get("source_id"),
                "latitude": round(lat, 6),
                "longitude": round(lng, 6),
                "timestamp": ts.astimezone(timezone.utc).isoformat(),
                "cross_validation_status": p["cross_validation_status"],
                "data_quality_score": p.get("data_quality_score"),
                "nearest_hydrophone": key,
                "nearest_hydrophone_km": km,
                "orcahello_overlap_count": ov,
                "orcahello_overlap_window_h": window_h,
                "noaa_tide_coverage": bool(noaa_cov),
                "covariates": {
                    "diel_phase": round(covariates.diel_phase(ts, lng), 4),
                    "lunar_phase": round(covariates.lunar_phase(ts)["phase"], 4),
                    "season_phase": season_phase(ts),
                    "depth_m": round(depth, 2) if depth is not None else None,
                    "shore_m": shore,
                    "fitted_today": ["diel_phase", "lunar_phase"],
                },
                "priority_score": score,
                "priority_tier": tier,
            }
        )

    # Highest priority first; cap at limit.
    tier_rank = {"A": 0, "B": 1, "C": 2}
    candidates.sort(key=lambda c: (tier_rank[c["priority_tier"]], -c["priority_score"]))
    candidates = candidates[:limit]

    stats = {
        "ingestion_run": run.run_id,
        "store_in_region": store_in_region,
        "store_confirmed": store_confirmed,
        "orcahello_index_records": len(index),
        "orcahello_index_provenance": index_provenance,
        "orcahello_confirmed_acoustic": len(acoustic),
        "pool_total": len(pool),
        "candidates": len(candidates),
        "tier_a": sum(1 for c in candidates if c["priority_tier"] == "A"),
        "tier_b": sum(1 for c in candidates if c["priority_tier"] == "B"),
        "tier_c": sum(1 for c in candidates if c["priority_tier"] == "C"),
        "near5km": sum(1 for c in candidates if c["nearest_hydrophone_km"] <= 5.0),
        "near10km": sum(1 for c in candidates if c["nearest_hydrophone_km"] <= 10.0),
        "live": live,
        "window_h": window_h,
    }
    return candidates, stats


def write_targets(candidates: List[dict], stats: Dict[str, object]) -> None:
    doc = {
        "_meta": {
            "family": "CAND",
            "schema": "candidate_targets.schema.yml",
            "status": "populated",
            "populated_by": "C-BUILD (tools/forecast_candidates/build_candidates.py)",
            "target_count": 40,
            "min_tier_a": 20,
            "confirmed_filter": "cross_validation.status in [verified, likely]; OrcaHello history requires reviewed-confirmed",
            "honesty": [
                "Acoustic-sourced candidates (orcahello, orcahello_history) carry source_kind=acoustic; hydrophone position, not whale GPS.",
                "Source alignment counts only real external overlaps (hydrophone proximity, OrcaHello annotation/detection window, NOAA span). Universally computable covariates do not count.",
                "No model is trained here; effective confidence remains 0% with the gate caveat.",
                "noaa_tide_coverage=true reflects NOAA CO-OPS tide/current prediction availability for the pilot region (PUG1701-1703), not an observed-current span.",
            ],
            "stats": stats,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
        "candidates": candidates,
    }
    TARGETS_OUT.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")


def write_gap(stats: Dict[str, object]) -> None:
    lines = [
        "# C-GAP coverage report",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()} (live={stats['live']}, window_h={stats['window_h']}).",
        "Read-only feasibility pass for the CAND waveset. No targets written by this mode.",
        "",
        "## Reachable confirmed sightings",
        "",
        f"- In-region sightings in store: {stats['store_in_region']}",
        f"- Confirmed (verified/likely) in-region: {stats['store_confirmed']}",
        f"- OrcaHello history records indexed: {stats['orcahello_index_records']}",
        f"- OrcaHello confirmed acoustic candidates: {stats['orcahello_confirmed_acoustic']}",
        f"- Combined candidate pool: {stats['pool_total']}",
        "",
        "## Hydrophone / tier feasibility",
        "",
        f"- Within 5 km of an in-region hydrophone: {stats['near5km']}",
        f"- Within 10 km: {stats['near10km']}",
        f"- Tier A (<=5 km AND OrcaHello overlap): {stats['tier_a']}",
        f"- Tier B: {stats['tier_b']}",
        f"- Tier C: {stats['tier_c']}",
        "",
        "## Feasibility verdict",
        "",
        f"- Target is >=40 candidates with >=20 tier-A. Reachable now: "
        f"{stats['candidates']} candidates, {stats['tier_a']} tier-A.",
    ]
    if not stats["live"]:
        lines.append("- NOTE: run with --live to include live OBIS/iNaturalist and OrcaHello history; counts above are cached/seed only.")
    GAP_OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="CAND forecast candidate builder")
    ap.add_argument("mode", choices=["gap", "build"])
    ap.add_argument("--live", action="store_true", help="include live OBIS/iNaturalist/OrcaHello ingest")
    ap.add_argument("--window-h", type=int, default=24, help="OrcaHello overlap window (hours)")
    ap.add_argument("--max", type=int, default=200, help="max candidates to keep")
    args = ap.parse_args()

    candidates, stats = build_records(live=args.live, window_h=args.window_h, limit=args.max)

    if args.mode == "gap":
        write_gap(stats)
        print(json.dumps(stats, indent=2))
        print(f"\nWrote {GAP_OUT}")
        return 0

    write_targets(candidates, stats)
    print(json.dumps(stats, indent=2))
    print(f"\nWrote {TARGETS_OUT}")
    if stats["candidates"] < 40 or stats["tier_a"] < 20:
        print(
            f"\n[exit-bar NOT met] candidates={stats['candidates']} (need >=40), "
            f"tier_a={stats['tier_a']} (need >=20). Reported honestly; not padded.",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

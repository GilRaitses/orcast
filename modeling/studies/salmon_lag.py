"""M-L3 helper: Chinook run-timing lag scan against daily acoustic presence.

Runnable as:
    python -m modeling.studies.salmon_lag

Pure-stdlib analysis code. It consumes:
  - OrcaHello cached detections from modeling.studies.common.load_orcahello_index()
  - Salmon run-timing series from src.aws_backend.sources.salmon.SalmonRunAdapter

It writes an informational report to modeling/studies/reports/salmon_lag.json.
"""
from __future__ import annotations

import json
import math
import random
from dataclasses import asdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from .common import GATE_INSUFFICIENT, GATE_PASS, GATE_WITHHELD, GateResult, load_orcahello_index

try:
    from src.aws_backend.sources.salmon import SalmonRunAdapter
except Exception as exc:  # pragma: no cover - exercised only when optional deps are absent.
    SalmonRunAdapter = None  # type: ignore[assignment]
    _IMPORT_ERROR = f"{type(exc).__name__}: {exc}"
else:
    _IMPORT_ERROR = ""

REPORT_PATH = Path(__file__).resolve().parent / "reports" / "salmon_lag.json"
LAG_MIN = -30
LAG_MAX = 30
N_PERMUTATIONS = 1000
PERMUTATION_SEED = 20260627


def _round(v: float) -> float:
    return round(float(v), 6)


def _iter_days(start: date, end: date) -> List[date]:
    out: List[date] = []
    cur = start
    while cur <= end:
        out.append(cur)
        cur += timedelta(days=1)
    return out


def _aggregate_daily_presence(records: Sequence[Dict[str, object]]) -> Tuple[List[date], List[float], Dict[str, int]]:
    counts: Dict[date, int] = {}
    for row in records:
        ts = row.get("t")
        if isinstance(ts, datetime):
            dt = ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)
        else:
            continue
        day = dt.date()
        counts[day] = counts.get(day, 0) + 1

    if not counts:
        return [], [], {}

    span_days = _iter_days(min(counts), max(counts))
    presence = [1.0 if counts.get(day, 0) > 0 else 0.0 for day in span_days]
    count_map = {d.isoformat(): counts.get(d, 0) for d in span_days}
    return span_days, presence, count_map


def _climatology_series_local(year: int) -> List[Dict[str, object]]:
    """Stdlib fallback that mirrors salmon.py's documented climatology shape."""
    primary_peak = 201
    primary_width = 24.0
    secondary_peak = 248
    secondary_width = 18.0
    secondary_weight = 0.35
    season_start = 60
    season_end = 320

    def gaussian(x: float, mu: float, sigma: float) -> float:
        return math.exp(-0.5 * ((x - mu) / sigma) ** 2)

    raw: Dict[str, float] = {}
    for doy in range(season_start, season_end + 1):
        d = date(year, 1, 1) + timedelta(days=doy - 1)
        val = gaussian(doy, primary_peak, primary_width) + secondary_weight * gaussian(
            doy, secondary_peak, secondary_width
        )
        raw[d.isoformat()] = val

    if not raw:
        return []
    lo = min(raw.values())
    hi = max(raw.values())
    span = hi - lo
    if span <= 0:
        norm = {k: 1.0 for k in raw}
    else:
        norm = {k: (v - lo) / span for k, v in raw.items()}

    out: List[Dict[str, object]] = []
    for iso in sorted(norm):
        idx = max(0.0, min(1.0, float(norm[iso])))
        out.append(
            {
                "t": iso,
                "fraser_index": idx,
                "columbia_index": None,
                "run_index": idx,
                "source": "climatology_fallback",
                "source_url": "orcast://salmon/climatology_fallback",
            }
        )
    return out


def _fetch_run_series_for_year(year: int, adapter: Optional[object]) -> Tuple[List[Dict[str, object]], str, Optional[str]]:
    if adapter is None:
        return _climatology_series_local(year), "climatology_fallback", "adapter_import_failed"

    try:
        series = adapter.fetch_run_index(year)  # type: ignore[attr-defined]
    except Exception as exc:
        try:
            series = adapter._climatology_series(year)  # type: ignore[attr-defined]
            return series, "climatology_fallback", f"live_fetch_failed:{type(exc).__name__}"
        except Exception:
            return _climatology_series_local(year), "climatology_fallback", f"live_fetch_failed:{type(exc).__name__}"

    if not series:
        try:
            series = adapter._climatology_series(year)  # type: ignore[attr-defined]
            return series, "climatology_fallback", "empty_live_series"
        except Exception:
            return _climatology_series_local(year), "climatology_fallback", "empty_live_series"

    source = str(series[0].get("source", "unknown"))
    return series, source, None


def _build_run_index(days: Sequence[date]) -> Tuple[List[float], Dict[str, str], List[str]]:
    if not days:
        return [], {}, []

    years = sorted({d.year for d in days})
    adapter = SalmonRunAdapter() if SalmonRunAdapter is not None else None
    run_by_day: Dict[str, float] = {}
    source_by_year: Dict[str, str] = {}
    notes: List[str] = []

    if _IMPORT_ERROR:
        notes.append(f"salmon_adapter_import_error:{_IMPORT_ERROR}")

    for year in years:
        series, source, note = _fetch_run_series_for_year(year, adapter)
        source_by_year[str(year)] = source
        if note:
            notes.append(f"{year}:{note}")
        for row in series:
            iso = str(row.get("t", ""))
            try:
                idx = float(row.get("run_index", 0.0))
            except (TypeError, ValueError):
                idx = 0.0
            run_by_day[iso] = max(0.0, min(1.0, idx))

    out = [run_by_day.get(d.isoformat(), 0.0) for d in days]
    return out, source_by_year, notes


def _pearson(xs: Sequence[float], ys: Sequence[float]) -> float:
    n = len(xs)
    if n != len(ys) or n < 2:
        return 0.0
    mx = sum(xs) / n
    my = sum(ys) / n
    cov = 0.0
    vx = 0.0
    vy = 0.0
    for x, y in zip(xs, ys):
        dx = x - mx
        dy = y - my
        cov += dx * dy
        vx += dx * dx
        vy += dy * dy
    if vx <= 0 or vy <= 0:
        return 0.0
    return cov / math.sqrt(vx * vy)


def _lag_corr(run_index: Sequence[float], presence: Sequence[float], lag_days: int) -> float:
    xs: List[float] = []
    ys: List[float] = []
    n = len(run_index)
    for i in range(n):
        j = i - lag_days
        if j < 0 or j >= n:
            continue
        xs.append(run_index[j])
        ys.append(presence[i])
    return _pearson(xs, ys)


def _best_lag(run_index: Sequence[float], presence: Sequence[float], lag_min: int, lag_max: int) -> Tuple[int, float, Dict[int, float]]:
    best_lag = 0
    best_corr = 0.0
    lag_to_corr: Dict[int, float] = {}
    for lag in range(lag_min, lag_max + 1):
        corr = _lag_corr(run_index, presence, lag)
        lag_to_corr[lag] = corr
        if abs(corr) > abs(best_corr):
            best_corr = corr
            best_lag = lag
    return best_lag, best_corr, lag_to_corr


def _circular_shift(values: Sequence[float], shift: int) -> List[float]:
    n = len(values)
    if n == 0:
        return []
    s = shift % n
    if s == 0:
        return list(values)
    return list(values[s:]) + list(values[:s])


def _permutation_null(
    run_index: Sequence[float],
    presence: Sequence[float],
    lag_min: int,
    lag_max: int,
    permutations: int,
    seed: int,
) -> Tuple[float, List[float], float, float]:
    rng = random.Random(seed)
    if len(presence) < 3:
        return 1.0, [], 0.0, 0.0

    obs_lag, obs_corr, _ = _best_lag(run_index, presence, lag_min, lag_max)
    obs_abs = abs(obs_corr)

    null_best_abs: List[float] = []
    for _ in range(permutations):
        shift = rng.randrange(1, len(presence))
        shifted = _circular_shift(presence, shift)
        _, corr, _ = _best_lag(run_index, shifted, lag_min, lag_max)
        null_best_abs.append(abs(corr))

    ge = sum(1 for v in null_best_abs if v >= obs_abs)
    p_value = (ge + 1.0) / (len(null_best_abs) + 1.0)
    if not null_best_abs:
        return p_value, null_best_abs, 0.0, 0.0
    mean_null = sum(null_best_abs) / len(null_best_abs)
    var_null = sum((v - mean_null) ** 2 for v in null_best_abs) / len(null_best_abs)
    std_null = math.sqrt(var_null)
    return p_value, null_best_abs, mean_null, std_null


def _source_summary(source_by_year: Dict[str, str]) -> Tuple[str, bool]:
    if not source_by_year:
        return "unknown", False
    labels = sorted(set(source_by_year.values()))
    if len(labels) == 1:
        label = labels[0]
    else:
        label = ",".join(labels)
    real_only = all(src not in {"climatology_fallback", "unknown"} for src in source_by_year.values())
    return label, real_only


def _write_payload(result: GateResult, path: Path = REPORT_PATH) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = asdict(result)
    payload["generated_at"] = datetime.now(timezone.utc).isoformat()
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def run(write_json: bool = True) -> GateResult:
    records = load_orcahello_index()
    days, presence, daily_counts = _aggregate_daily_presence(records)
    if not days:
        result = GateResult(
            level=3,
            name="salmon_lag",
            status=GATE_INSUFFICIENT,
            metrics={"records": 0},
            reason="No OrcaHello detections found in cache; cannot run lag scan.",
        )
        if write_json:
            _write_payload(result)
        return result

    run_index, source_by_year, notes = _build_run_index(days)
    source_label, source_is_real = _source_summary(source_by_year)
    best_lag, best_corr, lag_to_corr = _best_lag(run_index, presence, LAG_MIN, LAG_MAX)
    p_value, null_best_abs, mean_null, std_null = _permutation_null(
        run_index=run_index,
        presence=presence,
        lag_min=LAG_MIN,
        lag_max=LAG_MAX,
        permutations=N_PERMUTATIONS,
        seed=PERMUTATION_SEED,
    )
    effect_delta = abs(best_corr) - mean_null
    effect_z = (effect_delta / std_null) if std_null > 0 else 0.0

    if source_is_real and p_value < 0.05:
        status = GATE_PASS
        reason = (
            "Lag scan finds a non-null run-timing alignment signal with a real salmon feed "
            f"(best lag {best_lag:+d} days, r={best_corr:.3f}, p={p_value:.4f})."
        )
    elif not source_is_real:
        status = GATE_WITHHELD
        reason = (
            "Lag scan is informational only because salmon source includes climatology fallback; "
            "signal may be suggestive but cannot earn k_salmon gate credit on a placeholder feed."
        )
    else:
        status = GATE_WITHHELD
        reason = (
            "Lag scan did not beat the permutation null at p<0.05 with real-feed-only criteria; "
            "k_salmon remains withheld."
        )

    metrics = {
        "detection_span": {
            "records": len(records),
            "start": days[0].isoformat(),
            "end": days[-1].isoformat(),
            "n_days": len(days),
            "days_with_presence": int(sum(1 for v in presence if v > 0)),
            "daily_presence_mode": "binary",
        },
        "run_index": {
            "source": source_label,
            "source_by_year": source_by_year,
            "real_feed_only": source_is_real,
            "notes": notes,
        },
        "lag_scan": {
            "lag_range_days": [LAG_MIN, LAG_MAX],
            "best_lag_days": int(best_lag),
            "best_correlation": _round(best_corr),
            "best_abs_correlation": _round(abs(best_corr)),
            "permutations": N_PERMUTATIONS,
            "null_model": "circular_shift_presence",
            "null_best_abs_mean": _round(mean_null),
            "null_best_abs_std": _round(std_null),
            "p_value": _round(p_value),
            "effect_size_delta_abs": _round(effect_delta),
            "effect_size_z": _round(effect_z),
            "lag_correlations": {str(k): _round(v) for k, v in lag_to_corr.items()},
            "daily_presence_counts": daily_counts,
        },
    }
    result = GateResult(level=3, name="salmon_lag", status=status, metrics=metrics, reason=reason)
    if write_json:
        _write_payload(result)
    return result


if __name__ == "__main__":
    res = run(write_json=True)
    lag = (res.metrics.get("lag_scan", {}) or {})
    run_idx = (res.metrics.get("run_index", {}) or {})
    print(
        "M-L3 salmon lag:"
        f" {res.status} source={run_idx.get('source')} "
        f"best_lag={lag.get('best_lag_days')}d "
        f"r={lag.get('best_correlation')} p={lag.get('p_value')} -> {REPORT_PATH}"
    )
    print(f"  {res.reason}")

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

# Stock-alignment gate (B.3 honesty). A real feed only earns k_salmon credit if
# its dominant run is the Fraser SUMMER Chinook stock that SRKW chiefly target.
# Albion (Fraser/DFO) is that stock. DART (Columbia/Bonneville) is a real,
# parseable feed but its dominant peak is the Columbia FALL run, a DIFFERENT
# stock; it is a proxy/secondary source, not stock-aligned, so a real-but-DART
# signal that beats the null still leaves L3 withheld with the mismatch reason.
_STOCK_ALIGNED_SOURCES = {"albion"}

# ---------------------------------------------------------------------------
# PRE-REGISTRATION (item 2, W4). These constants fix the hypothesis BEFORE the
# conditioned scan so it is not window-shopped (research/L3_conditioning.md
# caveat 1: the Jun-Sep window is only honest if pre-specified). They are the
# biological hypothesis from RB: SRKW core-summer presence (Jun-Sep) couples to
# the Fraser-summer Chinook run, and the RUN LEADS PRESENCE (a +lag only).
#
# Lag sign is fixed to non-negative (run_index[i-lag] vs presence[i], lag >= 0),
# so the conditioned scan searches only +lags. This is a one-sided pre-registered
# search; its multiplicity (over +lags) is already absorbed by the best-|corr|
# permutation statistic. The window choice is NOT in the null, so it is fixed here.
PREREG_SUMMER_MONTHS: Tuple[int, ...] = (6, 7, 8, 9)  # Jun-Sep, fixed a priori
PREREG_WINDOW_LABEL = "Jun-Sep (SRKW core-summer presence window)"
PREREG_LAG_SIGN = "run_leads_presence_nonnegative"  # +lag only
PREREG_LAG_MIN = 0
PREREG_LAG_MAX = 30


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


# ---------------------------------------------------------------------------
# Masked lag machinery for the PRE-REGISTERED summer-conditioned scan.
# Mirrors the read-only prototype in research/L3_conditioning.md (Agent RB):
# the season restriction is a MASKED correlation -- off-season days are dropped
# from the correlation only, while lag indexing stays on the full contiguous
# daily array (so a +20-day lag never crosses a season seam) and the
# circular-shift null is re-scored under the same mask. Same null FAMILY as the
# pooled baseline so the conditioned and pooled numbers are directly comparable.
def _lag_corr_masked(
    run_index: Sequence[float],
    presence: Sequence[float],
    lag_days: int,
    mask: Sequence[bool],
) -> float:
    xs: List[float] = []
    ys: List[float] = []
    n = len(run_index)
    for i in range(n):
        if not mask[i]:
            continue
        j = i - lag_days
        if j < 0 or j >= n:
            continue
        xs.append(run_index[j])
        ys.append(presence[i])
    return _pearson(xs, ys)


def _best_lag_masked(
    run_index: Sequence[float],
    presence: Sequence[float],
    mask: Sequence[bool],
    lag_min: int,
    lag_max: int,
) -> Tuple[int, float, Dict[int, float]]:
    best_lag = lag_min
    best_corr = 0.0
    lag_to_corr: Dict[int, float] = {}
    for lag in range(lag_min, lag_max + 1):
        corr = _lag_corr_masked(run_index, presence, lag, mask)
        lag_to_corr[lag] = corr
        if abs(corr) > abs(best_corr):
            best_corr = corr
            best_lag = lag
    return best_lag, best_corr, lag_to_corr


def _permutation_null_masked(
    run_index: Sequence[float],
    presence: Sequence[float],
    mask: Sequence[bool],
    lag_min: int,
    lag_max: int,
    permutations: int,
    seed: int,
) -> Tuple[float, int, float, float, float, int]:
    """Circular-shift presence over the FULL contiguous array (same null family
    as the pooled baseline), recompute the masked best-|corr| over [lag_min,
    lag_max]. Returns (p, obs_lag, obs_corr, mean_null, std_null, n_inseason)."""
    rng = random.Random(seed)
    n_in = sum(1 for m in mask if m)
    obs_lag, obs_corr, _ = _best_lag_masked(run_index, presence, mask, lag_min, lag_max)
    obs_abs = abs(obs_corr)
    if n_in < 3 or len(presence) < 3:
        return 1.0, obs_lag, obs_corr, 0.0, 0.0, n_in
    null_abs: List[float] = []
    for _ in range(permutations):
        shift = rng.randrange(1, len(presence))
        shifted = _circular_shift(presence, shift)
        _, corr, _ = _best_lag_masked(run_index, shifted, mask, lag_min, lag_max)
        null_abs.append(abs(corr))
    ge = sum(1 for v in null_abs if v >= obs_abs)
    p_value = (ge + 1.0) / (len(null_abs) + 1.0)
    mean_null = sum(null_abs) / len(null_abs)
    var = sum((v - mean_null) ** 2 for v in null_abs) / len(null_abs)
    return p_value, obs_lag, obs_corr, mean_null, math.sqrt(var), n_in


def _summer_presence_days_by_year(
    days: Sequence[date], presence: Sequence[float], months: Sequence[int]
) -> Dict[int, int]:
    month_set = set(months)
    out: Dict[int, int] = {}
    for d, p in zip(days, presence):
        if d.month in month_set and p > 0:
            out[d.year] = out.get(d.year, 0) + 1
    return out


def _summer_conditioned_prereg(
    days: Sequence[date],
    presence: Sequence[float],
    run_index: Sequence[float],
    daily_counts: Dict[str, int],
    source_is_real: bool,
    stock_aligned: bool,
) -> Dict[str, object]:
    """PRE-REGISTERED, summer-conditioned scan + held-out-year out-of-sample test.

    EXPLORATORY by construction (window multiplicity already discounted by
    pre-registration; small summer presence-day counts; still binary presence).
    Does NOT promote: the held-out verdict only FLAGS for an operator/supervisor
    decision, it never sets the gate to pass.
    """
    months = PREREG_SUMMER_MONTHS
    lag_min, lag_max = PREREG_LAG_MIN, PREREG_LAG_MAX
    summer_mask = [d.month in months for d in days]

    # In-sample pre-registered scan over ALL years' summer days (exploratory).
    p_all, lag_all, corr_all, mean_all, std_all, n_in_all = _permutation_null_masked(
        run_index, presence, summer_mask, lag_min, lag_max, N_PERMUTATIONS, PERMUTATION_SEED
    )
    z_all = (abs(corr_all) - mean_all) / std_all if std_all > 0 else 0.0
    pres_in_all = int(sum(1 for d, p in zip(days, presence) if d.month in months and p > 0))

    # Held-out-year choice: the most data-rich summer-detection year (state it).
    pres_by_year = _summer_presence_days_by_year(days, presence, months)
    if pres_by_year:
        held_out_year = max(pres_by_year, key=lambda y: pres_by_year[y])
    else:
        held_out_year = None

    held_out: Dict[str, object] = {}
    if held_out_year is not None:
        # Choose the lag OUT-OF-SAMPLE: fix it from the TRAINING years (all summer
        # days except the held-out year), then evaluate the held-out year at that
        # fixed lag. Nothing is selected on the held-out year.
        train_mask = [
            d.month in months and d.year != held_out_year for d in days
        ]
        train_lag, train_corr, _ = _best_lag_masked(
            run_index, presence, train_mask, lag_min, lag_max
        )
        n_train_pres = int(
            sum(1 for d, p in zip(days, presence) if d.month in months and d.year != held_out_year and p > 0)
        )

        # Held-out evaluation at the fixed (training-selected) lag only -- no lag
        # search on the held-out year. Same full-array circular-shift null family,
        # masked to the held-out year's summer days, single lag.
        held_mask = [d.month in months and d.year == held_out_year for d in days]
        p_ho, _lag_ho, corr_ho, mean_ho, std_ho, n_in_ho = _permutation_null_masked(
            run_index, presence, held_mask, train_lag, train_lag, N_PERMUTATIONS, PERMUTATION_SEED
        )
        z_ho = (abs(corr_ho) - mean_ho) / std_ho if std_ho > 0 else 0.0
        held_pres = int(pres_by_year.get(held_out_year, 0))
        beats_null_ho = bool(p_ho < 0.05)
        held_out = {
            "held_out_year": int(held_out_year),
            "selection_rule": "most data-rich summer-detection year (max Jun-Sep presence-days)",
            "summer_presence_days_by_year": {str(k): int(v) for k, v in sorted(pres_by_year.items())},
            "lag_fixed_from_training_years_days": int(train_lag),
            "lag_selection": "lag chosen out-of-sample on TRAINING years (all summer days except held-out); held-out evaluated at that fixed lag",
            "training_best_correlation": _round(train_corr),
            "training_summer_presence_days": n_train_pres,
            "out_of_sample_correlation": _round(corr_ho),
            "out_of_sample_abs_correlation": _round(abs(corr_ho)),
            "out_of_sample_p_value": _round(p_ho),
            "null_abs_mean": _round(mean_ho),
            "null_abs_std": _round(std_ho),
            "effect_z": _round(z_ho),
            "held_out_summer_presence_days": held_pres,
            "held_out_inseason_days": int(n_in_ho),
            "beats_null_p05": beats_null_ho,
            "low_power_note": (
                "held-out summer presence-day count is small; a single-year, single-lag "
                "out-of-sample test has low power, so a non-significant result is expected "
                "and does not refute the in-sample signal."
                if held_pres < 10 else ""
            ),
        }
    else:
        beats_null_ho = False

    eligible_for_flag = bool(source_is_real and stock_aligned)
    flag_for_operator_decision = bool(eligible_for_flag and beats_null_ho)

    # Leave-one-year-out SENSITIVITY (informational): does the held-out verdict
    # depend on the single most-data-rich-year choice? For every year with >=3
    # summer presence-days, hold it out, fix the lag on the remaining training
    # years, and evaluate that year out-of-sample. This does NOT change the
    # verdict logic; it tells the operator whether the FLAG is robust or fragile.
    loyo: List[Dict[str, object]] = []
    n_loyo_beats = 0
    for y in sorted(pres_by_year):
        if pres_by_year[y] < 3:
            continue
        tr_mask = [d.month in months and d.year != y for d in days]
        tr_lag, _tr_corr, _ = _best_lag_masked(run_index, presence, tr_mask, lag_min, lag_max)
        y_mask = [d.month in months and d.year == y for d in days]
        p_y, _l_y, corr_y, _m_y, _s_y, n_in_y = _permutation_null_masked(
            run_index, presence, y_mask, tr_lag, tr_lag, N_PERMUTATIONS, PERMUTATION_SEED
        )
        beats_y = bool(p_y < 0.05)
        if beats_y:
            n_loyo_beats += 1
        loyo.append({
            "held_out_year": int(y),
            "summer_presence_days": int(pres_by_year[y]),
            "lag_fixed_from_training_years_days": int(tr_lag),
            "out_of_sample_correlation": _round(corr_y),
            "out_of_sample_p_value": _round(p_y),
            "beats_null_p05": beats_y,
        })

    # Optional, INFORMATIONAL ONLY (RA owed a summer re-test of counts): re-run the
    # response variable as daily COUNTS on the Jun-Sep window. Does NOT change the
    # verdict logic (L3_response_variable.md: counts do not help pooled; this only
    # checks whether they help within the conditioned window).
    counts_series = [float(daily_counts.get(d.isoformat(), 0)) for d in days]
    p_cnt, lag_cnt, corr_cnt, mean_cnt, std_cnt, _n_cnt = _permutation_null_masked(
        run_index, counts_series, summer_mask, lag_min, lag_max, N_PERMUTATIONS, PERMUTATION_SEED
    )
    z_cnt = (abs(corr_cnt) - mean_cnt) / std_cnt if std_cnt > 0 else 0.0

    return {
        "label": "PRE-REGISTERED summer-conditioned scan (EXPLORATORY, separate from the full-span scan above)",
        "exploratory": True,
        "pre_registration": {
            "window_months": list(months),
            "window_label": PREREG_WINDOW_LABEL,
            "lag_sign": PREREG_LAG_SIGN,
            "lag_range_days": [lag_min, lag_max],
            "fixed_before_scan": True,
            "response_variable": "binary daily presence",
            "null_model": "circular_shift_presence_masked",
            "permutations": N_PERMUTATIONS,
            "seed": PERMUTATION_SEED,
            "caveats": [
                "window multiplicity (Jun-Sep is one biological window; pre-registration is what makes it honest)",
                "small support: 36-63 summer presence-days, mostly orcasound_lab 2020-2021",
                "still binary presence; provenance-mixed mosaic; +lag direction is shape-driven, not a resolved interval",
            ],
        },
        "in_sample_all_years": {
            "best_lag_days": int(lag_all),
            "best_correlation": _round(corr_all),
            "best_abs_correlation": _round(abs(corr_all)),
            "p_value": _round(p_all),
            "beats_null_p05": bool(p_all < 0.05),
            "null_abs_mean": _round(mean_all),
            "null_abs_std": _round(std_all),
            "effect_z": _round(z_all),
            "inseason_days": int(n_in_all),
            "summer_presence_days": pres_in_all,
        },
        "held_out_year_eval": held_out,
        "held_out_loyo_sensitivity": {
            "informational_only": True,
            "min_summer_presence_days": 3,
            "n_years_evaluated": len(loyo),
            "n_years_beat_null_p05": n_loyo_beats,
            "per_year": loyo,
            "note": (
                "leave-one-year-out robustness check for the FLAG; does not change the verdict "
                "(verdict rests on the stated primary held-out year). Few summer presence-days "
                "per year means most single-year tests are low-power."
            ),
        },
        "optional_counts_summer": {
            "informational_only": True,
            "response_variable": "daily counts (raw)",
            "best_lag_days": int(lag_cnt),
            "best_correlation": _round(corr_cnt),
            "p_value": _round(p_cnt),
            "beats_null_p05": bool(p_cnt < 0.05),
            "effect_z": _round(z_cnt),
            "note": "RA summer re-test; does NOT change the verdict logic (pooled counts dead-end, L3_response_variable.md).",
        },
        "verdict": {
            "eligible_for_flag": eligible_for_flag,
            "held_out_beats_null_p05": bool(beats_null_ho),
            "flag_for_operator_decision": flag_for_operator_decision,
            "l3_status": GATE_WITHHELD,
            "note": (
                "FLAG-FOR-DECISION: held-out year beat the pre-registered null; this does NOT "
                "self-promote -- it is surfaced for an operator/supervisor decision (B.1)."
                if flag_for_operator_decision
                else "WITHHELD: held-out year did not beat the pre-registered null (or feed not real/stock-aligned). No promotion."
            ),
        },
    }


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


def _stock_aligned(source_by_year: Dict[str, str]) -> bool:
    """True only if every real source is a Fraser-summer-Chinook (SRKW-target) feed.

    DART (Columbia/Bonneville fall run) is real but NOT stock-aligned; it cannot
    earn k_salmon credit on its own even if it beats the permutation null.
    """
    srcs = set(source_by_year.values())
    if not srcs:
        return False
    return srcs <= _STOCK_ALIGNED_SOURCES


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
    stock_aligned = _stock_aligned(source_by_year)
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

    if source_is_real and stock_aligned and p_value < 0.05:
        status = GATE_PASS
        reason = (
            "Lag scan finds a non-null run-timing alignment signal with a real, stock-aligned "
            f"(Fraser-summer Chinook) salmon feed (best lag {best_lag:+d} days, r={best_corr:.3f}, "
            f"p={p_value:.4f})."
        )
    elif not source_is_real:
        status = GATE_WITHHELD
        reason = (
            "Lag scan is informational only because salmon source includes climatology fallback; "
            "signal may be suggestive but cannot earn k_salmon gate credit on a placeholder feed."
        )
    elif source_is_real and not stock_aligned:
        status = GATE_WITHHELD
        null_clause = (
            f"and it does NOT beat the permutation null (p={p_value:.4f} >= 0.05)"
            if p_value >= 0.05
            else f"and although it beats the permutation null (p={p_value:.4f} < 0.05)"
        )
        reason = (
            f"Lag scan ran on a REAL feed (source={source_label}) "
            f"(best lag {best_lag:+d} days, r={best_corr:.3f}, p={p_value:.4f}), {null_clause}, "
            "the feed is STOCK-MISMATCHED: DART (Columbia/Bonneville) is dominated by the Columbia "
            "FALL Chinook run, a different stock than the Fraser SUMMER Chinook that SRKW chiefly "
            "target. A Columbia-fall proxy cannot earn k_salmon credit; L3 stays withheld pending a "
            "stock-aligned (Fraser) feed."
        )
    else:
        status = GATE_WITHHELD
        reason = (
            "Lag scan did not beat the permutation null at p<0.05 with real-feed-only criteria; "
            "k_salmon remains withheld."
        )

    summer_conditioned = _summer_conditioned_prereg(
        days=days,
        presence=presence,
        run_index=run_index,
        daily_counts=daily_counts,
        source_is_real=source_is_real,
        stock_aligned=stock_aligned,
    )
    verdict = summer_conditioned.get("verdict", {}) or {}
    if verdict.get("flag_for_operator_decision"):
        ho = summer_conditioned.get("held_out_year_eval", {}) or {}
        reason = (
            reason
            + " PRE-REGISTERED SUMMER (EXPLORATORY, FLAG-FOR-DECISION): the held-out year "
            f"{ho.get('held_out_year')} beat the pre-registered Jun-Sep null at the training-fixed "
            f"lag {ho.get('lag_fixed_from_training_years_days')}d "
            f"(r={ho.get('out_of_sample_correlation')}, p={ho.get('out_of_sample_p_value')}). "
            "This does NOT self-promote; it is surfaced for an operator/supervisor decision (B.1). "
            "L3 stays WITHHELD pending that decision."
        )
    else:
        insamp = summer_conditioned.get("in_sample_all_years", {}) or {}
        reason = (
            reason
            + " PRE-REGISTERED SUMMER (EXPLORATORY): Jun-Sep in-sample best lag "
            f"{insamp.get('best_lag_days')}d r={insamp.get('best_correlation')} "
            f"p={insamp.get('p_value')}; held-out year did NOT beat the null out-of-sample. "
            "L3 stays WITHHELD (no promotion)."
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
            "stock_aligned": stock_aligned,
            "stock_note": (
                "stock_aligned=True requires a Fraser-summer-Chinook (SRKW-target) feed (Albion). "
                "DART (Columbia/Bonneville) is the Columbia fall run: real and parseable but a "
                "different stock, so stock_aligned=False and it cannot earn k_salmon credit alone."
            ),
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
            "beats_permutation_null": bool(p_value < 0.05),
            "effect_size_delta_abs": _round(effect_delta),
            "effect_size_z": _round(effect_z),
            "lag_correlations": {str(k): _round(v) for k, v in lag_to_corr.items()},
            "daily_presence_counts": daily_counts,
        },
        "summer_conditioned_prereg": summer_conditioned,
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
    sc = (res.metrics.get("summer_conditioned_prereg", {}) or {})
    insamp = (sc.get("in_sample_all_years", {}) or {})
    ho = (sc.get("held_out_year_eval", {}) or {})
    verdict = (sc.get("verdict", {}) or {})
    print(
        "  [PRE-REG summer Jun-Sep, EXPLORATORY] in-sample"
        f" lag={insamp.get('best_lag_days')}d r={insamp.get('best_correlation')}"
        f" p={insamp.get('p_value')} (presence_days={insamp.get('summer_presence_days')})"
    )
    print(
        f"  [held-out year {ho.get('held_out_year')} @ training-lag {ho.get('lag_fixed_from_training_years_days')}d]"
        f" r={ho.get('out_of_sample_correlation')} p={ho.get('out_of_sample_p_value')}"
        f" beats_null={ho.get('beats_null_p05')} (summer_presence_days={ho.get('held_out_summer_presence_days')})"
    )
    print(
        f"  [verdict] flag_for_operator_decision={verdict.get('flag_for_operator_decision')}"
        f" l3_status={verdict.get('l3_status')}"
    )

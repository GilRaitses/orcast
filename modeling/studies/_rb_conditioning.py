"""RB experiment: L3 salmon-lag CONDITIONING (season / per-station / SRKW window).

Read-only reuse of modeling.studies.salmon_lag helpers (imported, NOT edited).
Refit-safety: no fit_kernels import, no S3 write, no model write, no production
store write. Writes only an optional report JSON under studies/reports/.

Conditionings tested (all vs the circular-shift permutation null, same family as
the pooled baseline):
  0. baseline_pooled        - reproduce the charter number (all days, all stations)
  1. season_restricted      - drop off-season zeros (corr over in-season days only)
  2. per_station            - score each station separately
  3. per_station_in_season  - season restriction x per station
  4. srkw_summer_window     - condition on the SRKW summer presence window
"""
from __future__ import annotations

import json
import math
import random
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from modeling.studies.common import load_orcahello_index
from modeling.studies.salmon_lag import (
    LAG_MIN,
    LAG_MAX,
    N_PERMUTATIONS,
    PERMUTATION_SEED,
    _aggregate_daily_presence,
    _best_lag,
    _build_run_index,
    _circular_shift,
    _pearson,
    _permutation_null,
)

REPORT_PATH = Path(__file__).resolve().parent / "reports" / "L3_conditioning.json"

# SRKW summer presence window (core Salish Sea season). Primary Jun-Sep; we also
# report a wider May-Oct sensitivity band.
SRKW_PRIMARY_MONTHS = {6, 7, 8, 9}
SRKW_WIDE_MONTHS = {5, 6, 7, 8, 9, 10}


def _round(v: float) -> float:
    return round(float(v), 6)


# ---- masked lag machinery (thin wrappers over reused _pearson/_circular_shift) ----
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
    lag_min: int = LAG_MIN,
    lag_max: int = LAG_MAX,
) -> Tuple[int, float, Dict[int, float]]:
    best_lag = 0
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
    permutations: int = N_PERMUTATIONS,
    seed: int = PERMUTATION_SEED,
) -> Tuple[float, float, float, int, float]:
    """Circular-shift presence over the FULL contiguous array (reusing
    _circular_shift, the same null family as the pooled baseline), recompute the
    masked best-lag abs-corr. Returns (p, obs_corr, mean_null, n_pairs, std_null)."""
    rng = random.Random(seed)
    n_in = sum(1 for m in mask if m)
    obs_lag, obs_corr, _ = _best_lag_masked(run_index, presence, mask)
    obs_abs = abs(obs_corr)
    if n_in < 3:
        return 1.0, obs_corr, 0.0, n_in, 0.0
    null_abs: List[float] = []
    for _ in range(permutations):
        shift = rng.randrange(1, len(presence))
        shifted = _circular_shift(presence, shift)
        _, corr, _ = _best_lag_masked(run_index, shifted, mask)
        null_abs.append(abs(corr))
    ge = sum(1 for v in null_abs if v >= obs_abs)
    p_value = (ge + 1.0) / (len(null_abs) + 1.0)
    mean_null = sum(null_abs) / len(null_abs)
    var = sum((v - mean_null) ** 2 for v in null_abs) / len(null_abs)
    return p_value, obs_corr, mean_null, n_in, math.sqrt(var)


def _summ(label: str, best_lag: int, corr: float, p: float, mean_null: float,
          std_null: float, n_days: int, n_pres: int, n_pairs: Optional[int] = None) -> Dict[str, object]:
    z = (abs(corr) - mean_null) / std_null if std_null > 0 else 0.0
    return {
        "label": label,
        "best_lag_days": int(best_lag),
        "best_correlation": _round(corr),
        "best_abs_correlation": _round(abs(corr)),
        "p_value": _round(p),
        "beats_null_p05": bool(p < 0.05),
        "null_abs_mean": _round(mean_null),
        "null_abs_std": _round(std_null),
        "effect_z": _round(z),
        "n_days": int(n_days),
        "days_with_presence": int(n_pres),
        "n_inseason_days": int(n_pairs) if n_pairs is not None else int(n_days),
    }


def _run_full_arrays(records) -> Tuple[List[date], List[float], List[float]]:
    days, presence, _ = _aggregate_daily_presence(records)
    run_index, _src, _notes = _build_run_index(days)
    return days, presence, run_index


def main() -> None:
    records = load_orcahello_index()
    print(f"records={len(records)}")

    results: Dict[str, object] = {}

    # ---- 0. baseline pooled (reproduce charter) ----
    days, presence, run_index = _run_full_arrays(records)
    n_pres = int(sum(1 for v in presence if v > 0))
    bl, bc, _ = _best_lag(run_index, presence, LAG_MIN, LAG_MAX)
    p, _na, mean_null, std_null = _permutation_null(
        run_index, presence, LAG_MIN, LAG_MAX, N_PERMUTATIONS, PERMUTATION_SEED
    )
    results["baseline_pooled"] = _summ(
        "baseline_pooled (all days, all stations, binary presence)",
        bl, bc, p, mean_null, std_null, len(days), n_pres,
    )

    # ---- 1. season restriction: drop off-season zeros ----
    # in-season = days where the Albion run index is active (run_index > 0).
    mask_run = [v > 0.0 for v in run_index]
    bl, bc, _ = _best_lag_masked(run_index, presence, mask_run)
    p, _oc, mean_null, n_in, std_null = _permutation_null_masked(run_index, presence, mask_run)
    n_pres_in = int(sum(1 for d, pr, m in zip(days, presence, mask_run) if m and pr > 0))
    results["season_restricted_run_active"] = _summ(
        "season_restricted (corr over days with run_index>0)",
        bl, bc, p, mean_null, std_null, len(days), n_pres_in, n_in,
    )

    # calendar-window variant: Albion active DOY bracket 90..310 (Apr 1 - Nov 6)
    mask_cal = [90 <= d.timetuple().tm_yday <= 310 for d in days]
    bl, bc, _ = _best_lag_masked(run_index, presence, mask_cal)
    p, _oc, mean_null, n_in, std_null = _permutation_null_masked(run_index, presence, mask_cal)
    n_pres_in = int(sum(1 for d, pr, m in zip(days, presence, mask_cal) if m and pr > 0))
    results["season_restricted_doy90_310"] = _summ(
        "season_restricted (calendar DOY 90-310, Apr-Nov)",
        bl, bc, p, mean_null, std_null, len(days), n_pres_in, n_in,
    )

    # ---- 4. SRKW summer window (defined here so per-station can reuse) ----
    for name, months in (("srkw_summer_jun_sep", SRKW_PRIMARY_MONTHS),
                         ("srkw_summer_may_oct", SRKW_WIDE_MONTHS)):
        mask = [d.month in months for d in days]
        bl, bc, _ = _best_lag_masked(run_index, presence, mask)
        p, _oc, mean_null, n_in, std_null = _permutation_null_masked(run_index, presence, mask)
        n_pres_in = int(sum(1 for d, pr, m in zip(days, presence, mask) if m and pr > 0))
        results[name] = _summ(
            f"srkw_summer_window months={sorted(months)}",
            bl, bc, p, mean_null, std_null, len(days), n_pres_in, n_in,
        )

    # ---- 2 & 3. per-station (and per-station in-season) ----
    stations = ["orcasound_lab", "andrews_bay", "north_san_juan_channel", "haro_strait"]
    per_station: Dict[str, object] = {}
    for st in stations:
        st_records = [r for r in records if r.get("key") == st]
        if len(st_records) < 3:
            per_station[st] = {
                "n_records": len(st_records),
                "note": "absent from / too sparse in cached OrcaHello index; not scorable",
            }
            continue
        s_days, s_presence, _ = _aggregate_daily_presence(st_records)
        s_run, _src, _notes = _build_run_index(s_days)
        s_npres = int(sum(1 for v in s_presence if v > 0))
        # pooled (all days for that station)
        bl, bc, _ = _best_lag(s_run, s_presence, LAG_MIN, LAG_MAX)
        p, _na, mean_null, std_null = _permutation_null(
            s_run, s_presence, LAG_MIN, LAG_MAX, N_PERMUTATIONS, PERMUTATION_SEED
        )
        pooled = _summ(f"{st} pooled", bl, bc, p, mean_null, std_null, len(s_days), s_npres)
        # in-season (run_index>0)
        s_mask = [v > 0.0 for v in s_run]
        bl, bc, _ = _best_lag_masked(s_run, s_presence, s_mask)
        p, _oc, mean_null, n_in, std_null = _permutation_null_masked(s_run, s_presence, s_mask)
        s_npres_in = int(sum(1 for pr, m in zip(s_presence, s_mask) if m and pr > 0))
        inseason = _summ(f"{st} in-season", bl, bc, p, mean_null, std_null,
                         len(s_days), s_npres_in, n_in)
        per_station[st] = {"pooled": pooled, "in_season": inseason}
    results["per_station"] = per_station

    payload = {
        "study": "L3_conditioning",
        "agent": "RB",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "method": {
            "response": "binary daily presence (matches salmon_lag.py baseline)",
            "run_index": "Albion FOS Fraser-summer Chinook (source=albion all years), via SalmonRunAdapter",
            "lag_range_days": [LAG_MIN, LAG_MAX],
            "null": "circular_shift of presence over full contiguous array; "
                    "best |lag corr| statistic; same null family as baseline",
            "permutations": N_PERMUTATIONS,
            "seed": PERMUTATION_SEED,
            "season_restriction": "masked correlation over in-season days only "
                                  "(off-season zeros dropped from the correlation, "
                                  "lag indexing kept on full contiguous array)",
        },
        "results": results,
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    # ---- console summary ----
    def line(d):
        return (f"lag {d['best_lag_days']:+d}d  r={d['best_correlation']:+.3f}  "
                f"p={d['p_value']:.3f}  z={d['effect_z']:+.2f}  "
                f"in-season_days={d['n_inseason_days']}  pres_in={d['days_with_presence']}")
    print("\n=== L3 conditioning results ===")
    for k in ("baseline_pooled", "season_restricted_run_active",
              "season_restricted_doy90_310", "srkw_summer_jun_sep", "srkw_summer_may_oct"):
        print(f"{k:32s} {line(results[k])}")
    print("\nper-station:")
    for st, v in per_station.items():
        if "pooled" not in v:
            print(f"  {st:26s} {v}")
            continue
        print(f"  {st:26s} POOLED   {line(v['pooled'])}")
        print(f"  {'':26s} INSEASON {line(v['in_season'])}")
    print(f"\nwrote {REPORT_PATH}")


if __name__ == "__main__":
    main()

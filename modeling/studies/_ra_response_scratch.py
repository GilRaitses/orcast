"""RA scratch: L3 response-variable study (counts vs binary presence).

TEMPORARY standalone experiment for research agent RA. Reuses salmon_lag.py
functions READ-ONLY (imports them; does not edit). No fit-pipeline import, no S3,
no model write. Run:

    PYTHONPATH=. .venv-modeling/bin/python -m modeling.studies._ra_response_scratch

Writes modeling/studies/reports/L3_response_variable.json.
"""
from __future__ import annotations

import json
import math
import random
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import numpy as np
import statsmodels.api as sm

# READ-ONLY reuse of the convergence study's machinery (do NOT edit salmon_lag.py).
from modeling.studies.salmon_lag import (
    LAG_MIN,
    LAG_MAX,
    N_PERMUTATIONS,
    PERMUTATION_SEED,
    _aggregate_daily_presence,
    _best_lag,
    _build_run_index,
    _lag_corr,
    _pearson,
    _permutation_null,
    _source_summary,
    _stock_aligned,
)
from modeling.studies.common import load_orcahello_index

REPORT_PATH = Path(__file__).resolve().parent / "reports" / "L3_response_variable.json"


def _round(v: float, n: int = 6) -> float:
    return round(float(v), n)


# --------------------------------------------------------------------------- #
# Data assembly (same source the lag scan uses)
# --------------------------------------------------------------------------- #
def assemble() -> Dict[str, object]:
    records = load_orcahello_index()
    days, presence, count_map = _aggregate_daily_presence(records)
    run_index, source_by_year, notes = _build_run_index(days)
    counts = [float(count_map[d.isoformat()]) for d in days]

    # distinct stations active per day (a crude, ENDOGENOUS effort proxy only).
    stations_by_day: Dict[str, set] = {}
    for row in records:
        ts = row.get("t")
        if not isinstance(ts, datetime):
            continue
        key = str(row.get("key", ""))
        # station = portion of key before the first time component; keep raw key.
        d = (ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)).date().isoformat()
        stations_by_day.setdefault(d, set()).add(key.split("/")[0] if key else "")
    n_stations = [len(stations_by_day.get(d.isoformat(), set())) for d in days]

    source_label, source_is_real = _source_summary(source_by_year)
    stock = _stock_aligned(source_by_year)
    return {
        "records": records,
        "days": days,
        "presence": presence,
        "counts": counts,
        "run_index": run_index,
        "n_stations": n_stations,
        "source_by_year": source_by_year,
        "source_label": source_label,
        "source_is_real": source_is_real,
        "stock_aligned": stock,
        "notes": notes,
    }


# --------------------------------------------------------------------------- #
# Correlation-style formulations (reuse _best_lag + _permutation_null)
# --------------------------------------------------------------------------- #
def corr_formulation(
    run_index: Sequence[float],
    response: Sequence[float],
    label: str,
) -> Dict[str, object]:
    best_lag, best_corr, lag_to_corr = _best_lag(run_index, response, LAG_MIN, LAG_MAX)
    p_value, null_abs, mean_null, std_null = _permutation_null(
        run_index=run_index,
        presence=response,
        lag_min=LAG_MIN,
        lag_max=LAG_MAX,
        permutations=N_PERMUTATIONS,
        seed=PERMUTATION_SEED,
    )
    delta = abs(best_corr) - mean_null
    z = (delta / std_null) if std_null > 0 else 0.0
    return {
        "formulation": label,
        "best_lag_days": int(best_lag),
        "best_correlation": _round(best_corr),
        "best_abs_correlation": _round(abs(best_corr)),
        "null_best_abs_mean": _round(mean_null),
        "null_best_abs_std": _round(std_null),
        "permutations": N_PERMUTATIONS,
        "p_value": _round(p_value),
        "beats_null_p05": bool(p_value < 0.05),
        "effect_size_delta_abs": _round(delta),
        "effect_size_z": _round(z),
        "lag_correlations": {str(k): _round(v) for k, v in lag_to_corr.items()},
    }


def _rank(xs: Sequence[float]) -> List[float]:
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    ranks = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0  # 1-based average rank for ties
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


# --------------------------------------------------------------------------- #
# Count GLM (Poisson IRLS for the fast permutation null; statsmodels NB report)
# --------------------------------------------------------------------------- #
def _season_design(days: Sequence[date], n_harm: int = 2) -> np.ndarray:
    cols = [np.ones(len(days))]
    doy = np.array([d.timetuple().tm_yday for d in days], dtype=float)
    for h in range(1, n_harm + 1):
        ang = 2.0 * math.pi * h * doy / 365.25
        cols.append(np.sin(ang))
        cols.append(np.cos(ang))
    return np.column_stack(cols)


def _poisson_irls(X: np.ndarray, y: np.ndarray, max_iter: int = 50, tol: float = 1e-8) -> Tuple[np.ndarray, float]:
    beta = np.zeros(X.shape[1])
    beta[0] = math.log(max(y.mean(), 1e-6))
    for _ in range(max_iter):
        eta = np.clip(X @ beta, -30, 30)
        mu = np.exp(eta)
        W = mu
        z = eta + (y - mu) / np.clip(mu, 1e-8, None)
        XtW = X.T * W
        try:
            beta_new = np.linalg.solve(XtW @ X, XtW @ z)
        except np.linalg.LinAlgError:
            beta_new = np.linalg.lstsq(XtW @ X, XtW @ z, rcond=None)[0]
        if np.max(np.abs(beta_new - beta)) < tol:
            beta = beta_new
            break
        beta = beta_new
    eta = np.clip(X @ beta, -30, 30)
    mu = np.exp(eta)
    with np.errstate(divide="ignore", invalid="ignore"):
        term = np.where(y > 0, y * np.log(y / mu), 0.0)
    deviance = 2.0 * np.sum(term - (y - mu))
    return beta, float(deviance)


def _lagged_run(run_index: np.ndarray, lag: int, lo: int, hi: int) -> np.ndarray:
    """run_index[i-lag] for i in [lo,hi); matches _lag_corr convention."""
    idx = np.arange(lo, hi) - lag
    return run_index[idx]


def count_glm(
    days: Sequence[date],
    counts: Sequence[float],
    run_index: Sequence[float],
    permutations: int = 500,
) -> Dict[str, object]:
    y_full = np.array(counts, dtype=float)
    run = np.array(run_index, dtype=float)
    n = len(y_full)
    lo, hi = abs(LAG_MIN), n - abs(LAG_MAX)  # fixed window valid for all lags
    y = y_full[lo:hi]
    season = _season_design(days, n_harm=2)[lo:hi]

    # season-only (reduced) deviance, fit once.
    _, dev_reduced = _poisson_irls(season, y)
    _, dev_null = _poisson_irls(np.ones((len(y), 1)), y)

    # observed lag scan: LR = dev_reduced - dev_full at each lag.
    lags = list(range(LAG_MIN, LAG_MAX + 1))
    lr_by_lag: Dict[int, float] = {}
    best_lr = -1.0
    best_lag = 0
    best_dev_full = dev_reduced
    for lag in lags:
        col = _lagged_run(run, lag, lo, hi).reshape(-1, 1)
        X = np.column_stack([season, col])
        _, dev_full = _poisson_irls(X, y)
        lr = dev_reduced - dev_full
        lr_by_lag[lag] = lr
        if lr > best_lr:
            best_lr = lr
            best_lag = lag
            best_dev_full = dev_full

    # circular-shift null on the run-index series; re-run the lag scan; keep max LR.
    rng = random.Random(PERMUTATION_SEED)
    null_best_lr: List[float] = []
    for _ in range(permutations):
        s = rng.randrange(1, n)
        shifted = np.concatenate([run[s:], run[:s]])
        m = -1.0
        for lag in lags:
            col = _lagged_run(shifted, lag, lo, hi).reshape(-1, 1)
            X = np.column_stack([season, col])
            _, dev_full = _poisson_irls(X, y)
            lr = dev_reduced - dev_full
            if lr > m:
                m = lr
        null_best_lr.append(m)
    ge = sum(1 for v in null_best_lr if v >= best_lr)
    p_value = (ge + 1.0) / (len(null_best_lr) + 1.0)
    mean_null = sum(null_best_lr) / len(null_best_lr)
    var_null = sum((v - mean_null) ** 2 for v in null_best_lr) / len(null_best_lr)
    std_null = math.sqrt(var_null)

    # deviance skill of the best-lag full model.
    dev_skill_vs_null = 1.0 - best_dev_full / dev_null if dev_null > 0 else 0.0
    dev_skill_vs_season = 1.0 - best_dev_full / dev_reduced if dev_reduced > 0 else 0.0

    # statsmodels report at the best lag: Poisson + NB coefficient, Wald p, alpha.
    col = _lagged_run(run, best_lag, lo, hi).reshape(-1, 1)
    X = np.column_stack([season, col])
    pois = sm.GLM(y, X, family=sm.families.Poisson()).fit()
    coef_pois = float(pois.params[-1])
    wald_p_pois = float(pois.pvalues[-1])
    pearson_chi2 = float(pois.pearson_chi2)
    df_resid = int(pois.df_resid)
    dispersion = pearson_chi2 / df_resid if df_resid else float("nan")
    nb_report: Dict[str, object] = {}
    try:
        nb = sm.NegativeBinomial(y, X).fit(disp=0, maxiter=200)
        nb_report = {
            "run_index_coef": _round(float(nb.params[-1])),
            "run_index_wald_p": _round(float(nb.pvalues[-1])),
            "alpha_dispersion": _round(float(nb.params[-1] if False else nb.params[-1])),  # placeholder, set below
        }
        # NegativeBinomial appends alpha as the LAST param; run-index is second-to-last.
        nb_report["run_index_coef"] = _round(float(nb.params[-2]))
        nb_report["run_index_wald_p"] = _round(float(nb.pvalues[-2]))
        nb_report["alpha_dispersion"] = _round(float(nb.params[-1]))
        nb_report["converged"] = bool(nb.mle_retvals.get("converged", False))
    except Exception as exc:  # pragma: no cover
        nb_report = {"error": f"{type(exc).__name__}: {exc}"}

    return {
        "formulation": "count_glm_poisson_nb_season",
        "window": {"n_days_used": int(hi - lo), "drop_each_end": int(abs(LAG_MIN))},
        "season_term": "2 annual harmonics (sin/cos x2) + intercept",
        "best_lag_days": int(best_lag),
        "lr_stat_dev_drop": _round(best_lr),
        "deviance_null_intercept": _round(dev_null),
        "deviance_season_only": _round(dev_reduced),
        "deviance_full_best_lag": _round(best_dev_full),
        "deviance_skill_vs_intercept": _round(dev_skill_vs_null),
        "deviance_skill_vs_season": _round(dev_skill_vs_season),
        "poisson_run_index_coef": _round(coef_pois),
        "poisson_run_index_wald_p": _round(wald_p_pois),
        "poisson_dispersion_pearson": _round(dispersion),
        "negbin": nb_report,
        "permutation_null": {
            "model": "circular_shift_run_index_then_lagscan_LR",
            "permutations": permutations,
            "null_best_lr_mean": _round(mean_null),
            "null_best_lr_std": _round(std_null),
            "p_value": _round(p_value),
            "beats_null_p05": bool(p_value < 0.05),
            "effect_size_z": _round((best_lr - mean_null) / std_null if std_null > 0 else 0.0),
        },
        "lr_by_lag": {str(k): _round(v) for k, v in lr_by_lag.items()},
    }


# --------------------------------------------------------------------------- #
def main() -> None:
    data = assemble()
    days = data["days"]
    run_index = data["run_index"]
    presence = data["presence"]
    counts = data["counts"]
    n_stations = data["n_stations"]

    n = len(days)
    nonzero = [c for c in counts if c > 0]
    results: Dict[str, object] = {}

    # 1. binary baseline (reproduce salmon_lag headline).
    results["binary_presence"] = corr_formulation(run_index, presence, "binary_presence")

    # 2a. raw daily counts.
    results["counts_raw"] = corr_formulation(run_index, counts, "counts_raw")

    # 2b. log1p(counts) (tame the heavy tail / spikes).
    log_counts = [math.log1p(c) for c in counts]
    results["counts_log1p"] = corr_formulation(run_index, log_counts, "counts_log1p")

    # 2c. rank (Spearman-style) counts.
    rank_counts = _rank(counts)
    rank_run = _rank(run_index)
    results["counts_rank_spearman"] = corr_formulation(rank_run, rank_counts, "counts_rank_spearman")

    # 3. rate / counts-per-effort.
    #   True independent per-day effort is NOT available for the cached index
    #   (W1 Agent A: station_uptime covers 2026-06-20..27 only, disjoint from the
    #   detection span; haro_strait has no uptime node). So an effort-normalized
    #   rate cannot be computed. As a saturation probe we test count MAGNITUDE on
    #   days with >=1 detection (does intensity track the run index when present),
    #   and a crude ENDOGENOUS n-active-stations normalization on those days.
    pres_idx = [i for i in range(n) if counts[i] > 0]
    cond_counts_full = [0.0] * n
    cond_rate_full = [0.0] * n
    for i in pres_idx:
        cond_counts_full[i] = counts[i]
        cond_rate_full[i] = counts[i] / max(1, n_stations[i])
    # correlate magnitude with lagged run index, restricted to presence days, at
    # the count-scan best lag (report the lag-scan too on the full conditional series).
    results["counts_conditional_on_presence"] = corr_formulation(
        run_index, cond_counts_full, "counts_conditional_on_presence(zeros=offdays)"
    )
    results["rate_per_active_station_proxy"] = corr_formulation(
        run_index, cond_rate_full, "rate_per_active_station_proxy(endogenous)"
    )

    # 4. count GLM.
    results["count_glm"] = count_glm(days, counts, run_index, permutations=500)

    payload = {
        "study": "L3_response_variable",
        "agent": "RA",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "refit_safety": "no fit-pipeline import; no S3; no model write; write_outputs=False semantics",
        "detection_span": {
            "records": len(data["records"]),
            "start": days[0].isoformat(),
            "end": days[-1].isoformat(),
            "n_days": n,
            "days_with_presence": len(nonzero),
            "presence_fraction": _round(len(nonzero) / n),
            "count_mean": _round(sum(counts) / n),
            "count_mean_on_presence_days": _round(sum(nonzero) / len(nonzero)) if nonzero else 0.0,
            "count_max": int(max(counts)),
            "count_var_over_mean_all_days": _round((float(np.var(counts)) / (sum(counts) / n)) if sum(counts) else 0.0),
        },
        "run_index": {
            "source": data["source_label"],
            "source_by_year": data["source_by_year"],
            "real_feed_only": data["source_is_real"],
            "stock_aligned": data["stock_aligned"],
            "notes": data["notes"],
        },
        "lag_scan": {"lag_range_days": [LAG_MIN, LAG_MAX], "permutations_corr": N_PERMUTATIONS},
        "formulations": results,
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    # console summary
    def line(key: str) -> str:
        r = results[key]
        if "p_value" in r:
            return f"  {key:42s} lag={r['best_lag_days']:+d} r={r['best_correlation']:.3f} p={r['p_value']:.4f} {'BEATS' if r['beats_null_p05'] else 'no'}"
        return ""

    print("L3 response-variable study (RA):")
    print(f"  span {days[0]}..{days[-1]}  n_days={n}  presence_days={len(nonzero)} ({100*len(nonzero)/n:.1f}%)")
    print(f"  count mean(all)={sum(counts)/n:.3f}  mean(presence)={sum(nonzero)/len(nonzero):.2f}  max={int(max(counts))}  var/mean={float(np.var(counts))/(sum(counts)/n):.1f}")
    for k in ["binary_presence", "counts_raw", "counts_log1p", "counts_rank_spearman",
              "counts_conditional_on_presence", "rate_per_active_station_proxy"]:
        print(line(k))
    g = results["count_glm"]
    pn = g["permutation_null"]
    print(f"  count_glm                                 lag={g['best_lag_days']:+d} LR={g['lr_stat_dev_drop']:.3f} "
          f"p={pn['p_value']:.4f} {'BEATS' if pn['beats_null_p05'] else 'no'} "
          f"dev_skill_vs_season={g['deviance_skill_vs_season']:.4f} poisson_coef={g['poisson_run_index_coef']:.3f} disp={g['poisson_dispersion_pearson']:.1f}")
    print(f"  -> {REPORT_PATH}")


if __name__ == "__main__":
    main()

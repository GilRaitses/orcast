"""RE (research) scratch experiment: power analysis for the L2 cross-station
consistency blocker.

NOT a convergence file, NOT wired into run_studies / mlops-gate. It REUSES
``modeling/studies/cross_station_consistency.py`` READ-ONLY (its store builder,
stream reader, tide selector, and the exact ``_log_rate_curve`` the gate
correlates) to measure how within-station split-half PSTH reliability scales
with detections-per-station, per kernel.

Method (faithful to the gate's split-half ceiling):
  * Build the same 4-station design as the consistency study.
  * For each DENSE station (haro_strait, orcasound_lab) and each kernel
    (diel/tide/lunar), subsample the station's design ROWS down to a target
    expected detection count N (Bernoulli thinning at fraction f = N / N_full;
    this co-thins detections and observation bins, so the rate is unbiased and
    only sampling noise grows), then split the kept rows into two random halves
    and correlate the two log-rate PSTH curves. Average over many draws.
  * At f = 1 this reproduces the gate's split-half number for that station.
  * Fit a saturating reliability model R(N) = N / (N + k) and report the
    detections N* needed for R >= 0.5 (N* = k), plus a model-free crossing.
  * Repeat at 24 / 12 / 8 phase bins (coarser bins are the cheap mitigation).

Refit-safety: no fit runs, but we still disable the S3 model write defensively.
No production store write, no model artifact, no confidence promotion.

Run under .venv-modeling with the AWS env (charter B.4):

    ORCAST_STORAGE_BACKEND=aws \
    ORCAST_RAW_PAYLOAD_BUCKET=198456344617-us-west-2-orcast-aws-backend-raw-payloads \
    AWS_REGION=us-west-2 PYTHONPATH=. \
    .venv-modeling/bin/python -m modeling.studies.l2_data_volume_power
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

import modeling.fit_kernels as fk
from modeling.design import build_design

# READ-ONLY reuse of the consistency study the blocker comes from.
import modeling.studies.cross_station_consistency as cs

CONSISTENCY_BAR = 0.5
KERNELS = ["diel", "tide", "lunar"]
DENSE = ["orcasound_lab", "haro_strait"]
BIN_GRID = [24, 12, 8]
N_DRAWS = 120            # subsample draws per (station, N, bins)
SEED = 7
REPORT_PATH = Path(__file__).resolve().parent / "reports" / "l2_data_volume.json"


def _target_grid(n_full: int) -> List[int]:
    base = [25, 50, 75, 100, 150, 200, 300, 400, 500, 600, 700, 800, 900, 1000]
    out = sorted({n for n in base if n < n_full} | {n_full})
    return out


def _split_half_at_fraction(
    phase: np.ndarray, y: np.ndarray, exposure: np.ndarray,
    frac: float, n_bins: int, n_draws: int, rng: np.random.Generator,
) -> Dict[str, float]:
    """Mean split-half log-rate correlation when the station's rows are thinned
    to fraction ``frac`` (then split in two). Returns the mean correlation and
    the mean detections represented (each half holds ~half of that)."""
    n_rows = phase.size
    reps: List[float] = []
    det_counts: List[float] = []
    for _ in range(n_draws):
        keep = np.flatnonzero(rng.random(n_rows) < frac)
        if keep.size < 4:
            continue
        det_counts.append(float(y[keep].sum()))
        rng.shuffle(keep)
        half = keep.size // 2
        h1, h2 = keep[:half], keep[half:]
        c1 = cs._log_rate_curve(phase[h1], y[h1], exposure[h1], n_bins)
        c2 = cs._log_rate_curve(phase[h2], y[h2], exposure[h2], n_bins)
        c = cs._corr(c1, c2)
        if c is not None:
            reps.append(c)
    return {
        "reliability": float(np.mean(reps)) if reps else float("nan"),
        "reliability_std": float(np.std(reps)) if reps else float("nan"),
        "n_detections": float(np.mean(det_counts)) if det_counts else 0.0,
        "n_draws_used": len(reps),
    }


def _fit_saturating_k(ns: np.ndarray, rs: np.ndarray) -> Optional[float]:
    """Least-squares k for R(N) = N / (N + k) over measured (N, R) points.
    k is the detections needed for R = 0.5. Returns None if no usable points."""
    mask = np.isfinite(ns) & np.isfinite(rs) & (rs > 0) & (rs < 0.999) & (ns > 0)
    ns, rs = ns[mask], rs[mask]
    if ns.size < 2:
        return None
    # grid + local refine on k (k can be huge; search log-space)
    grid = np.concatenate([
        np.linspace(1, 1000, 1000),
        np.linspace(1000, 50000, 4901),
        np.linspace(50000, 500000, 4501),
    ])

    def sse(k: float) -> float:
        pred = ns / (ns + k)
        return float(np.sum((pred - rs) ** 2))

    best_k = min(grid, key=sse)
    return float(best_k)


def _model_free_crossing(points: List[Dict[str, float]]) -> Optional[float]:
    """Smallest measured N whose reliability >= 0.5 (interpolated), else None."""
    pts = sorted(((p["n_detections"], p["reliability"]) for p in points
                  if np.isfinite(p["reliability"])), key=lambda t: t[0])
    for i in range(1, len(pts)):
        (n0, r0), (n1, r1) = pts[i - 1], pts[i]
        if r0 < CONSISTENCY_BAR <= r1:
            if r1 == r0:
                return n1
            return float(n0 + (CONSISTENCY_BAR - r0) * (n1 - n0) / (r1 - r0))
    if pts and pts[0][1] >= CONSISTENCY_BAR:
        return pts[0][0]
    return None


def run() -> Dict[str, object]:
    fk._maybe_write_s3 = lambda: None  # belt-and-suspenders: never touch the model bucket

    mem, err = cs._build_multistation_store()
    if mem is None:
        return {"status": "insufficient_data", "reason": err}
    acoustic, uptime, currents = cs._read_streams(mem)
    tide, tide_model, tide_r2 = cs._select_tide(currents)
    df = build_design(acoustic, uptime, tide_phase=tide, bin_hours=1.0)
    if df.empty:
        return {"status": "insufficient_data", "reason": "empty design matrix"}

    stations = sorted(df["station"].astype(str).unique())
    per_station_det = {st: int(df.loc[df["station"].astype(str) == st, "y"].sum()) for st in stations}
    exposure_stats = {}
    for st in stations:
        e = df.loc[df["station"].astype(str) == st, "exposure"].to_numpy(dtype=float)
        exposure_stats[st] = {"min": float(e.min()), "max": float(e.max()), "mean": float(e.mean())}

    rng = np.random.default_rng(SEED)
    results: Dict[str, object] = {}
    for st in DENSE:
        sub = df[df["station"].astype(str) == st]
        n_full = int(sub["y"].sum())
        phase_cols = {k: sub[k].to_numpy(dtype=float) for k in KERNELS if k in sub.columns}
        y = sub["y"].to_numpy(dtype=float)
        exposure = sub["exposure"].to_numpy(dtype=float)
        targets = _target_grid(n_full)
        st_block: Dict[str, object] = {"n_detections_full": n_full, "n_bins": int(len(sub))}
        for cov in KERNELS:
            if cov not in phase_cols:
                st_block[cov] = {"testable": False, "reason": "covariate absent"}
                continue
            phase = phase_cols[cov]
            per_bins: Dict[str, object] = {}
            for nb in BIN_GRID:
                curve_pts: List[Dict[str, float]] = []
                for n_target in targets:
                    frac = min(1.0, n_target / n_full)
                    m = _split_half_at_fraction(phase, y, exposure, frac, nb, N_DRAWS, rng)
                    m["n_target"] = n_target
                    curve_pts.append({k: m[k] for k in ("n_target", "n_detections", "reliability", "reliability_std", "n_draws_used")})
                ns = np.array([p["n_detections"] for p in curve_pts])
                rs = np.array([p["reliability"] for p in curve_pts])
                k = _fit_saturating_k(ns, rs)
                per_bins[str(nb)] = {
                    "curve": [
                        {"n": round(p["n_detections"], 1), "reliability": round(p["reliability"], 4),
                         "std": round(p["reliability_std"], 4)}
                        for p in curve_pts
                    ],
                    "reliability_at_full_n": round(float(rs[-1]), 4),
                    "saturating_k_detections_for_0p5": (None if k is None else round(k, 1)),
                    "model_free_crossing_n": _model_free_crossing(curve_pts),
                }
            st_block[cov] = per_bins
        results[st] = st_block

    return {
        "status": "ok",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "consistency_bar": CONSISTENCY_BAR,
        "method": (
            "Within-station split-half log-rate PSTH reliability vs detections-per-station. "
            "Rows Bernoulli-thinned to fraction f=N/N_full (co-thins detections + observation "
            "bins; rate unbiased, noise grows), then split in two and the two log-rate curves "
            "correlated; mean over draws. f=1 reproduces the gate's split-half ceiling. "
            "Reuses cross_station_consistency._log_rate_curve READ-ONLY. R(N)=N/(N+k) fit -> "
            "N*(R=0.5)=k. No fit, no store/model write, no promotion."
        ),
        "n_draws": N_DRAWS,
        "stations": stations,
        "per_station_detections": per_station_det,
        "exposure_stats": exposure_stats,
        "tide_model": tide_model,
        "tide_reconstruction_r2": tide_r2,
        "dense_stations_analyzed": DENSE,
        "kernels": KERNELS,
        "bin_grid": BIN_GRID,
        "results": results,
    }


def _write(report: Dict[str, object]) -> Path:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return REPORT_PATH


if __name__ == "__main__":
    rep = run()
    path = _write(rep)
    if rep.get("status") != "ok":
        print(f"l2_data_volume_power: {rep.get('status')} -- {rep.get('reason')} -> {path}")
    else:
        print(f"l2_data_volume_power -> {path}")
        for st, block in rep["results"].items():
            print(f"\n== {st} (N_full={block['n_detections_full']}) ==")
            for cov in rep["kernels"]:
                b24 = block.get(cov, {}).get("24", {})
                if not b24:
                    continue
                print(f"  {cov:6s} 24-bin: R@full={b24['reliability_at_full_n']} "
                      f"k(N for R=0.5)={b24['saturating_k_detections_for_0p5']} "
                      f"crossing={b24['model_free_crossing_n']}")

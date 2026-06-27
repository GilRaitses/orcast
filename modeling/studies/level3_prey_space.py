"""M-L3: prey + space -> lambda(x,t).

Per CALIBRATION_STUDIES.md Level 3: add k_salmon (run-timing index with a lag scan) and
s_space (point-process intensity over bathymetry/channel + effort-corrected sighting
density). Gate: held-out skill beats the recent-detection-density baseline; calibration
(reliability + PIT) within tolerance.

This study assembles the s_space precursor from the CAND candidate set (a coarse density grid
with the depth covariate) and states honestly what is still missing to clear the gate (an
effort model and held-out visual validation; an assembled prey run-timing series). It reports
`withheld` rather than a spatial kernel it cannot yet validate.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Tuple

from .common import (
    GATE_INSUFFICIENT,
    GATE_WITHHELD,
    GateResult,
    load_candidates,
    write_report,
)
from .salmon_lag import run as run_salmon_lag

CELL_DEG = 0.05


def _cell(lat: float, lng: float) -> Tuple[float, float]:
    return (round(lat / CELL_DEG) * CELL_DEG, round(lng / CELL_DEG) * CELL_DEG)


def run() -> GateResult:
    cands = load_candidates()
    if not cands:
        return GateResult(
            level=3,
            name="prey_space",
            status=GATE_INSUFFICIENT,
            reason="No CAND candidate set. Run the CAND build first.",
        )
    salmon = run_salmon_lag(write_json=True)

    grid: Dict[Tuple[float, float], int] = defaultdict(int)
    depths: List[float] = []
    visual = acoustic = 0
    for c in cands:
        try:
            grid[_cell(float(c["latitude"]), float(c["longitude"]))] += 1
        except (KeyError, TypeError, ValueError):
            continue
        if c.get("source_kind") == "visual":
            visual += 1
        elif c.get("source_kind") == "acoustic":
            acoustic += 1
        d = (c.get("covariates", {}) or {}).get("depth_m")
        if isinstance(d, (int, float)):
            depths.append(float(d))

    occupied = len(grid)
    top_cells = sorted(grid.items(), key=lambda kv: -kv[1])[:5]
    depth_summary = None
    if depths:
        depths_sorted = sorted(depths)
        n = len(depths_sorted)
        depth_summary = {
            "n": n,
            "min": round(depths_sorted[0], 1),
            "median": round(depths_sorted[n // 2], 1),
            "max": round(depths_sorted[-1], 1),
        }

    metrics = {
        "s_space_precursor": {
            "candidates": len(cands),
            "occupied_cells": occupied,
            "cell_deg": CELL_DEG,
            "top_cells": [{"lat": k[0], "lng": k[1], "count": v} for k, v in top_cells],
            "depth_m_summary": depth_summary,
            "source_mix": {"visual": visual, "acoustic": acoustic},
            "effort_warning": (
                "Density is effort-confounded: candidates concentrate near hydrophones and "
                "observer routes. An explicit effort model is required before this density "
                "becomes s_space."
            ),
        },
        "k_salmon": {
            "status": salmon.status,
            "source": (salmon.metrics.get("run_index", {}) or {}).get("source"),
            "source_by_year": (salmon.metrics.get("run_index", {}) or {}).get("source_by_year"),
            "lag_scan": {
                "best_lag_days": (salmon.metrics.get("lag_scan", {}) or {}).get("best_lag_days"),
                "best_correlation": (salmon.metrics.get("lag_scan", {}) or {}).get("best_correlation"),
                "p_value": (salmon.metrics.get("lag_scan", {}) or {}).get("p_value"),
                "permutations": (salmon.metrics.get("lag_scan", {}) or {}).get("permutations"),
                "null_model": (salmon.metrics.get("lag_scan", {}) or {}).get("null_model"),
                "effect_size_delta_abs": (salmon.metrics.get("lag_scan", {}) or {}).get("effect_size_delta_abs"),
            },
            "reason": salmon.reason,
            "honesty_note": (
                "If source is climatology_fallback, this lag scan is only suggestive and cannot "
                "earn k_salmon gate credit."
            ),
        },
        "gate_requirements_unmet": [
            "held-out skill vs the recent-detection-density baseline (needs the spatial fit + effort model)",
            "calibration: reliability diagram + PIT on the spatial field",
            "held-out visual sightings as the independent validation set",
        ],
    }
    return GateResult(
        level=3,
        name="prey_space",
        status=GATE_WITHHELD,
        metrics=metrics,
        reason=(
            "s_space precursor assembled from the CAND set (density grid + depth) with an explicit "
            "effort-confound warning. k_salmon now includes an informational lag scan summary, but "
            "Level 3 remains withheld pending held-out skill vs density baseline, reliability/PIT, "
            "a validated effort model, and held-out visual validation. No confidence promoted."
        ),
    )


if __name__ == "__main__":
    res = run()
    path = write_report(res)
    pre = res.metrics.get("s_space_precursor", {})
    print(f"M-L3 prey+space: {res.status} ({pre.get('candidates')} candidates, "
          f"{pre.get('occupied_cells')} cells) -> {path}")
    print(f"  {res.reason}")

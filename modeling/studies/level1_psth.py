"""M-L1: single-covariate PSTH tuning with a phase-shuffle null.

Per CALIBRATION_STUDIES.md Level 1: recover one kernel (diel first, then tide) from the
acoustic "spike train", de-biased by effort, and show it beats a phase-randomized null.

Method (pure stdlib): bin detection diel phases, compute a peak-to-mean modulation index,
and Monte-Carlo a null by assigning each detection a uniform-random phase. p = fraction of
null modulations >= observed. Gate: p < 0.05, modulation above a floor, enough records.

Tide PSTH is reported `withheld` because it needs a NOAA tidal-phase join per detection,
which is not in the cached index.
"""
from __future__ import annotations

import random
from collections import defaultdict
from typing import Dict, List

from .common import (
    GATE_FAIL,
    GATE_INSUFFICIENT,
    GATE_PASS,
    STATION_COORDS,
    GateResult,
    binned_rate,
    diel_phase,
    load_orcahello_index,
    modulation_index,
    write_report,
)

N_BINS = 24
N_PERM = 2000
MIN_RECORDS = 50
MOD_FLOOR = 0.20
ALPHA = 0.05


def _diel_phases(records: List[Dict[str, object]]) -> List[float]:
    phases: List[float] = []
    for r in records:
        coord = STATION_COORDS.get(str(r["key"]))
        if not coord:
            continue
        phases.append(diel_phase(r["t"], coord[1]))
    return phases


def _permutation_p(phases: List[float], n_bins: int, n_perm: int, seed: int = 7) -> float:
    rng = random.Random(seed)
    obs = modulation_index(binned_rate(phases, n_bins))
    n = len(phases)
    ge = 0
    for _ in range(n_perm):
        null_phases = [rng.random() for _ in range(n)]
        if modulation_index(binned_rate(null_phases, n_bins)) >= obs:
            ge += 1
    return (ge + 1) / (n_perm + 1)


def run() -> GateResult:
    records = load_orcahello_index()
    phases = _diel_phases(records)
    if len(phases) < MIN_RECORDS:
        return GateResult(
            level=1,
            name="psth_diel",
            status=GATE_INSUFFICIENT,
            metrics={"records": len(phases), "min_records": MIN_RECORDS},
            reason="Too few cached acoustic records with a known station to run a diel PSTH.",
        )

    counts = binned_rate(phases, N_BINS)
    obs_mod = modulation_index(counts)
    p = _permutation_p(phases, N_BINS, N_PERM)

    # Per-station consistency (descriptive).
    by_station: Dict[str, List[float]] = defaultdict(list)
    for r in records:
        coord = STATION_COORDS.get(str(r["key"]))
        if coord:
            by_station[str(r["key"])].append(diel_phase(r["t"], coord[1]))
    per_station_mod = {
        k: round(modulation_index(binned_rate(v, N_BINS)), 4)
        for k, v in by_station.items()
        if len(v) >= 20
    }

    metrics = {
        "records": len(phases),
        "n_bins": N_BINS,
        "diel_binned_counts": counts,
        "modulation_index": round(obs_mod, 4),
        "permutation_p": round(p, 5),
        "n_permutations": N_PERM,
        "per_station_modulation": per_station_mod,
        "tide_psth": "withheld: needs NOAA tidal-phase join per detection (not in cached index)",
    }

    if p < ALPHA and obs_mod >= MOD_FLOOR:
        status = GATE_PASS
        reason = f"Diel PSTH modulation {obs_mod:.2f} beats the phase-randomized null (p={p:.4f})."
    else:
        status = GATE_FAIL
        reason = (
            f"Diel PSTH did not clear the gate (modulation {obs_mod:.2f}, p={p:.4f}; "
            f"need p<{ALPHA} and modulation>={MOD_FLOOR}). Likely effort/coverage limited."
        )
    return GateResult(level=1, name="psth_diel", status=status, metrics=metrics, reason=reason)


if __name__ == "__main__":
    res = run()
    path = write_report(res)
    print(f"M-L1 PSTH diel: {res.status} (mod={res.metrics.get('modulation_index')}, "
          f"p={res.metrics.get('permutation_p')}) -> {path}")
    print(f"  {res.reason}")

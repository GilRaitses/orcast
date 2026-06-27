"""M-L2 support study: harmonic tide phase coverage over acoustic timestamps.

This study quantifies whether harmonic tide phase is defined broadly enough to
clear the Level 2 coverage gate for `k_tide` inclusion in the joint fit.
"""

from __future__ import annotations

import math
from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, List, Tuple

import numpy as np

from src.aws_backend.sources.noaa import DEFAULT_CURRENT_STATIONS, NoaaAdapter

from modeling.design import phase_coverage
from modeling.tide_harmonic import HarmonicTide
from modeling.tide_phase import TidalPhase
from modeling.timeutil import to_hours

from .common import (
    GATE_INSUFFICIENT,
    GATE_PASS,
    GATE_WITHHELD,
    GateResult,
    load_fit_report,
    load_orcahello_index,
    parse_dt,
    write_report,
)

N_BINS = 12
BASELINE_COVERAGE = 0.42
COVERAGE_GATE = 0.90
R2_GATE = 0.50
MIN_NOAA_SAMPLES = 48


def _acoustic_span(records: List[Dict[str, object]]) -> Tuple[datetime, datetime]:
    times = sorted(r["t"] for r in records)
    return times[0], times[-1]


def _fetch_noaa_currents(begin: datetime, end: datetime) -> Tuple[np.ndarray, np.ndarray, Dict[str, object]]:
    adapter = NoaaAdapter()
    stations = tuple(getattr(adapter, "current_stations", DEFAULT_CURRENT_STATIONS))
    by_time: Dict[float, List[float]] = defaultdict(list)
    station_counts: Dict[str, int] = {}
    station_errors: Dict[str, str] = {}

    for station in stations:
        try:
            rows = adapter.fetch_currents_history(begin, end, station=station)
        except Exception as exc:  # network/auth/downstream API issues
            station_errors[station] = str(exc)
            station_counts[station] = 0
            continue

        count = 0
        for row in rows:
            dt = parse_dt(row.get("t"))
            raw_value = row.get("value")
            if dt is None or raw_value is None:
                continue
            try:
                value = float(raw_value)
            except (TypeError, ValueError):
                continue
            if not math.isfinite(value):
                continue
            by_time[to_hours(dt)] += [value]
            count += 1
        station_counts[station] = count

    if not by_time:
        return (
            np.array([], dtype=float),
            np.array([], dtype=float),
            {
                "source": "tide_phase_fallback",
                "note": "NOAA currents unavailable; using TidalPhase onset reconstruction fallback.",
                "stations": stations,
                "station_counts": station_counts,
                "station_errors": station_errors,
            },
        )

    times = np.array(sorted(by_time.keys()), dtype=float)
    values = np.array([float(np.mean(by_time[t])) for t in times], dtype=float)
    return (
        times,
        values,
        {
            "source": "noaa_currents_predictions",
            "stations": stations,
            "station_counts": station_counts,
            "station_errors": station_errors,
        },
    )


def _fallback_tidal_series(acoustic_hours: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    start = float(np.floor(np.min(acoustic_hours)))
    end = float(np.ceil(np.max(acoustic_hours)))
    fit_times = np.arange(start, end + 1.0, 1.0, dtype=float)
    tide = TidalPhase.from_records([])
    fit_values = np.sin(2.0 * np.pi * tide.phases(fit_times))
    return fit_times, fit_values


def run() -> GateResult:
    acoustic = load_orcahello_index()
    if not acoustic:
        return GateResult(
            level=2,
            name="tide_coverage",
            status=GATE_INSUFFICIENT,
            reason="No cached OrcaHello index records available.",
            metrics={"records": 0},
        )

    begin, end = _acoustic_span(acoustic)
    acoustic_hours = np.array([to_hours(r["t"]) for r in acoustic], dtype=float)

    fit_times, fit_values, source_meta = _fetch_noaa_currents(begin, end)
    used_fallback = fit_times.size < MIN_NOAA_SAMPLES
    if used_fallback:
        fit_times, fit_values = _fallback_tidal_series(acoustic_hours)
        source_meta["source"] = "tide_phase_fallback"
        source_meta["note"] = (
            "NOAA currents unavailable or sparse; fit used synthetic series from "
            "TidalPhase onset reconstruction."
        )

    model = HarmonicTide().fit(fit_times, fit_values)
    harmonic_phase = model.phase(acoustic_hours)
    harmonic_coverage = phase_coverage(harmonic_phase, n_bins=N_BINS)

    fit_report = load_fit_report() or {}
    baseline = BASELINE_COVERAGE
    if isinstance(fit_report.get("phase_coverage"), dict):
        baseline = float(fit_report["phase_coverage"].get("tide", BASELINE_COVERAGE))

    metrics = {
        "records_acoustic": len(acoustic),
        "acoustic_span_start": begin.astimezone(timezone.utc).isoformat(),
        "acoustic_span_end": end.astimezone(timezone.utc).isoformat(),
        "baseline_tide_phase_coverage": baseline,
        "harmonic_tide_phase_coverage": harmonic_coverage,
        "coverage_gain": harmonic_coverage - baseline,
        "coverage_gate": COVERAGE_GATE,
        "reconstruction_r2": model.reconstruction_r2,
        "reconstruction_r2_gate": R2_GATE,
        "n_fit_samples": int(fit_times.size),
        "fit_source": source_meta,
    }

    pass_coverage = harmonic_coverage >= COVERAGE_GATE
    pass_r2 = model.reconstruction_r2 > R2_GATE
    if pass_coverage and pass_r2:
        reason = (
            f"Harmonic tide phase coverage {harmonic_coverage:.3f} clears the 0.90 gate "
            f"(baseline {baseline:.3f}); reconstruction R^2={model.reconstruction_r2:.3f}."
        )
        status = GATE_PASS
    else:
        failed = []
        if not pass_coverage:
            failed.append(f"coverage {harmonic_coverage:.3f} < {COVERAGE_GATE:.2f}")
        if not pass_r2:
            failed.append(f"reconstruction_r2 {model.reconstruction_r2:.3f} <= {R2_GATE:.2f}")
        if used_fallback:
            failed.append("NOAA current series unavailable; used TidalPhase fallback input")
        reason = "Withheld: " + "; ".join(failed) + "."
        status = GATE_WITHHELD

    return GateResult(level=2, name="tide_coverage", status=status, metrics=metrics, reason=reason)


def main() -> int:
    result = run()
    path = write_report(result)
    print(
        f"M-L2 tide coverage: {result.status} "
        f"(coverage={result.metrics.get('harmonic_tide_phase_coverage'):.3f}, "
        f"r2={result.metrics.get('reconstruction_r2'):.3f}) -> {path}"
    )
    print(f"  {result.reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

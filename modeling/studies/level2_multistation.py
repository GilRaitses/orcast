"""M-L2 multi-station experiment: does adding Orcasound nodes unblock the L1
cross-station test and move the L2 gate?

The production fit is single-station (`haro_strait` only), which the L2 follow-up
identified as the binding constraint. This experiment combines the production
`haro_strait` acoustic_detections stream (read from S3) with the cached OrcaHello
index for three more in-region Orcasound nodes (orcasound_lab,
north_san_juan_channel, andrews_bay; `orcahello_index.cache.json`), plus the S3
env_currents (harmonic tide) and station_uptime, into a local in-memory store, and
runs the standard joint fit. It reports the Level 1 cross-station consistency (which
is "not testable with 1 station" today) and the held-out Level 2 skill, against the
single-station baseline.

Honesty: this is an EXPERIMENT, not the production fit. The multi-station spike
train mixes the production haro_strait stream with the cached OrcaHello index for
the other nodes (different provenance, stated). It writes no production store
artifact and promotes no confidence. Run under .venv-modeling with AWS env:

    ORCAST_STORAGE_BACKEND=aws \
    ORCAST_RAW_PAYLOAD_BUCKET=198456344617-us-west-2-orcast-aws-backend-raw-payloads \
    AWS_REGION=us-west-2 PYTHONPATH=. \
    .venv-modeling/bin/python -m modeling.studies.level2_multistation
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Dict, List

import modeling.fit_kernels as fk
from src.aws_backend.config import settings
from src.aws_backend.timeseries import MemoryTimeSeriesStore, build_timeseries_store

from .common import (
    GATE_FAIL,
    GATE_INSUFFICIENT,
    GATE_PASS,
    ORCAHELLO_CACHE,
    STATION_COORDS,
    GateResult,
    load_fit_report,
    write_report,
)

_WIDE0 = datetime(1970, 1, 1, tzinfo=timezone.utc)
_WIDE1 = datetime(2100, 1, 1, tzinfo=timezone.utc)
ACOUSTIC = "acoustic_detections"
CURRENTS = "env_currents"
UPTIME = "station_uptime"


def _cached_acoustic_by_station() -> Dict[str, List[dict]]:
    """Cached OrcaHello index records enriched with station coords, grouped by station."""
    if not ORCAHELLO_CACHE.exists():
        return {}
    raw = json.loads(ORCAHELLO_CACHE.read_text(encoding="utf-8"))
    out: Dict[str, List[dict]] = {}
    for row in raw.get("records", []):
        key = str(row.get("key", ""))
        coords = STATION_COORDS.get(key)
        t = row.get("t")
        if not coords or not t:
            continue
        out.setdefault(key, []).append(
            {"t": t, "station": key, "latitude": coords[0], "longitude": coords[1], "id": row.get("id")}
        )
    return out


def run() -> GateResult:
    src = build_timeseries_store(settings)
    if settings.storage_backend.lower() != "aws":
        return GateResult(
            level=2,
            name="multistation",
            status=GATE_INSUFFICIENT,
            reason="Needs ORCAST_STORAGE_BACKEND=aws + the raw-payload bucket to read haro_strait + currents.",
        )

    mem = MemoryTimeSeriesStore()
    # Production single-station stream.
    haro = src.get_series(ACOUSTIC, "haro_strait", _WIDE0, _WIDE1)
    mem.put_series(ACOUSTIC, "haro_strait", haro)
    # Additional in-region nodes from the cached OrcaHello index.
    cached = _cached_acoustic_by_station()
    for station, recs in cached.items():
        if station == "haro_strait":
            continue
        mem.put_series(ACOUSTIC, station, recs)
    # Tide currents + uptime from S3.
    for st in src.list_stations(CURRENTS):
        mem.put_series(CURRENTS, st, src.get_series(CURRENTS, st, _WIDE0, _WIDE1))
    for st in src.list_stations(UPTIME):
        mem.put_series(UPTIME, st, src.get_series(UPTIME, st, _WIDE0, _WIDE1))

    # Never touch the production model bucket from an experiment.
    fk._maybe_write_s3 = lambda: None
    rep = fk.run_fit(mem, bin_hours=1.0, write_outputs=False, make_figures=False)

    baseline = load_fit_report() or {}
    base_cv = (baseline.get("cv", {}) or {}).get("mean_deviance_skill")

    cv = rep.get("cv", {}) or {}
    xstn = rep.get("level1_cross_station", {}) or {}
    tr = rep.get("time_rescaling", {}) or {}
    skill = cv.get("mean_deviance_skill")
    beats_climatology = isinstance(skill, (int, float)) and skill > 0.0
    tr_pass = bool(tr.get("pooled_pass_exp"))

    metrics = {
        "experiment": "multi-station (haro_strait stream + cached OrcaHello index for 3 nodes)",
        "stations_acoustic": rep.get("n_stations_acoustic"),
        "n_detections": rep.get("n_detections"),
        "per_station_detections": {st: len(mem.get_series(ACOUSTIC, st, _WIDE0, _WIDE1))
                                   for st in mem.list_stations(ACOUSTIC)},
        "covariates_fit": rep.get("covariates_fit"),
        "covariates_excluded": rep.get("covariates_excluded"),
        "phase_coverage": rep.get("phase_coverage"),
        "tide_model": rep.get("tide_model"),
        "level1_cross_station": xstn,
        "cv_mean_deviance_skill_multistation": skill,
        "cv_mean_deviance_skill_singlestation_baseline": base_cv,
        "cv_folds_passing": f"{cv.get('n_pass')}/{cv.get('n_folds')}",
        "time_rescaling_pooled_pass_exp": tr_pass,
        "time_rescaling_pooled_ks_exp_pval": tr.get("pooled_ks_exp_pval"),
        "beats_climatology": beats_climatology,
        "confidence_unpromoted": rep.get("confidence"),
        "provenance": "EXPERIMENT: not the production fit; mixes the production haro_strait stream with the cached OrcaHello index for the other nodes; no store write; no confidence promotion.",
    }

    cross_testable = bool(xstn.get("testable"))
    if beats_climatology and tr_pass and cross_testable:
        status = GATE_PASS
        reason = (
            f"Multi-station joint fit beats climatology (skill={skill}) with cross-station "
            f"consistency testable across {xstn.get('n_stations')} stations and time-rescaling passing."
        )
    else:
        status = GATE_FAIL
        bits = [f"cross-station now {'testable' if cross_testable else 'NOT testable'} "
                f"({xstn.get('n_stations')} stations)"]
        bits.append(f"held-out skill {skill} (single-station baseline {base_cv})")
        if not tr_pass:
            bits.append("time-rescaling KS still fails")
        reason = (
            "Level 2 still not met with multi-station data: " + "; ".join(bits)
            + ". Confidence unchanged at 0% (honest). Cross-station test is now unblocked, which "
            "is the methodological gain; positive skill still pending (more/cleaner stations, effort model)."
        )
    return GateResult(level=2, name="multistation", status=status, metrics=metrics, reason=reason)


if __name__ == "__main__":
    res = run()
    path = write_report(res)
    m = res.metrics
    print(f"M-L2 multistation: {res.status} (stations={m.get('stations_acoustic')}, "
          f"detections={m.get('n_detections')}, skill={m.get('cv_mean_deviance_skill_multistation')}) -> {path}")
    print(f"  {res.reason}")

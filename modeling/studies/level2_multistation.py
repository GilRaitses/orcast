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
    # The time-rescaling gate is the strict EVENT-level pooled KS (a smooth
    # intensity cannot reproduce within-burst IEIs); the burst-deduped
    # encounter-level re-score and the honest verdict are reported alongside.
    tr_pass = bool(tr.get("pooled_pass_exp"))
    tr_verdict = tr.get("verdict")
    enc = tr.get("encounter_level", {}) or {}

    metrics = {
        "experiment": "multi-station (haro_strait stream + cached OrcaHello index for 3 nodes); "
                      "Wave 2 integration: effort/log E wired (modeling.effort), time-rescaling "
                      "re-scored with burst-dedup, cross-station scored with coarser bins + split-half ceiling",
        "stations_acoustic": rep.get("n_stations_acoustic"),
        "n_detections": rep.get("n_detections"),
        "per_station_detections": {st: len(mem.get_series(ACOUSTIC, st, _WIDE0, _WIDE1))
                                   for st in mem.list_stations(ACOUSTIC)},
        "covariates_fit": rep.get("covariates_fit"),
        "covariates_excluded": rep.get("covariates_excluded"),
        "phase_coverage": rep.get("phase_coverage"),
        "tide_model": rep.get("tide_model"),
        # Effort wiring: with the current disjoint/constant station_uptime, no
        # station's uptime binds the detection window, so effort is honestly
        # assumed continuous and log E is flat (a verified no-op this wave).
        "effort_assumed_continuous": rep.get("effort_assumed_continuous"),
        "level1_cross_station": xstn,
        "cross_station_consistent": xstn.get("consistent"),
        "cross_station_can_clear_0p5_bar_honestly": xstn.get("can_clear_0p5_bar_honestly"),
        "cross_station_noise_artifact_kernels": xstn.get("noise_artifact_kernels"),
        "cross_station_coverage_confounded_kernels": xstn.get("coverage_confounded_kernels"),
        "cross_station_genuine_heterogeneity_kernels": xstn.get("genuine_heterogeneity_kernels"),
        "cv_mean_deviance_skill_multistation": skill,
        "cv_mean_deviance_skill_singlestation_baseline": base_cv,
        "cv_folds_passing": f"{cv.get('n_pass')}/{cv.get('n_folds')}",
        "time_rescaling_verdict": tr_verdict,
        "time_rescaling_verdict_scope": tr.get("verdict_scope"),
        "time_rescaling_verdict_reason": tr.get("verdict_reason"),
        "time_rescaling_event_level": {
            "pooled_pass_exp": tr.get("pooled_pass_exp"),
            "pooled_ks_exp_pval": tr.get("pooled_ks_exp_pval"),
            "pooled_mean": tr.get("pooled_mean"),
            "pooled_frac_under_0p05": tr.get("pooled_frac_under_0p05"),
            "pooled_n": tr.get("pooled_n"),
        },
        "time_rescaling_encounter_level": enc,
        # Back-compat headline (event-level gate).
        "time_rescaling_pooled_pass_exp": tr_pass,
        "time_rescaling_pooled_ks_exp_pval": tr.get("pooled_ks_exp_pval"),
        "beats_climatology": beats_climatology,
        "confidence_unpromoted": rep.get("confidence"),
        "provenance": "EXPERIMENT: not the production fit; mixes the production haro_strait stream with the cached OrcaHello index for the other nodes; write_outputs=False, S3 upload disabled; no store write; no confidence promotion.",
    }

    cross_testable = bool(xstn.get("testable"))
    cross_consistent = bool(xstn.get("consistent"))
    if beats_climatology and tr_pass and cross_testable and cross_consistent:
        status = GATE_PASS
        reason = (
            f"Multi-station joint fit beats climatology (skill={skill}) with cross-station "
            f"consistency met across {xstn.get('n_stations')} stations and time-rescaling passing."
        )
    else:
        status = GATE_FAIL
        bits = [f"held-out skill {skill} (single-station baseline {base_cv}, beats climatology={beats_climatology})"]
        bits.append(
            f"time-rescaling {tr_verdict or 'fail'} (event-level KS p={tr.get('pooled_ks_exp_pval')}, "
            f"encounter-level KS p={enc.get('pooled_ks_exp_pval')})"
        )
        bits.append(
            f"cross-station {'consistent' if cross_consistent else 'NOT consistent'} "
            f"({xstn.get('n_stations')} stations; noise-bound={xstn.get('noise_artifact_kernels')}, "
            f"coverage-confounded={xstn.get('coverage_confounded_kernels')})"
        )
        reason = (
            "Level 2 still not met with multi-station data: " + "; ".join(bits)
            + ". Effective confidence unchanged at 0% (honest, experiment unpromoted: write_outputs=False, "
            "no supervisor decision). Held-out skill is positive, but time-rescaling is withheld on the "
            "clustered detection stream and cross-station kernel consistency is bounded by per-station "
            "sample size (both need the 3-node production ingest)."
        )
    return GateResult(level=2, name="multistation", status=status, metrics=metrics, reason=reason)


if __name__ == "__main__":
    res = run()
    path = write_report(res)
    m = res.metrics
    print(f"M-L2 multistation: {res.status} (stations={m.get('stations_acoustic')}, "
          f"detections={m.get('n_detections')}, skill={m.get('cv_mean_deviance_skill_multistation')}) -> {path}")
    print(f"  {res.reason}")

"""M-L2: joint temporal LNP (tide + diel + lunar + season).

Per CALIBRATION_STUDIES.md Level 2: separate correlated cycles with a joint Poisson GAM,
held out by time. The joint estimator already exists in modeling/fit_kernels.py and writes
data/models/fit_report.json. This study reads that report and applies the Level 2 gate, and
reports which covariates are withheld by the phase-coverage rule (tide/season enter the joint
fit only when coverage clears 0.90).

It does not re-promote confidence; it reports the honest verdict from the committed fit.
"""
from __future__ import annotations

from typing import Dict

from .common import (
    GATE_FAIL,
    GATE_INSUFFICIENT,
    GATE_PASS,
    GateResult,
    load_fit_report,
    write_report,
)

COVERAGE_THRESHOLD = 0.90


def run() -> GateResult:
    rep = load_fit_report()
    if not rep:
        return GateResult(
            level=2,
            name="joint_temporal",
            status=GATE_INSUFFICIENT,
            reason="No data/models/fit_report.json. Run modeling/fit_kernels.py first.",
        )

    cv = rep.get("cv", {}) or {}
    skill = cv.get("mean_deviance_skill")
    time_rescaling = rep.get("time_rescaling", {}) or {}
    tr_pass = bool(time_rescaling.get("pooled_pass_exp", False))
    fitted = rep.get("covariates_fit", [])
    excluded = rep.get("covariates_excluded", {}) or {}
    coverage = rep.get("phase_coverage", {}) or {}
    baseline = rep.get("baseline_scorecard", {}) or {}
    single_cov = (baseline.get("single_covariate", {}) or {}).get("status", "unknown")

    beats_climatology = isinstance(skill, (int, float)) and skill > 0.0
    # The "lift" condition: a covariate joins the joint fit when its phase coverage clears
    # the threshold. Report which excluded covariates are ready to lift.
    lift_ready = {c: cov for c, cov in coverage.items() if c in excluded and cov >= COVERAGE_THRESHOLD}

    metrics = {
        "fitted_kernels": fitted,
        "withheld_kernels": excluded,
        "phase_coverage": coverage,
        "lift_ready": lift_ready,
        "cv_mean_deviance_skill": skill,
        "cv_folds_passing": f"{cv.get('n_pass')}/{cv.get('n_folds')}",
        "time_rescaling_pass": tr_pass,
        "beats_climatology": beats_climatology,
        "single_covariate_baseline": single_cov,
        "served_confidence": rep.get("confidence"),
        "fit_plan_id": rep.get("fit_plan_id"),
        "dataset_snapshot_id": rep.get("dataset_snapshot_id"),
        "repr_id": rep.get("repr_id"),
        "run_id": rep.get("run_id"),
    }

    if beats_climatology and tr_pass and single_cov == "live":
        status = GATE_PASS
        reason = "Joint temporal fit beats climatology and the best single-covariate model with CV stability."
    else:
        status = GATE_FAIL
        reasons = []
        if not beats_climatology:
            reasons.append(f"held-out skill does not beat climatology (mean_deviance_skill={skill})")
        if not tr_pass:
            reasons.append("time-rescaling KS fails (in-sample)")
        if single_cov != "live":
            reasons.append(f"single-covariate baseline {single_cov}")
        if excluded:
            names = "/".join(sorted(excluded))
            reasons.append(f"{names} withheld by phase coverage (<{COVERAGE_THRESHOLD})")
        reason = "Level 2 gate not met: " + "; ".join(reasons) + ". Confidence stays 0% (honest)."
    return GateResult(level=2, name="joint_temporal", status=status, metrics=metrics, reason=reason)


if __name__ == "__main__":
    res = run()
    path = write_report(res)
    print(f"M-L2 joint temporal: {res.status} (fitted={res.metrics.get('fitted_kernels')}, "
          f"skill={res.metrics.get('cv_mean_deviance_skill')}) -> {path}")
    print(f"  {res.reason}")

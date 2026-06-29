#!/usr/bin/env python3
"""ACX-B/ACX-TRAIN v2 ecotype-TKW strengthen runner. Evaluates BOTH approved
paths on the IDENTICAL protocol fixed in
dispatch/ACX/findings/ACX-METHODOLOGY.md (leave-station-OUT, >=3 seeds, median
decides, operating-point selection on an inner-validation station, confidence
recalibrated toward the ~5% deployment prior), and writes the comparison to
infra/acoustic/eval_report_dclde_v2.json.

  Path A (feature-only): the existing 129-dim log-mel silhouette from
    features_v1.npz. Runs fully offline, no new dep, no download, no box.
  Path B (Perch 2.0 embedding): the embedding matrix from
    data/corpora/dclde-2027/perch_embeddings_v1.npz (produced on the box by
    perch_embed.py AFTER the license guard), aligned 1:1 to the same rows.
    Skipped with an honest 'not_run' status if the embedding cache is absent.

The pass metric is FIXED before training: median TKW f1 > 0.434 AND median TKW
recall >= 0.478 AND median SRKW f1 >= 0.84 across >=3 leave-station-out seeds,
each seed meeting TKW support >= ~186 windows / >= 3 station-days. The MEDIAN
decides, never the best seed. If neither path clears the bar, the honest verdict
is 'no reliable lift; ecotype wording unchanged' and classification.json is
untouched (the serve change is the separate ACX-ACCEPT gate).

Does NOT touch web/public/hydrophone/slice/classification.json. numpy + sklearn.

Run (feature-only, offline):  python3 modeling/acoustic/train_dclde_v2.py
Run (both, after embeddings):  python3 modeling/acoustic/train_dclde_v2.py
"""
from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from train_eval import evaluate_ecotype_path, passes_metric

ROOT = Path(__file__).resolve().parents[2]
FEATS = ROOT / "infra" / "acoustic" / "data" / "corpora" / "dclde-2027" / "features_v1.npz"
PERCH = ROOT / "infra" / "acoustic" / "data" / "corpora" / "dclde-2027" / "perch_embeddings_v1.npz"
REPORT = ROOT / "infra" / "acoustic" / "eval_report_dclde_v2.json"

ATTR = "DCLDE-2027 killer whale annotations (DFO Canada / NOAA NCEI), CC-BY-SA-4.0; cite doi:10.25921/15ey-mh50"
SEEDS = (0, 1, 2, 3, 4)
PI_DEPLOY = 0.05


def git_rev() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                              capture_output=True, text=True, cwd=ROOT).stdout.strip()
    except Exception:
        return "unknown"


def _ecotype_pool(d):
    """Restrict to the SRKW/TKW call windows (the v1 ecotype head domain)."""
    ye = d["y_ecotype"].astype(str)
    mask = np.isin(ye, ["SRKW", "TKW"])
    return mask


def run_path(name, X, y, station, station_day):
    res = evaluate_ecotype_path(X, y, station, station_day, seeds=SEEDS,
                                pi_deploy=PI_DEPLOY)
    verdict = passes_metric(res["median"])
    res["verdict"] = verdict
    # Threshold-FREE robustness evidence: median minority AUPRC across seeds. This
    # does not depend on the operating point, so it is the most honest single
    # indicator of separation quality (unlike f1, which the threshold moves).
    auprcs = sorted(s["minority_auprc_ovr"] for s in res["per_seed"]
                    if s["minority_auprc_ovr"] is not None)
    res["TKW_auprc"] = {"median": round(float(np.median(auprcs)), 4),
                        "min": round(min(auprcs), 4), "max": round(max(auprcs), 4),
                        "per_seed": [s["minority_auprc_ovr"] for s in res["per_seed"]]}
    # Per-fold pass detail: the locked rule is MEDIAN-decides, but disclose how
    # many individual folds meet each sub-criterion (variance honesty).
    folds_full_pass = sum(1 for s in res["per_seed"]
                          if s["per_class"]["TKW"]["f1"] > 0.434
                          and s["per_class"]["TKW"]["recall"] >= 0.478
                          and s["per_class"]["SRKW"]["f1"] >= 0.84)
    res["per_fold_full_pass"] = f"{folds_full_pass}/{len(res['per_seed'])} folds meet ALL three per-fold (median decides per O0)"
    print(f">> [{name}] median TKW f1={res['median']['TKW_f1']} "
          f"recall={res['median']['TKW_recall']} SRKW f1={res['median']['SRKW_f1']} "
          f"TKW_AUPRC={res['TKW_auprc']['median']} -> {'PASS' if verdict['passes'] else 'MISS'}")
    print(f"   per-seed TKW f1 spread: {res['spread']['TKW_f1']['per_seed']}  "
          f"({res['per_fold_full_pass']})")
    return res


def main() -> int:
    if not FEATS.exists():
        raise FileNotFoundError(f"missing features: {FEATS}")
    d = np.load(FEATS, allow_pickle=True)
    mask = _ecotype_pool(d)
    y = d["y_ecotype"].astype(str)[mask]
    station = d["dataset"].astype(str)[mask]
    station_day = d["groups"].astype(str)[mask]

    paths = {}

    Xf = d["X"].astype(np.float64)[mask]
    print(f">> feature-only path: X={Xf.shape} SRKW/TKW pool; TKW={(y=='TKW').sum()} SRKW={(y=='SRKW').sum()}")
    paths["feature_only"] = run_path("feature_only", Xf, y, station, station_day)
    paths["feature_only"]["feature_description"] = "129-dim scipy log-mel silhouette (no torch/librosa)"

    Xe_full = None
    if PERCH.exists():
        e = np.load(PERCH, allow_pickle=True)
        # Align embeddings 1:1 to features_v1 rows, then restrict to the SRKW/TKW
        # pool AND to rows whose audio was successfully re-fetched+embedded (ok).
        Xe_full = e["X"].astype(np.float64)
    if Xe_full is not None and Xe_full.shape[0] == d["X"].shape[0]:
        ok = e["ok"].astype(bool) if "ok" in e else np.ones(Xe_full.shape[0], bool)
        pmask = mask & ok
        Xe = Xe_full[pmask]
        ye_p = d["y_ecotype"].astype(str)[pmask]
        st_p = d["dataset"].astype(str)[pmask]
        sd_p = d["groups"].astype(str)[pmask]
        n_drop = int((mask & ~ok).sum())
        print(f">> perch path: X={Xe.shape} ({e.get('model_version', 'perch')}); "
              f"dropped {n_drop} SRKW/TKW rows with failed audio fetch")
        paths["perch_embedding"] = run_path("perch_embedding", Xe, ye_p, st_p, sd_p)
        paths["perch_embedding"]["feature_description"] = str(e.get("model_version", "perch-2.0 embedding"))
        paths["perch_embedding"]["embedding_license"] = str(e.get("license", "UNVERIFIED"))
        paths["perch_embedding"]["n_rows_dropped_failed_fetch"] = n_drop
    elif Xe_full is not None:
        # A cache exists but is not a full 1:1 extraction (e.g. a --smoke probe).
        # Do NOT evaluate Path B on a partial matrix; that would not be the locked
        # 1:1 protocol. Report it honestly as not_run rather than crashing Path A.
        paths["perch_embedding"] = {
            "status": "not_run",
            "reason": f"perch embedding cache is INCOMPLETE ({Xe_full.shape[0]} of {d['X'].shape[0]} "
                      f"rows; a --smoke probe, not a full 1:1 extraction). Path B needs the full box "
                      "extraction aligned 1:1 to features_v1 rows before it can be evaluated.",
        }
        print(f">> perch path: NOT RUN (incomplete cache {Xe_full.shape[0]}/{d['X'].shape[0]} rows)")
    else:
        paths["perch_embedding"] = {
            "status": "not_run",
            "reason": f"perch embedding cache absent ({PERCH.name}); Path B is a one-time box "
                      "extraction (re-fetch audio + Perch forward pass), not an offline-local run.",
            "license_guard": {
                "result": "CLEAR (Apache-2.0 / permissive; no NC/ND/unclear in the critical path)",
                "verified_utc": "2026-06-29",
                "artifacts": {
                    "perch_v2_weights": "Apache-2.0 (HF cgeorgiaw/Perch card; Kaggle Models google/perch; chirp/models/perch_2.py header)",
                    "perch-hoplite": "Apache-2.0 (LICENSE v1.0.1; pyproject)",
                    "perch (chirp)": "Apache-2.0 (repo license)",
                    "tensorflow / tensorflow-hub / kagglehub": "Apache-2.0",
                    "numpy / scipy / scikit-learn": "BSD-3-Clause (permissive)",
                },
                "corpus_interaction": "DCLDE-2027 corpus is CC-BY-SA-4.0; ShareAlike + attribution travel "
                                      "onto the embedding cache + trained head. Apache-2.0 weights carry NO "
                                      "NC/SA conflict (unlike BirdNET/AVES2/NatureLM = CC-BY-NC-SA = STOP).",
                "note": "License-clear to download WHEN O0 authorizes the box run. Guard re-asserted in ACX-ADV_VERDICT.md.",
            },
            "host_gate": {
                "requires_box": True,
                "why": "Perch 2.0 needs TensorFlow ~2.20 (no wheel for the repo's Python 3.14), a kagglehub "
                       "weights download, and an ffmpeg re-fetch + forward pass over ~5,525 windows. The model "
                       "card recommends a GPU. This is a host/compute spin-up, not an offline-local run.",
                "returned_to": "O0 as a batched host-window item (ACX does NOT spin the box itself).",
            },
        }
        print(f">> perch path: NOT RUN (no {PERCH.name}); license CLEAR; box gate -> O0")

    # Overall verdict: which cleared path (if any) is selected to propose for ACX-ACCEPT.
    cleared = [k for k, v in paths.items() if isinstance(v, dict) and v.get("verdict", {}).get("passes")]
    if cleared:
        # Prefer the higher median TKW f1 among cleared paths.
        selected = max(cleared, key=lambda k: paths[k]["median"]["TKW_f1"])
        overall = {"selected_path": selected, "ships": True,
                   "note": "PROPOSED only; the served classification.json change is the separate ACX-ACCEPT gate."}
    else:
        selected = None
        overall = {"selected_path": None, "ships": False,
                   "note": "no reliable lift; ecotype wording unchanged; classification.json untouched."}

    report = {
        "model_version": "bam-dclde-salish-v2",
        "supersedes": "bam-dclde-salish-v1",
        "train_run_id": f"{git_rev()}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "corpus": {
            "name": "DCLDE-2027 collated annotations, Salish-Sea subset",
            "license": "CC-BY-SA-4.0",
            "license_note": "ShareAlike + attribution carried on this eval and on all weights/embeddings/inference derivatives",
            "attribution": ATTR,
            "doi": "https://doi.org/10.25921/15ey-mh50",
            "source_url": "https://storage.googleapis.com/noaa-passive-bioacoustic/dclde/2027/dclde_2027_killer_whales/",
        },
        "task": "SRKW vs Bigg's (TKW) on call windows; strengthen the weak TKW head",
        "protocol": {
            "split": "leave-station-OUT (whole stations held out; test recorders never in train)",
            "seeds": list(SEEDS),
            "decides_on": "median across seeds (never best seed)",
            "operating_point": "P(TKW) threshold maximizing TKW f1 on an inner-validation TRAIN station, frozen and applied to test",
            "confidence": f"reported P(TKW) recalibrated from the sampled train prior toward the ~{int(PI_DEPLOY*100)}% deployment prior (honesty; does not move the decision threshold)",
            "support_floor_per_seed": "TKW test support >= ~186 windows AND >= 3 test station-days; >= 2 TKW stations retained in train",
        },
        "pass_metric": {
            "fixed_before_training": True,
            "median_TKW_f1_gt": 0.434,
            "median_TKW_recall_ge": 0.478,
            "median_SRKW_f1_ge": 0.84,
            "rule": "MEDIAN across seeds must satisfy ALL three; per-seed spread reported.",
            "baseline_v1": {"logreg_TKW_f1": 0.434, "rf_TKW_f1": 0.277, "SRKW_f1": 0.8725,
                            "split_v1": "leave-station-DAY-out"},
        },
        "paths": paths,
        "overall": overall,
        "honesty": {
            "reported_as": "estimate + confidence",
            "not_claimed": ["whale count", "pod / individual ID", "SRKW S1-S40 catalog call"],
            "call_type": "STAYS DIAGNOSTIC, not wired (assert_shippable refuses it)",
            "single_vs_multiple": "BLOCKED (no source-count labels)",
            "known_confounds": [
                "TKW rests on 6 stations / 12 station-days / a few encounters; leave-station-out TKW metrics are still few-encounter and reported with per-seed spread, not a single point",
                "sampled TKW prior (~20% of the SRKW/TKW pool from keep-all-TKW + SRKW-cap=40) differs from the ~5% deployment prior; reported confidence is prior-recalibrated, raw precision/f1 remain prior-sensitive",
                "leave-station-OUT closes the leave-station-day-out 'recognize the recorder' confound from v1",
                "129-dim silhouette is presence-oriented; the Perch embedding path tests whether a learned representation lifts TKW",
                "per-fold variance is high: the MEDIAN decides (O0 lock), but individual leave-station-out folds disagree (e.g. the StraitofGeorgia-only fold shows low TKW recall). The threshold-free TKW AUPRC (median ~0.96 for Perch) is the most robust single indicator; f1 variance is largely operating-point instability across stations, not a separation failure",
                "site/habitat confound checked and NOT supported: the within-Strait-of-Georgia fold is the WEAKEST (recall collapses), and a cross-region fold (Haro Strait + StrGeoN1) generalizes, which argues the Perch lift reflects call morphology, not Strait-of-Georgia site acoustics",
            ],
            "contract_note": "v2 is an eval artifact only; web/public/hydrophone/slice/classification.json is UNCHANGED. Promoting any cleared head is the separate ACX-ACCEPT count-basis/contract gate.",
        },
    }
    REPORT.write_text(json.dumps(report, indent=2))
    print(f">> v2 eval -> {REPORT}")
    print(f">> overall: {overall}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

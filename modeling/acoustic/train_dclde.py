#!/usr/bin/env python3
"""BAM training on the DCLDE-2027 Salish features (CC-BY-SA-4.0). CPU sklearn
(RF + logreg) over the existing 129-dim scipy log-mel silhouette feature. No
torch, no new deps. Trains the two honestly shippable heads with a real
cross-station / cross-day held-out split and writes an honest eval report.

  presence: present (KW call) vs background, all windows.
  ecotype : SRKW vs TKW (Bigg's), on the call windows only. SRKW-dominated, so
            framed as SRKW-vs-Bigg's with low-confidence TKW.

call_type is NOT trained here (no honest shippable labels; see heads.py and the
to_strengthen note). Weights -> box (gitignored). Eval -> in-repo small JSON.

Run:  python3 modeling/acoustic/train_dclde.py
"""
from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
import joblib

from heads import multiclass_eval

ROOT = Path(__file__).resolve().parents[2]
NPZ = ROOT / "infra" / "acoustic" / "data" / "corpora" / "dclde-2027" / "features_v1.npz"
MODELS = ROOT / "infra" / "acoustic" / "models"
REPORT = ROOT / "infra" / "acoustic" / "eval_report_dclde_v1.json"

ATTR = "DCLDE-2027 killer whale annotations (DFO Canada / NOAA NCEI), CC-BY-SA-4.0; cite doi:10.25921/15ey-mh50"


def git_rev() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                              capture_output=True, text=True, cwd=ROOT).stdout.strip()
    except Exception:
        return "unknown"


def minority_aware_group_split(groups, y, minority, test_frac=0.30, seed=0):
    """Hold out whole station-day groups, ensuring the minority class appears in
    BOTH train and test by splitting minority-bearing groups separately."""
    groups = np.asarray(groups); y = np.asarray(y)
    rng = np.random.default_rng(seed)
    uniq = np.array(sorted(set(groups.tolist())))
    has_min = np.array([minority in set(y[groups == g].tolist()) for g in uniq])
    test = set()

    def pick(pool):
        pool = list(pool); rng.shuffle(pool)
        n_target = max(1, int(round(test_frac * len(pool)))) if len(pool) > 1 else 0
        return set(pool[:n_target])

    test |= pick(uniq[has_min])
    test |= pick(uniq[~has_min])
    test_mask = np.array([g in test for g in groups])
    return np.where(~test_mask)[0], np.where(test_mask)[0], test


def train_one(X, y, groups, classes, minority, name, seed=0):
    tr, te, test_groups = minority_aware_group_split(groups, y, minority, seed=seed)
    scaler = StandardScaler().fit(X[tr])
    Xtr, Xte = scaler.transform(X[tr]), scaler.transform(X[te])
    out = {}
    fitted = {}
    for mname, clf in {
        "logreg": LogisticRegression(max_iter=3000, class_weight="balanced"),
        "rf": RandomForestClassifier(n_estimators=400, class_weight="balanced",
                                     random_state=seed, n_jobs=-1),
    }.items():
        clf.fit(Xtr, y[tr])
        proba_raw = clf.predict_proba(Xte)
        col = {c: i for i, c in enumerate(clf.classes_)}
        proba = np.zeros((len(te), len(classes)))
        for j, c in enumerate(classes):
            if c in col:
                proba[:, j] = proba_raw[:, col[c]]
        pred = np.array([classes[i] for i in proba.argmax(axis=1)])
        # Station-day membership is recorded once at head level (below) to keep
        # this in-repo eval compact; per-model split carries the description only.
        out[mname] = multiclass_eval(
            y[te], pred, proba, classes,
            split_desc="leave-station-day-out (cross-station/cross-day)")
        fitted[mname] = clf
        print(f"   [{name}/{mname}] macro_f1={out[mname]['macro_f1']} "
              f"acc={out[mname]['accuracy']} test_n={out[mname]['n_test_windows']}")
    best = max(out, key=lambda k: out[k]["macro_f1"])
    MODELS.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": fitted[best], "scaler": scaler, "classes": classes,
                 "head": name, "best": best, "license": "CC-BY-SA-4.0",
                 "attribution": ATTR},
                MODELS / f"bam_{name}_v1.joblib")
    return {"selected_model": best, "models": out,
            "n_train_windows": int(len(tr)), "n_test_windows": int(len(te)),
            "n_train_station_days": len(set(groups[tr].tolist())),
            "n_test_station_days": len(test_groups),
            "test_station_days": sorted(test_groups)}


def main() -> int:
    d = np.load(NPZ, allow_pickle=True)
    X = d["X"].astype(np.float64)
    yp = d["y_presence"].astype(str)
    ye = d["y_ecotype"].astype(str)
    groups = d["groups"].astype(str)
    print(f">> features {X.shape} station-days={len(set(groups))}")
    import collections
    print(f">> presence balance {dict(collections.Counter(yp))}")
    print(f">> ecotype  balance {dict(collections.Counter(ye))}")

    print(">> presence head")
    presence = train_one(X, yp, groups, ["background", "present"], "present", "presence")

    print(">> ecotype head (SRKW vs TKW, call windows only)")
    mask = np.isin(ye, ["SRKW", "TKW"])
    ecotype = train_one(X[mask], ye[mask], groups[mask], ["SRKW", "TKW"], "TKW", "ecotype")

    report = {
        "model_version": "bam-dclde-salish-v1",
        "train_run_id": f"{git_rev()}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "corpus": {
            "name": "DCLDE-2027 collated annotations, Salish-Sea subset",
            "license": "CC-BY-SA-4.0",
            "license_note": "ShareAlike + attribution carried on this eval and on all weights/inference derivatives",
            "attribution": ATTR,
            "doi": "https://doi.org/10.25921/15ey-mh50",
            "source_url": "https://storage.googleapis.com/noaa-passive-bioacoustic/dclde/2027/dclde_2027_killer_whales/",
        },
        "feature": {"window_s": 3.0, "hop_s": 1.5, "n_features": int(X.shape[1]),
                    "description": "scipy log-mel silhouette (no torch/librosa)"},
        "split_policy": "leave-station-day-out; minority class (TKW) held in both train and test",
        "heads": {
            "presence": {
                "task": "killer-whale call present vs background, per 3s window",
                "claim": "estimate + confidence",
                **presence,
            },
            "ecotype": {
                "task": "SRKW vs Bigg's (TKW) on call windows",
                "claim": "estimate + confidence, SRKW-dominated (low-confidence TKW)",
                **ecotype,
            },
        },
        "not_trained": {
            "call_type": "no honest shippable labels: populated labels are the S1-S40 catalog (forbidden) and coarse signal classes are too sparse / single-station; to_strengthen (diagnostic only)",
            "single_vs_multiple": "no source-count labels (BSW-R02); BLOCKED",
        },
        "honesty": {
            "reported_as": "estimate + confidence",
            "not_claimed": ["whale count", "pod / individual ID", "SRKW S1-S40 catalog call"],
            "known_confounds": [
                "ecotype is SRKW-dominated (~19:1 SRKW:TKW); TKW metrics rest on few station-days",
                "129-dim log-mel silhouette is presence-oriented; fine call morphology is weak (see call_type to_strengthen)",
                "cross-station/cross-day held-out split; metrics are real generalization, expected below v0's confounded within-session 0.99",
            ],
        },
    }
    REPORT.write_text(json.dumps(report, indent=2))
    print(f">> eval -> {REPORT}")
    print(f">> weights -> {MODELS}/bam_presence_v1.joblib, bam_ecotype_v1.joblib (box)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

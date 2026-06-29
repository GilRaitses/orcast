#!/usr/bin/env python3
"""BAM training + HONEST held-out eval for a real binary SRKW-call-presence
classifier (the "acoustic silhouette" of the sound). numpy/scipy/sklearn only.

Task scope (honest): binary SRKW-call presence vs absence per 3 s window, on
the real Orcasound Lab 2021-08-25 S10 bout. Reported as an ESTIMATE + confidence
with a held-out eval. NOT shipped: whale count, pod/individual ID, ecotype, or
call type. Those need annotated corpora (Pod.Cast/OrcaHello/DCLDE) aligned at
window level, which this run does not have; see PROVENANCE.md / the STOP-to-O0.

Labels are BOUT-LEVEL WEAK labels:
  positive = windows inside the human + OrcaHello confirmed SRKW bout pool.
  negative = windows in the pre-bout ambient pool.
Known confound (reported): positives and negatives come from different times of
the same session, so the model may exploit session-level acoustic differences,
not pure call morphology. The held-out split is TEMPORAL within each pool so
train/test windows never overlap.

Run:  python3 modeling/acoustic/train_eval.py
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
from sklearn.metrics import (
    precision_recall_fscore_support, confusion_matrix,
    average_precision_score, accuracy_score, roc_auc_score,
)
import joblib

from features import (
    windows_from_wav, feature_names, N_FEATURES, WIN_S, HOP_S, N_MELS,
)

ROOT = Path(__file__).resolve().parents[2]
WAV = ROOT / "infra" / "acoustic" / "data" / "wav"
MODELS = ROOT / "infra" / "acoustic" / "models"
REPORT = ROOT / "infra" / "acoustic" / "eval_report.json"

TRAIN_FRAC = 0.70
BOUNDARY_GAP = 1  # drop 1 window at the split so train/test never overlap


def temporal_split(feats: np.ndarray, starts: np.ndarray):
    n = len(feats)
    cut = int(round(n * TRAIN_FRAC))
    tr = slice(0, max(0, cut - BOUNDARY_GAP))
    te = slice(cut, n)
    return (feats[tr], starts[tr]), (feats[te], starts[te])


def git_rev() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                              capture_output=True, text=True, cwd=ROOT).stdout.strip()
    except Exception:
        return "unknown"


def main() -> int:
    MODELS.mkdir(parents=True, exist_ok=True)
    print(">> extracting features (pos)")
    pf, ps = windows_from_wav(str(WAV / "srkw_bout_pos.wav"))
    print(f"   pos windows {pf.shape}")
    print(">> extracting features (neg)")
    nf, ns = windows_from_wav(str(WAV / "ambient_neg.wav"))
    print(f"   neg windows {nf.shape}")

    (pf_tr, ps_tr), (pf_te, ps_te) = temporal_split(pf, ps)
    (nf_tr, ns_tr), (nf_te, ns_te) = temporal_split(nf, ns)

    X_tr = np.vstack([pf_tr, nf_tr])
    y_tr = np.concatenate([np.ones(len(pf_tr)), np.zeros(len(nf_tr))]).astype(int)
    X_te = np.vstack([pf_te, nf_te])
    y_te = np.concatenate([np.ones(len(pf_te)), np.zeros(len(nf_te))]).astype(int)

    scaler = StandardScaler().fit(X_tr)
    X_tr_s, X_te_s = scaler.transform(X_tr), scaler.transform(X_te)

    models = {
        "logreg": LogisticRegression(max_iter=2000, class_weight="balanced", C=1.0),
        "rf": RandomForestClassifier(n_estimators=300, class_weight="balanced",
                                     random_state=0, n_jobs=-1),
    }

    results = {}
    fitted = {}
    for name, clf in models.items():
        clf.fit(X_tr_s, y_tr)
        prob = clf.predict_proba(X_te_s)[:, 1]
        pred = (prob >= 0.5).astype(int)
        p, r, f1, _ = precision_recall_fscore_support(
            y_te, pred, average="binary", zero_division=0)
        cm = confusion_matrix(y_te, pred, labels=[0, 1])
        results[name] = {
            "precision": round(float(p), 4),
            "recall": round(float(r), 4),
            "f1": round(float(f1), 4),
            "accuracy": round(float(accuracy_score(y_te, pred)), 4),
            "auprc": round(float(average_precision_score(y_te, prob)), 4),
            "roc_auc": round(float(roc_auc_score(y_te, prob)), 4),
            "confusion_tn_fp_fn_tp": [int(cm[0, 0]), int(cm[0, 1]),
                                      int(cm[1, 0]), int(cm[1, 1])],
        }
        fitted[name] = clf
        print(f"   {name}: F1={results[name]['f1']} P={results[name]['precision']} "
              f"R={results[name]['recall']} AUPRC={results[name]['auprc']}")

    best = max(results, key=lambda k: results[k]["f1"])

    # Label-QC diagnostic: do the labels separate on a simple physical feature
    # (high/low band energy ratio)? Confirms positives are not garbage labels.
    names = feature_names()
    hi_lo_idx = names.index("hi_lo_log")
    qc = {
        "feature": "hi_lo_log (log high>=4kHz / low band energy)",
        "pos_mean": round(float(pf[:, hi_lo_idx].mean()), 4),
        "neg_mean": round(float(nf[:, hi_lo_idx].mean()), 4),
        "centroid_pos_mean_hz": round(float(pf[:, names.index("centroid_mean")].mean()), 1),
        "centroid_neg_mean_hz": round(float(nf[:, names.index("centroid_mean")].mean()), 1),
    }

    joblib.dump({"model": fitted[best], "scaler": scaler, "best": best,
                 "feature_names": names}, MODELS / "srkw_presence_v0.joblib")

    f1_best = results[best]["f1"]
    if f1_best < 0.50:
        claim = "low-confidence / experimental classifier (held-out F1 < 0.50)"
        hud_ok = False
    else:
        claim = "binary SRKW-call presence, estimate + confidence"
        hud_ok = True

    report = {
        "model_version": "bam-srkw-presence-v0",
        "train_run_id": f"{git_rev()}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "task": "binary SRKW-call presence vs absence per window",
        "feature": {
            "window_s": WIN_S, "hop_s": HOP_S, "n_features": N_FEATURES,
            "log_mel_bands": N_MELS, "fft": 2048, "fft_hop": 512,
            "description": "log-mel power spectrogram per-band mean/std/p90 + spectral-shape stats; scipy+numpy, no librosa",
        },
        "data": {
            "station": "Orcasound Lab (rpi_orcasound_lab)",
            "session": "1629941419",
            "bout": "210825_1922-2007_OS_SRKW_L",
            "license": "CC BY-NC-SA 4.0", "attribution": "Orcasound - orcasound.net",
            "label_basis": "bout-level weak labels",
            "pos_windows": int(len(pf)), "neg_windows": int(len(nf)),
            "train_windows": int(len(X_tr)), "test_windows": int(len(X_te)),
            "split": "temporal within each pool (first 70% train, last 30% test, 1-window gap)",
        },
        "models": results,
        "selected_model": best,
        "label_qc": qc,
        "honesty": {
            "claim": claim,
            "hud_claim_ok": hud_ok,
            "reported_as": "estimate + confidence",
            "not_claimed": ["whale count", "pod / individual ID", "ecotype (SRKW vs Bigg's)",
                            "call type", "single vs multiple callers"],
            "known_confounds": [
                "positives (in-bout) and negatives (pre-bout) are different times of the same session; the model may exploit session-level acoustic differences, not call morphology alone",
                "bout-level labels: in-bout windows include non-vocal gaps mislabeled positive; reported metrics are an upper bound on per-call detection",
                "single hydrophone, single bout; cross-station / cross-day generalization NOT evaluated here",
            ],
            "to_strengthen": "align Pod.Cast / OrcaHello / DCLDE-2027 per-annotation windows for window-level labels, call-type, and single-vs-multiple heads (STOP-to-O0: corpora fetch + alignment)",
        },
    }
    REPORT.write_text(json.dumps(report, indent=2))
    print(f">> best={best} F1={f1_best} | report -> {REPORT}")
    print(f">> label QC: {json.dumps(qc)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

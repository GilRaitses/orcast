#!/usr/bin/env python3
"""BAM inference: run the trained real classifier over the demo-window clip and
emit the PRECOMPUTED REAL inference JSON the reenactment lane + integrator
consume. Every window's `presenceConfidence` is a real model posterior, not a
scripted label.

Output: web/public/hydrophone/slice/classification.json
Schema: bsw-acoustic-classification/v1 (presence-only, honest).

Run:  python3 modeling/acoustic/infer_demo.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import joblib

from features import windows_from_wav, WIN_S, HOP_S

ROOT = Path(__file__).resolve().parents[2]
WAV = ROOT / "infra" / "acoustic" / "data" / "wav" / "demo_window.wav"
MODEL = ROOT / "infra" / "acoustic" / "models" / "srkw_presence_v0.joblib"
EVAL = ROOT / "infra" / "acoustic" / "eval_report.json"
OUT = ROOT / "web" / "public" / "hydrophone" / "slice" / "classification.json"

PRESENCE_THRESHOLD = 0.5
SPAWN_FRACTION = 0.10  # >=10% of windows positive -> the clip has a present caller


def main() -> int:
    bundle = joblib.load(MODEL)
    clf, scaler = bundle["model"], bundle["scaler"]
    report = json.loads(EVAL.read_text())

    feats, starts = windows_from_wav(str(WAV))
    prob = clf.predict_proba(scaler.transform(feats))[:, 1]
    pred = prob >= PRESENCE_THRESHOLD

    windows = [
        {
            "tStartS": round(float(t), 3),
            "tEndS": round(float(t + WIN_S), 3),
            "presence": bool(p),
            "presenceConfidence": round(float(c), 4),
        }
        for t, p, c in zip(starts, pred, prob)
    ]

    presence_fraction = float(pred.mean()) if len(pred) else 0.0
    sel = report["selected_model"]
    m = report["models"][sel]
    record = {
        "schema": "bsw-acoustic-classification/v1",
        "model_version": report["model_version"],
        "train_run_id": report["train_run_id"],
        "clipId": "orcasound_lab_20210825_srkw",
        "stationId": "rpi_orcasound_lab",
        "station": {"name": "Orcasound Lab", "lat": 48.5583362, "lng": -123.1735774},
        "audio": {
            "url": "/hydrophone/slice/orcasound_lab_20210825_srkw.m4a",
            "durationS": round(float(starts[-1] + WIN_S), 1) if len(starts) else 0.0,
            "license": "CC BY-NC-SA 4.0",
            "attribution": "Orcasound - orcasound.net",
            "honesty": "measured",
        },
        "window": {"windowS": WIN_S, "hopS": HOP_S, "threshold": PRESENCE_THRESHOLD},
        "classes": ["srkw_call_presence"],
        "eval": {
            "task": report["task"],
            "selected_model": sel,
            "test_f1": m["f1"], "test_precision": m["precision"],
            "test_recall": m["recall"], "test_auprc": m["auprc"],
            "held_out": "temporal within pool",
            "label_basis": report["data"]["label_basis"],
            "known_confounds": report["honesty"]["known_confounds"],
        },
        "honesty": {
            "inference": "measured_model_output",
            "claim": "estimate",
            "wording": "estimated: SRKW call present (confidence X)",
            "not_claimed": report["honesty"]["not_claimed"],
            "spawn": "modeled_3d_placement",
            "motion": "measured_srkw_dtag",
            "crossSensor": "illustrative",
            "representativeness": "Kinematics are representative SRKW DTAG motion, not the recorded animal.",
        },
        "windows": windows,
        "summary": {
            "presenceFraction": round(presence_fraction, 4),
            "meanConfidence": round(float(prob.mean()), 4) if len(prob) else 0.0,
            "clipPresence": bool(presence_fraction >= SPAWN_FRACTION),
            "spawnCount": 1 if presence_fraction >= SPAWN_FRACTION else 0,
            "spawnCountBasis": "presence_only",
        },
    }
    OUT.write_text(json.dumps(record, indent=2))
    print(f">> wrote {OUT}")
    print(f">> windows={len(windows)} presenceFraction={presence_fraction:.3f} "
          f"meanConf={record['summary']['meanConfidence']} "
          f"spawnCount={record['summary']['spawnCount']}")
    print(f">> bytes={OUT.stat().st_size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

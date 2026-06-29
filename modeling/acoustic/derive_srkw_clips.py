#!/usr/bin/env python3
"""Offline: derive REAL behavior->motion clips from the measured SRKW DTAG
driver (Tennessen 2024, CC-BY-4.0). A clip is a time window [t0,t1] into the
real driver; the MOTION is always measured SRKW telemetry. The behavior label
is a MODELED kinematic match (R04), never fabricated motion.

Reads web/public/orca/motion/orca_srkw_oo14_driver.bin (float32, interleaved
(n_samples, 7): t,yaw,pitch,roll,depth,fluke_phase,fluke_amp at 5 Hz) and writes
web/public/orca/motion/clips/manifest.json (web-served so the BRE loader can
fetch it at /orca/motion/clips/manifest.json).

Run:  python3 modeling/acoustic/derive_srkw_clips.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
BIN = ROOT / "web" / "public" / "orca" / "motion" / "orca_srkw_oo14_driver.bin"
MANI = ROOT / "web" / "public" / "orca" / "motion" / "orca_srkw_oo14_driver.json"
OUT = ROOT / "web" / "public" / "orca" / "motion" / "clips" / "manifest.json"

WIN_S = 45.0  # candidate window length


def main() -> int:
    mani = json.loads(MANI.read_text())
    sr = float(mani["sample_rate_hz"])  # 5 Hz
    nch = int(mani["n_channels"])       # 7
    data = np.fromfile(BIN, dtype="<f4")
    n = data.size // nch
    data = data[: n * nch].reshape(n, nch)
    t = data[:, 0]
    yaw, pitch, roll, depth = data[:, 1], data[:, 2], data[:, 3], data[:, 4]
    famp = data[:, 6]

    w = int(round(WIN_S * sr))
    hop = int(round((WIN_S / 3) * sr))
    cands = []
    for s in range(0, n - w + 1, hop):
        e = s + w
        d = depth[s:e]
        # yaw variance via circular spread
        cy, sy = np.cos(yaw[s:e]).mean(), np.sin(yaw[s:e]).mean()
        yaw_steadiness = np.hypot(cy, sy)  # 1 = perfectly steady heading
        cands.append({
            "s": s, "e": e, "t0": float(t[s]), "t1": float(t[e - 1]),
            "depth_mean": float(d.mean()), "depth_range": float(d.max() - d.min()),
            "roll_abs_p90": float(np.percentile(np.abs(roll[s:e]), 90)),
            "yaw_steadiness": float(yaw_steadiness),
            "fluke_amp_mean": float(famp[s:e].mean()),
        })

    def pick(key, reverse=True, **filters):
        pool = [c for c in cands if all(f(c) for f in filters.values())]
        if not pool:
            pool = cands
        return sorted(pool, key=lambda c: c[key], reverse=reverse)[0]

    # Traveling (class 8): steady heading + active fluke + modest depth.
    traveling = pick("yaw_steadiness",
                     shallow=lambda c: c["depth_mean"] < 40,
                     active=lambda c: c["fluke_amp_mean"] > 0.2)
    # Side rolls (class 5): high |roll|.
    side_rolls = pick("roll_abs_p90")
    # Exploratory dive (class 1): largest depth excursion.
    exploratory = pick("depth_range")

    def clip(c, behavior_class, name):
        return {
            "id": name,
            "driverUrl": "/orca/motion/orca_srkw_oo14_driver.json",
            "t0_s": round(c["t0"], 2),
            "t1_s": round(c["t1"], 2),
            "behaviorClass": behavior_class,
            "behaviorName": name,
            "loop": True,
            "honesty": "measured_motion_modeled_label",
            "selection": "srkw_kinematic_match",
            "measured": {
                "depth_mean_m": round(c["depth_mean"], 2),
                "depth_range_m": round(c["depth_range"], 2),
                "roll_abs_p90_deg": round(np.degrees(c["roll_abs_p90"]), 1),
                "yaw_steadiness": round(c["yaw_steadiness"], 3),
                "fluke_amp_mean": round(c["fluke_amp_mean"], 3),
            },
        }

    manifest = {
        "schema": "bsw-behavior-clips/v1",
        "driver": {
            "url": "/orca/motion/orca_srkw_oo14_driver.json",
            "species": "orca", "ecotype": "SRKW", "deployment": mani.get("deployment"),
            "license": mani.get("license"), "dataset_doi": mani.get("dataset_doi"),
            "simulated": False,
        },
        "honesty_note": "Motion is measured SRKW DTAG telemetry. Behavior labels are a modeled kinematic match to the humpback ethogram (R04); the cross-species label is disclosed, never presented as measured orca behavior. Acoustic presence picks WHICH clip spawns; it never drives the trajectory.",
        "representativeness": "Kinematics are representative SRKW DTAG motion, not the recorded animal.",
        "fallback": {
            "id": "continuous", "driverUrl": "/orca/motion/orca_srkw_oo14_driver.json",
            "t0_s": 0.0, "t1_s": round(float(t[-1]), 2), "behaviorClass": None,
            "behaviorName": "unclassified", "loop": True, "honesty": "measured",
            "selection": "continuous_fallback",
        },
        "clips": [
            clip(traveling, 8, "Traveling"),
            clip(side_rolls, 5, "Side_rolls"),
            clip(exploratory, 1, "Exploratory_dives"),
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(manifest, indent=2))
    print(f">> wrote {OUT}")
    for c in manifest["clips"]:
        print(f"   {c['behaviorName']:18s} t=[{c['t0_s']:.1f},{c['t1_s']:.1f}] {c['measured']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

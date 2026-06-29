#!/usr/bin/env python3
"""Bake the operator's REAL humpback DTAG H5 as a labeled CONTRAST baseline.

Two jobs, both honest:
  1. Validate `prebake.py` on REAL per-sample animaltags data by reusing its
     writer, DSP (Az-band fluke extraction), and exact bin/JSON format.
  2. Emit the humpback contrast baseline numbers for the OG-DATA orca-vs-humpback
     table.

The source is the operator's own real humpback (Megaptera novaeangliae) tag
`mn09_203a` ("lavaliers_Calf"), 5 Hz, 128 dives, ~5.5 h. It is REAL data, so the
manifest is `simulated: false`, `species: "humpback"`, `role: "contrast"`. This is
**NOT an orca driver**: the orca twin is never driven by humpback motion. Humpback
kinematics must never be presented as orca.

This file lives under `dev/` and only WRITES under `dev/`. It does not modify
`prebake.py` (it imports its primitives) and does not copy the 54 MB external H5
into the repo -- the H5 is read in place by absolute path.

The H5 here uses a nested layout (`/data/pitch`, `/depth/values`, `/data/Aw.3`,
`/dives/metrics/*`) rather than the animaltags sensor-struct groups `prebake.bake_h5`
expects, and it already carries the DERIVED pitch/roll/heading product. So this
adapter reads the explicit documented paths (HUMPBACK_CONTRAST_DATA.md) and feeds
them through the SAME `write_track()` writer, proving the format pipeline on real
per-sample data.
"""
from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from prebake import (  # noqa: E402
    FORMAT_NAME,
    FORMAT_VERSION,
    MotionTrack,
    bandpass_fft,
    stroke_phase_amplitude,
    write_track,
)

# External, read-only. Do NOT copy into orcast.
H5_PATH = "/Users/gilraitses/whale-behavior-analysis/Visualization_Poster_Appendix/data/dive_analysis.h5"
LOG_CSV = "/Users/gilraitses/whale-behavior-analysis/Visualization_Poster_Appendix/data/log_mn09_203a.csv"

ANIMAL_ID = "mn09_203a"
ANIMAL_NAME = "lavaliers_Calf"
SPECIES = "humpback"  # Megaptera novaeangliae
ROLE = "contrast"

# Documented H5 channel -> rig-DOF paths (HUMPBACK_CONTRAST_DATA.md).
PATHS = {
    "depth": "depth/values",       # metres, +down
    "pitch": "data/pitch",         # radians
    "roll": "data/roll",           # radians
    "head": "data/head",           # radians (heading)
    "az": "data/Aw.3",             # whale-frame dorso-ventral accel (heave)
    "time": "eti/values",          # seconds
    "sample_rate": "analysis/metadata/sample_rate",
}

# Humpback stroke band for the Az fluke-beat extraction. Distinct from the orca
# STROKE_BAND_HZ (0.3-1.0): humpback fluke beat is slower (~0.2-0.3 Hz). The lower
# edge (0.12 Hz) excludes the slow dive-cycle / posture drift so the fluke channel
# carries the stroke oscillation only; that drift belongs to depth/pitch.
HUMPBACK_STROKE_BAND_HZ = (0.12, 0.6)


def _fluke_frequency_hz(az: np.ndarray, fs: float, h5) -> Dict[str, Any]:
    """Fluke-beat frequency from the Az band, with a stroke-peak cross-check.

    Whole-record FFT is biased low because humpbacks glide intermittently, so the
    tag's own detected stroke peaks (a tagtools stroke detector run on the
    whale-frame accel) are the credible estimator. Both are reported honestly.
    """
    x = bandpass_fft(az, fs, *HUMPBACK_STROKE_BAND_HZ)
    spec = np.abs(np.fft.rfft(x - x.mean())) ** 2
    fr = np.fft.rfftfreq(len(x), d=1.0 / fs)
    m = (fr >= HUMPBACK_STROKE_BAND_HZ[0]) & (fr <= HUMPBACK_STROKE_BAND_HZ[1])
    az_band_fpk = float(fr[m][int(np.argmax(spec[m]))])

    out: Dict[str, Any] = {
        "method": "Az-band (Aw.3) dominant frequency + tag stroke-peak cross-check",
        "az_band_spectral_fpk_hz": round(az_band_fpk, 4),
        "az_band_spectral_caveat": (
            "Whole-record FFT is biased low by intermittent stroking/glides; use the "
            "stroke-peak rate as the headline fluke-beat frequency."
        ),
    }
    peaks_path = "analysis/tagtools/behaviors/strokes/peaks"
    if peaks_path in h5:
        pk = np.sort(np.asarray(h5[peaks_path][()]))
        ip = np.diff(pk) / fs
        ip = ip[(ip > 1.0) & (ip < 15.0)]
        if ip.size:
            med = float(np.median(ip))
            out["stroke_peak_median_interval_s"] = round(med, 3)
            out["stroke_peak_fluke_hz"] = round(1.0 / med, 4)
            out["stroke_peak_count"] = int(pk.size)
    out["fluke_beat_hz"] = out.get("stroke_peak_fluke_hz", out["az_band_spectral_fpk_hz"])
    return out


def _dist(arr: np.ndarray) -> Dict[str, float]:
    a = np.asarray(arr, dtype=float)
    a = a[np.isfinite(a)]
    return {
        "min": round(float(np.min(a)), 3),
        "median": round(float(np.median(a)), 3),
        "max": round(float(np.max(a)), 3),
        "mean": round(float(np.mean(a)), 3),
        "n": int(a.size),
    }


def _behavior_mix() -> List[Dict[str, Any]]:
    """Behavior mix from the event log (fraction of annotated time per event)."""
    p = Path(LOG_CSV)
    if not p.exists():
        return []
    secs: Dict[str, float] = defaultdict(float)
    fs = 5.0
    with p.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            try:
                start = float(row["eventStart"])
                end = float(row["eventEnd"])
                fs = float(row.get("sampleHz") or fs)
            except (KeyError, ValueError):
                continue
            label = (row.get("event") or "").strip() or "unlabeled"
            secs[label] += max(end - start, 0.0) / fs
    total = sum(secs.values()) or 1.0
    mix = [
        {"behavior": k, "seconds": round(v, 1), "fraction": round(v / total, 4)}
        for k, v in secs.items()
    ]
    mix.sort(key=lambda d: d["fraction"], reverse=True)
    return mix


def bake() -> Dict[str, Any]:
    import h5py

    h5_path = Path(H5_PATH)
    if not h5_path.exists():
        raise SystemExit(f"humpback H5 not found (external, read-only): {h5_path}")

    with h5py.File(str(h5_path), "r") as h5:
        fs = float(np.ravel(h5[PATHS["sample_rate"]][()])[0])
        depth = np.asarray(h5[PATHS["depth"]][()], dtype=float)
        pitch = np.asarray(h5[PATHS["pitch"]][()], dtype=float)
        roll = np.asarray(h5[PATHS["roll"]][()], dtype=float)
        head = np.asarray(h5[PATHS["head"]][()], dtype=float)
        az = np.asarray(h5[PATHS["az"]][()], dtype=float)
        t = np.asarray(h5[PATHS["time"]][()], dtype=float)
        t = t - t[0]

        n = min(len(depth), len(pitch), len(roll), len(head), len(az), len(t))
        depth, pitch, roll, head, az, t = (a[:n] for a in (depth, pitch, roll, head, az, t))

        # Fluke beat: SAME Az-band method as the dev track, humpback band.
        phase, amp = stroke_phase_amplitude(az, fs, band=HUMPBACK_STROKE_BAND_HZ)

        # ---- contrast baseline over the 128 dives (real, tag-computed metrics) ----
        def metric(name: str) -> np.ndarray:
            return np.asarray(h5[f"dives/metrics/{name}"][()], dtype=float)

        n_dives = int(h5["dives/dive_indices"].shape[0])
        baseline = {
            "n_dives": n_dives,
            "deployment_duration_s": round(float(t[-1]), 1),
            "sample_rate_hz": fs,
            "max_depth_m": _dist(metric("max_depth")),
            "descent_rate_mps": _dist(metric("descent_rate")),
            "ascent_rate_mps": _dist(metric("ascent_rate")),
            "descent_duration_s": _dist(metric("descent_duration")),
            "bottom_duration_s": _dist(metric("bottom_duration")),
            "ascent_duration_s": _dist(metric("ascent_duration")),
            "dive_duration_s": _dist(metric("duration")),
            "depth_track_range_m": [round(float(depth.min()), 3), round(float(depth.max()), 3)],
            "fluke_beat": _fluke_frequency_hz(az, fs, h5),
            "behavior_mix": _behavior_mix(),
        }

    track = MotionTrack(
        sample_rate_hz=fs,
        t_s=t,
        body_yaw_rad=head,
        body_pitch_rad=pitch,
        body_roll_rad=roll,
        depth_m=depth,
        fluke_phase_rad=phase,
        fluke_amplitude=amp,
        simulated=False,
        provenance=(
            "REAL humpback (Megaptera novaeangliae) DTAG deployment "
            f"{ANIMAL_ID!r} ({ANIMAL_NAME!r}), baked from the operator's external H5 "
            f"{H5_PATH} by dev/bake_humpback_contrast.py using prebake.py primitives. "
            "Role: CONTRAST baseline only. This is NOT an orca driver; the orca twin "
            "is never driven by humpback motion and humpback kinematics are never "
            "presented as orca."
        ),
        declination_deg_applied=0.0,
        source={
            "type": "h5-real",
            "species": SPECIES,
            "role": ROLE,
            "animal_id": ANIMAL_ID,
            "animal_name": ANIMAL_NAME,
            "h5_path": H5_PATH,
            "h5_channel_paths": PATHS,
            "measured": True,
            "derived_orientation_product": True,
        },
        notes=[
            "simulated=false: REAL humpback data (operator's own).",
            "role=contrast: baseline for the orca-vs-humpback table; NOT the orca driver.",
            "Orientation is the H5's already-derived pitch/roll/head product (radians).",
            "Fluke beat extracted from the whale-frame dorso-ventral Aw.3 (Az) channel "
            f"with a humpback stroke band {list(HUMPBACK_STROKE_BAND_HZ)} Hz (slower than "
            "the orca 0.3-1.0 Hz band).",
            "Validates prebake.py's bin/JSON format and Az-band fluke method on real "
            "per-sample animaltags data.",
        ],
    )

    out_dir = Path(__file__).resolve().parent
    base = f"humpback_{ANIMAL_ID}_contrast"
    bin_path = out_dir / f"{base}.bin"
    manifest_path = out_dir / f"{base}.json"
    manifest = write_track(track, bin_path, manifest_path)

    # Augment the manifest with species/role/baseline and the ACTUAL stroke band used
    # (write_track stamps the orca default), then rewrite under dev/.
    manifest["species"] = SPECIES
    manifest["role"] = ROLE
    manifest["animal_id"] = ANIMAL_ID
    manifest["stroke_band_hz"] = list(HUMPBACK_STROKE_BAND_HZ)
    manifest["contrast_baseline"] = baseline
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    return manifest


def main() -> int:
    manifest = bake()
    b = manifest["contrast_baseline"]
    print(
        f"baked {manifest['bin_file']} ({manifest['bin_bytes']} bytes) | "
        f"format {FORMAT_NAME} v{FORMAT_VERSION} | species={manifest['species']} "
        f"role={manifest['role']} simulated={manifest['simulated']} "
        f"n_samples={manifest['n_samples']} rate={manifest['sample_rate_hz']}Hz"
    )
    print(
        f"depth range (m): {b['depth_track_range_m']} | "
        f"max_depth median={b['max_depth_m']['median']} max={b['max_depth_m']['max']} | "
        f"descent={b['descent_rate_mps']['median']} ascent={b['ascent_rate_mps']['median']} m/s | "
        f"fluke={b['fluke_beat']['fluke_beat_hz']} Hz"
    )
    print("top behaviors:", [m["behavior"] for m in b["behavior_mix"][:4]])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

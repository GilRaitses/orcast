#!/usr/bin/env python3
"""Synthesize the LABELED SIMULATED per-sample orca dev track.

WHY THIS EXISTS (honesty, read first):
The only in-repo biologging fixture, ``data/dtag_analysis_results.json``
(``cascadia_2010_k33_test``), is AGGREGATED dive analysis -- per-dive
max_depth/descent_rate/ascent_rate/bottom_time/mean_dba plus surface and
energetic summaries. It is itself flagged ``simulated: true`` (methodology
"TagTools-inspired") and contains NO per-sample channels (see
OG-R_h5_mapping.md section 5). It therefore cannot drive a per-sample orientation
or a per-sample Az fluke beat on its own.

O0 APPROVED (SIGN_OFF.md decision 3) synthesizing a per-sample dev track from that
aggregate, marked SIMULATED everywhere. This script does exactly that: it shapes a
plausible descent/bottom/ascent depth profile per dive event, derives a plausible
pitch from the depth rate, adds a slow heading drift and modest banking roll, and
synthesizes an Az-equivalent stroke oscillation in the orca stroke band so the
fluke beats. The output is written through the SAME writer the real H5 baker uses
(prebake.write_track), so the bin/JSON format is byte-identical.

This output is a SYNTHESIZED DEV FIXTURE, NOT a measured swim. ``simulated`` is
true in the manifest and the provenance and notes say so plainly. Nothing here may
be presented as measured animal data.

Dependencies: numpy only (no h5py needed for the synthesis).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

# Import the shared format + writer from the sibling baker.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from prebake import (  # noqa: E402
    FORMAT_NAME,
    FORMAT_VERSION,
    STROKE_BAND_HZ,
    MotionTrack,
    write_track,
)

# Determinism: a fixed seed so the dev fixture is reproducible byte-for-byte.
SEED = 20260628

# Synthesis sample rate. The fixture's data_summary implies ~50 Hz upstream
# (total_samples 36000 / (duration_hours 0.2 * 3600) = 50), so we reproduce that
# claimed per-sample rate for the dev track.
SYNTH_RATE_HZ = 50.0

# Plausibility anchors from OG-R_h5_mapping.md section 3 / Wright et al. 2017.
CRUISE_SPEED_MPS = 2.3  # orca cruising ~2.1-2.7 m/s; used to turn depth-rate into pitch.
MAX_PITCH_RAD = np.deg2rad(80.0)


def _smoothstep(x: np.ndarray) -> np.ndarray:
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3.0 - 2.0 * x)


def _dive_depth_segment(t_local: np.ndarray, ev: Dict[str, Any]) -> np.ndarray:
    """Depth (m, positive down) over a dive window, shaped from the aggregate event.

    descent (rate-sized, smoothstep) -> bottom hold (bottom_time) -> ascent
    (rate-sized, smoothstep). Portions are scaled to fit the event window so the
    profile is internally smooth even where the aggregate's rates/duration are only
    roughly self-consistent (it is a simulated aggregate)."""
    window = float(t_local[-1] - t_local[0]) if t_local.size > 1 else 1.0
    max_depth = float(ev["max_depth"])
    desc = max_depth / max(float(ev["descent_rate"]), 1e-6)
    asc = max_depth / max(float(ev["ascent_rate"]), 1e-6)
    bottom = max(float(ev.get("bottom_time", 0.0)), 0.0)
    total = desc + bottom + asc
    if total <= 0:
        return np.zeros_like(t_local)
    scale = window / total
    desc *= scale
    bottom *= scale
    asc *= scale

    tt = t_local - t_local[0]
    depth = np.zeros_like(tt)
    # descent
    d_mask = tt < desc
    depth[d_mask] = max_depth * _smoothstep(tt[d_mask] / max(desc, 1e-6))
    # bottom hold (gentle undulation, not a flat line)
    b_mask = (tt >= desc) & (tt < desc + bottom)
    undulation = 0.04 * max_depth * np.sin(2.0 * np.pi * 0.15 * (tt[b_mask] - desc))
    depth[b_mask] = max_depth + undulation
    # ascent
    a_mask = tt >= desc + bottom
    frac = (tt[a_mask] - desc - bottom) / max(asc, 1e-6)
    depth[a_mask] = max_depth * (1.0 - _smoothstep(frac))
    return np.clip(depth, 0.0, None)


def synthesize(fixture: Dict[str, Any]) -> MotionTrack:
    rng = np.random.default_rng(SEED)

    ds = fixture.get("data_summary", {})
    duration_s = float(ds.get("duration_hours", 0.2)) * 3600.0
    n = int(round(duration_s * SYNTH_RATE_HZ))
    # Honor the fixture's claimed total_samples if it matches the implied rate.
    n = int(ds.get("total_samples", n)) if ds.get("total_samples") else n
    fs = SYNTH_RATE_HZ
    duration_s = (n - 1) / fs
    t = np.arange(n, dtype=np.float64) / fs

    dives: List[Dict[str, Any]] = (
        fixture.get("dive_analysis", {}).get("dive_events", []) or []
    )

    # --- Depth track from aggregated dive events (0 at surface). ---
    depth = np.zeros(n, dtype=np.float64)
    for ev in dives:
        start = float(ev["start_time"])
        end = float(ev["end_time"])
        i0 = max(int(np.floor(start * fs)), 0)
        i1 = min(int(np.ceil(end * fs)), n)
        if i1 - i0 < 2:
            continue
        depth[i0:i1] = _dive_depth_segment(t[i0:i1], ev)

    # Light smoothing of the stitched depth so segment joins stay C1-ish.
    win = max(int(0.3 * fs), 3)
    kernel = np.ones(win) / win
    depth = np.convolve(depth, kernel, mode="same")
    depth = np.clip(depth, 0.0, None)

    # --- Pitch from vertical speed vs nominal horizontal cruise speed. ---
    # Descending (depth increasing) => nose-down => negative pitch (nose-up positive).
    d_depth_dt = np.gradient(depth, 1.0 / fs)
    pitch = -np.arctan2(d_depth_dt, CRUISE_SPEED_MPS)
    pitch = np.clip(pitch, -MAX_PITCH_RAD, MAX_PITCH_RAD)

    # --- Heading: slow drift (band-limited random walk) + gentle per-dive turns. ---
    steps = rng.normal(0.0, 1.0, size=n)
    drift = np.cumsum(steps)
    # band-limit by a long moving average so heading turns are slow and smooth
    hwin = max(int(8.0 * fs), 5)
    drift = np.convolve(drift, np.ones(hwin) / hwin, mode="same")
    drift = drift - drift[0]
    scale = np.deg2rad(40.0) / (np.max(np.abs(drift)) + 1e-9)
    heading = drift * scale  # radians, smooth slow drift within +/-~40 deg

    # --- Roll: bank into heading changes, small, with the full range available. ---
    d_head_dt = np.gradient(heading, 1.0 / fs)
    roll = np.clip(2.5 * d_head_dt, np.deg2rad(-35.0), np.deg2rad(35.0))
    rwin = max(int(1.0 * fs), 3)
    roll = np.convolve(roll, np.ones(rwin) / rwin, mode="same")

    # --- Fluke beat: synthetic Az-equivalent oscillation in the orca stroke band. ---
    # Effort (and thus stroke amplitude + a little frequency) tracks active swimming:
    # high during descent/ascent, near zero at the surface and on a gliding bottom.
    mean_dba = float(
        np.mean([ev.get("mean_dba", 0.9) for ev in dives]) if dives else 0.9
    )
    vert_speed = np.abs(d_depth_dt)
    effort = vert_speed / (np.percentile(vert_speed, 95) + 1e-9)
    effort = np.clip(effort, 0.0, 1.0)
    ewin = max(int(0.5 * fs), 3)
    effort = np.convolve(effort, np.ones(ewin) / ewin, mode="same")

    f_lo, f_hi = STROKE_BAND_HZ
    f_cruise = 0.45  # cruising stroke ~0.4-0.6 Hz
    inst_freq = np.clip(f_cruise + 0.25 * effort, f_lo, f_hi)
    phase = np.mod(2.0 * np.pi * np.cumsum(inst_freq) / fs, 2.0 * np.pi)
    # amplitude scaled by effort and the aggregate mean DBA, normalized to 0..1
    amp = np.clip(effort * (0.6 + 0.4 * np.clip(mean_dba, 0.0, 1.0)), 0.0, 1.0)

    provenance = (
        "SYNTHESIZED DEV FIXTURE -- NOT a measured swim. Generated by "
        "infra/orca/biologging/dev/make_dev_track.py (seed "
        f"{SEED}) from the AGGREGATED, already-simulated fixture "
        "data/dtag_analysis_results.json (deployment "
        f"{fixture.get('deployment_id')!r}, methodology "
        f"{fixture.get('methodology')!r}). Per-sample depth is shaped from the "
        "aggregated dive events; pitch is derived from depth rate; heading is a slow "
        "synthetic drift; roll banks into heading changes; the fluke beat is a "
        "synthetic Az-equivalent oscillation in the orca stroke band. This exercises "
        "the rig and the channel->DOF mapping; it asserts nothing measured."
    )
    notes = [
        "simulated=true: this is a synthesized dev track, not measured telemetry.",
        "Source fixture is aggregated dive analysis and is itself simulated "
        "(simulated:true, TagTools-inspired); it has no per-sample channels.",
        "Horizontal world position is NOT included; the science reconstructs it by "
        "dead-reckoning and georeferencing (OG-R_h5_mapping.md 3.3). Any horizontal "
        "track in the twin must be labeled reconstructed, not measured GPS.",
        "Replace with prebake.py output from a real, agreement-covered H5 when one "
        "exists; that path is partnership-gated (SIGN_OFF.md decision 4).",
    ]

    return MotionTrack(
        sample_rate_hz=fs,
        t_s=t,
        body_yaw_rad=heading,
        body_pitch_rad=pitch,
        body_roll_rad=roll,
        depth_m=depth,
        fluke_phase_rad=phase,
        fluke_amplitude=amp,
        simulated=True,
        provenance=provenance,
        declination_deg_applied=0.0,
        source={
            "type": "synthesized-dev-fixture",
            "from_fixture": "data/dtag_analysis_results.json",
            "deployment_id": fixture.get("deployment_id"),
            "fixture_methodology": fixture.get("methodology"),
            "fixture_simulated": True,
            "seed": SEED,
            "synth_rate_hz": fs,
            "generator": "infra/orca/biologging/dev/make_dev_track.py",
            "measured": False,
        },
        notes=notes,
    )


def main() -> int:
    here = Path(__file__).resolve().parent
    repo_root = here.parents[3]
    fixture_path = repo_root / "data" / "dtag_analysis_results.json"
    if not fixture_path.exists():
        print(f"error: fixture not found: {fixture_path}", file=sys.stderr)
        return 2
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))

    track = synthesize(fixture)
    bin_path = here / "orca_dev_track.bin"
    manifest_path = here / "orca_dev_track.json"
    manifest = write_track(track, bin_path, manifest_path)
    print(
        f"wrote {bin_path.name} ({manifest['bin_bytes']} bytes) + {manifest_path.name} "
        f"| format {FORMAT_NAME} v{FORMAT_VERSION} "
        f"| n_samples={manifest['n_samples']} rate={manifest['sample_rate_hz']}Hz "
        f"duration={manifest['duration_s']:.1f}s simulated={manifest['simulated']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

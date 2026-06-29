"""Tagtools-style processing stages, re-implemented in numpy (no R runtime).

Stages mirror the documented tagtools/animaltags pipeline and the products that
already exist in the real h5 (`analysis/tagtools/*`, `analysis/animal_frame_metrics/*`,
`dives/*`). Each stage is honest about being a documented re-implementation and
records the reference product it reproduces, so the studio is auditable and the
console can invoke any single stage.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

import numpy as np

from .io import SensorData


@dataclass
class StepResult:
    """Result of one pipeline stage, carrying provenance + a small summary.

    `summary` is small and safe to commit/serve. `heavy` holds full-resolution
    arrays that must go to the box, never git.
    """

    step_id: str
    title: str
    truth_label: str
    summary: Dict[str, Any]
    provenance: Dict[str, Any]
    reproduces_h5_path: Optional[str] = None
    heavy: Dict[str, np.ndarray] = field(default_factory=dict)


def _running_mean(x: np.ndarray, win: int) -> np.ndarray:
    if win < 2:
        return x.copy()
    kernel = np.ones(win, dtype=float) / float(win)
    return np.convolve(x, kernel, mode="same")


def step_calibration(sensor: SensorData) -> StepResult:
    """Stage 1 - calibration check on the whale-frame accelerometer.

    The h5 already holds calibrated whale-frame accel (Aw). This stage verifies
    the calibration by checking the static (low-pass) acceleration magnitude,
    which should sit near 1 g (~9.81 m/s^2) when the animal is not accelerating.
    """
    fs = sensor.sample_rate_hz
    acc = sensor.whale_frame_accel
    mag = np.linalg.norm(acc, axis=1)
    win = max(1, int(round(fs * 2.0)))
    static_mag = _running_mean(mag, win)
    return StepResult(
        step_id="tagtools.calibration",
        title="Accelerometer calibration check",
        truth_label="derived",
        reproduces_h5_path="data/Aw.{1,2,3}",
        summary={
            "units": "g",
            "static_accel_mean_g": float(np.mean(static_mag)),
            "static_accel_std_g": float(np.std(static_mag)),
            "expected_static_g": 1.0,
            "low_pass_window_samples": win,
            "n_samples": int(mag.size),
        },
        provenance={
            "method": "low-pass (running mean) magnitude of whale-frame accel",
            "inputs": ["Aw.1", "Aw.2", "Aw.3"],
            "runtime": "numpy (no R/animaltags)",
        },
        heavy={"accel_magnitude": mag},
    )


def step_orientation(sensor: SensorData) -> StepResult:
    """Stage 2 - orientation cross-check (pitch/roll from accel vs provided).

    Reproduces the spirit of `analysis/orientation_comparison/*`: derive pitch
    and roll from the calibrated accelerometer and compare against the provided
    pitch/roll channels. Reports mean absolute difference (radians).
    """
    aw1 = sensor.col("Aw.1")
    aw2 = sensor.col("Aw.2")
    aw3 = sensor.col("Aw.3")
    # tagtools a2pr convention: pitch from longitudinal axis, roll from lateral.
    calc_pitch = np.arctan2(aw1, np.sqrt(aw2 ** 2 + aw3 ** 2))
    calc_roll = np.arctan2(aw2, aw3)
    ref_pitch = sensor.col("pitch")
    ref_roll = sensor.col("roll")
    pitch_mad = float(np.mean(np.abs(calc_pitch - ref_pitch)))
    # Compare on the unit circle so a pure convention offset is not double-counted.
    roll_diff = np.angle(np.exp(1j * (calc_roll - ref_roll)))
    roll_mad = float(np.mean(np.abs(roll_diff)))
    return StepResult(
        step_id="tagtools.orientation",
        title="Orientation cross-check",
        truth_label="derived",
        reproduces_h5_path="analysis/orientation_comparison/{pitch,roll}",
        summary={
            "pitch_mean_abs_diff_rad": pitch_mad,
            "roll_mean_abs_diff_rad": roll_mad,
            "n_samples": int(calc_pitch.size),
        },
        provenance={
            "method": "pitch/roll from calibrated accel (a2pr-style); compared to provided channels",
            "inputs": ["Aw.1", "Aw.2", "Aw.3", "pitch", "roll"],
            "runtime": "numpy (no R/animaltags)",
        },
        heavy={"calc_pitch": calc_pitch, "calc_roll": calc_roll},
    )


def step_odba(sensor: SensorData, filter_seconds: float = 2.0) -> StepResult:
    """Stage 3 - Overall Dynamic Body Acceleration.

    Reproduces `analysis/animal_frame_metrics/odba`: high-pass the whale-frame
    accel (subtract a running-mean static component) and sum the absolute
    dynamic components across the three axes.
    """
    fs = sensor.sample_rate_hz
    win = max(2, int(round(fs * filter_seconds)))
    acc = sensor.whale_frame_accel
    dynamic = np.empty_like(acc)
    for axis in range(3):
        static = _running_mean(acc[:, axis], win)
        dynamic[:, axis] = acc[:, axis] - static
    odba = np.sum(np.abs(dynamic), axis=1)
    return StepResult(
        step_id="tagtools.odba",
        title="Overall Dynamic Body Acceleration (ODBA)",
        truth_label="derived",
        reproduces_h5_path="analysis/animal_frame_metrics/odba",
        summary={
            "units": "g",
            "odba_mean_g": float(np.mean(odba)),
            "odba_p95_g": float(np.percentile(odba, 95)),
            "odba_max_g": float(np.max(odba)),
            "high_pass_window_samples": win,
            "n_samples": int(odba.size),
        },
        provenance={
            "method": "sum |accel - running_mean(accel)| over x,y,z (high-pass ODBA)",
            "inputs": ["Aw.1", "Aw.2", "Aw.3"],
            "filter_cutoff_seconds": filter_seconds,
            "runtime": "numpy (no R/animaltags)",
        },
        heavy={"odba": odba},
    )


def step_dive_detection(
    sensor: SensorData,
    surface_threshold_m: float = 2.0,
    min_dive_seconds: float = 10.0,
) -> StepResult:
    """Stage 4 - dive detection from the depth (pressure) channel.

    Reproduces `dives/dive_indices` (the reference h5 reports 128 dives). A dive
    is a contiguous run below `surface_threshold_m` lasting at least
    `min_dive_seconds`. Output per dive: (start, max_depth, end) indices.
    """
    fs = sensor.sample_rate_hz
    depth = sensor.depth_m
    below = depth > surface_threshold_m
    min_len = int(round(fs * min_dive_seconds))

    dives: List[List[int]] = []
    i = 0
    n = depth.size
    while i < n:
        if below[i]:
            start = i
            while i < n and below[i]:
                i += 1
            end = i - 1
            if (end - start + 1) >= min_len:
                seg = depth[start : end + 1]
                max_idx = start + int(np.argmax(seg))
                dives.append([int(start), int(max_idx), int(end)])
        else:
            i += 1

    dive_indices = np.array(dives, dtype=np.int64) if dives else np.zeros((0, 3), dtype=np.int64)
    durations = (
        (dive_indices[:, 2] - dive_indices[:, 0]) / fs if dive_indices.size else np.zeros(0)
    )
    max_depths = (
        np.array([depth[d[1]] for d in dives]) if dives else np.zeros(0)
    )
    return StepResult(
        step_id="tagtools.dive_detection",
        title="Dive detection",
        truth_label="derived",
        reproduces_h5_path="dives/dive_indices",
        summary={
            "n_dives_detected": int(dive_indices.shape[0]),
            "reference_h5_n_dives": 128,
            "surface_threshold_m": surface_threshold_m,
            "min_dive_seconds": min_dive_seconds,
            "mean_dive_duration_s": float(np.mean(durations)) if durations.size else 0.0,
            "mean_max_depth_m": float(np.mean(max_depths)) if max_depths.size else 0.0,
            "deepest_dive_m": float(np.max(max_depths)) if max_depths.size else 0.0,
        },
        provenance={
            "method": "threshold + min-duration runs on depth(pressure); per-dive argmax",
            "inputs": ["p"],
            "runtime": "numpy (no R/animaltags)",
            "note": "recomputed count may differ from the reference 128; parameters reported, not tuned to match",
        },
        heavy={"dive_indices": dive_indices, "max_depths": max_depths, "durations": durations},
    )


def step_stroke_glide(
    sensor: SensorData,
    stroke_band_seconds: float = 5.0,
) -> StepResult:
    """Stage 5 - stroke / glide detection.

    Reproduces `analysis/tagtools/behaviors/{strokes,glides}` (reference: 2405
    stroke peaks, 2439 troughs, 670 glides). Band-passes a fluking-sensitive
    axis, finds zero-up/down crossings as stroke peaks/troughs, and labels
    low-amplitude spans as glides.
    """
    fs = sensor.sample_rate_hz
    # Heave axis (dorsoventral) carries the fluke stroke signal most strongly.
    heave = sensor.col("Aw.3")
    win = max(2, int(round(fs * stroke_band_seconds)))
    dynamic = heave - _running_mean(heave, win)

    sign = np.sign(dynamic)
    sign[sign == 0] = 1
    crossings = np.where(np.diff(sign) != 0)[0]

    peaks: List[int] = []
    troughs: List[int] = []
    for k in range(len(crossings) - 1):
        a, b = crossings[k], crossings[k + 1]
        seg = dynamic[a : b + 1]
        if seg.size == 0:
            continue
        if np.mean(seg) >= 0:
            peaks.append(int(a + np.argmax(seg)))
        else:
            troughs.append(int(a + np.argmin(seg)))

    amp = np.abs(dynamic)
    glide_thresh = float(np.percentile(amp, 25))
    low = amp < glide_thresh
    min_glide = int(round(fs * 3.0))
    glides: List[List[int]] = []
    i = 0
    n = amp.size
    while i < n:
        if low[i]:
            start = i
            while i < n and low[i]:
                i += 1
            if (i - start) >= min_glide:
                glides.append([int(start), int(i - 1)])
        else:
            i += 1

    return StepResult(
        step_id="tagtools.stroke_glide",
        title="Stroke / glide detection",
        truth_label="derived",
        reproduces_h5_path="analysis/tagtools/behaviors/{strokes,glides}",
        summary={
            "n_stroke_peaks": len(peaks),
            "n_stroke_troughs": len(troughs),
            "n_glides": len(glides),
            "reference_h5": {"stroke_peaks": 2405, "stroke_troughs": 2439, "glides": 670},
            "glide_amplitude_threshold_g": glide_thresh,
        },
        provenance={
            "method": "band-pass heave (Aw.3); zero-crossing peaks/troughs; low-amplitude glides",
            "inputs": ["Aw.3"],
            "runtime": "numpy (no R/animaltags)",
            "note": "recomputed counts differ from reference; method documented, not tuned to match",
        },
        heavy={
            "stroke_peaks": np.array(peaks, dtype=np.int64),
            "stroke_troughs": np.array(troughs, dtype=np.int64),
            "glides": np.array(glides, dtype=np.int64) if glides else np.zeros((0, 2), np.int64),
        },
    )


PipelineStep = Callable[[SensorData], StepResult]

PIPELINE_STEPS: Dict[str, PipelineStep] = {
    "tagtools.calibration": step_calibration,
    "tagtools.orientation": step_orientation,
    "tagtools.odba": step_odba,
    "tagtools.dive_detection": step_dive_detection,
    "tagtools.stroke_glide": step_stroke_glide,
}

"""Console-invocable descriptors for the tagtools studio steps.

These are the reusable "what the console can invoke" records. B3 registers the
matching managed HUD skills in Central Casting; this module is the single source
of truth for the step contract (inputs, outputs, honesty label).
"""

from __future__ import annotations

from typing import Dict, List


def step_descriptors() -> List[Dict[str, object]]:
    return [
        {
            "step_id": "tagtools.calibration",
            "title": "Accelerometer calibration check",
            "inputs": ["Aw.1", "Aw.2", "Aw.3"],
            "outputs": ["static_accel_mean", "static_accel_std"],
            "truth_label": "derived",
            "reproduces_h5_path": "data/Aw.{1,2,3}",
            "reproducible": True,
            "runtime": "numpy",
        },
        {
            "step_id": "tagtools.orientation",
            "title": "Orientation cross-check",
            "inputs": ["Aw.1", "Aw.2", "Aw.3", "pitch", "roll"],
            "outputs": ["pitch_mean_abs_diff_rad", "roll_mean_abs_diff_rad"],
            "truth_label": "derived",
            "reproduces_h5_path": "analysis/orientation_comparison/{pitch,roll}",
            "reproducible": True,
            "runtime": "numpy",
        },
        {
            "step_id": "tagtools.odba",
            "title": "Overall Dynamic Body Acceleration",
            "inputs": ["Aw.1", "Aw.2", "Aw.3"],
            "outputs": ["odba_mean_g", "odba_p95_g", "odba_max_g"],
            "truth_label": "derived",
            "reproduces_h5_path": "analysis/animal_frame_metrics/odba",
            "reproducible": True,
            "runtime": "numpy",
        },
        {
            "step_id": "tagtools.dive_detection",
            "title": "Dive detection",
            "inputs": ["p"],
            "outputs": ["n_dives_detected", "mean_dive_duration_s", "deepest_dive_m"],
            "truth_label": "derived",
            "reproduces_h5_path": "dives/dive_indices",
            "reproducible": True,
            "runtime": "numpy",
        },
        {
            "step_id": "tagtools.stroke_glide",
            "title": "Stroke / glide detection",
            "inputs": ["Aw.3"],
            "outputs": ["n_stroke_peaks", "n_stroke_troughs", "n_glides"],
            "truth_label": "derived",
            "reproduces_h5_path": "analysis/tagtools/behaviors/{strokes,glides}",
            "reproducible": True,
            "runtime": "numpy",
        },
    ]

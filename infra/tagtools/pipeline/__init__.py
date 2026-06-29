"""Reusable, offline tagtools/animaltags-style processing pipeline (BSS lane).

This package re-implements a small set of biologging DTAG processing stages in
pure Python + numpy. It deliberately does NOT depend on the R `tagtools` /
`animaltags` runtime (O0 gate 2, posture 2): the algorithms here are documented
re-implementations that consume already-derived h5/CSV products and reproduce
tagtools-style outputs offline. Heavy per-sample outputs are written to the box,
not git (see infra/tagtools/BOX_MANIFEST.md).

Each stage is a `PipelineStep` that returns a `StepResult` carrying provenance,
so the studio is a reusable processing surface the orchestrated console can
invoke, not a one-off script.
"""

from .steps import (
    PIPELINE_STEPS,
    StepResult,
    step_calibration,
    step_dive_detection,
    step_odba,
    step_orientation,
    step_stroke_glide,
)

__all__ = [
    "PIPELINE_STEPS",
    "StepResult",
    "step_calibration",
    "step_orientation",
    "step_odba",
    "step_dive_detection",
    "step_stroke_glide",
]

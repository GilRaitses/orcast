#!/usr/bin/env python3
"""Offline bake for the BSS tagtools studio (O0 gate 2, posture 2).

Reads the REAL DTAG products, runs every tagtools stage, and writes:

  1. A SMALL, real, derived summary fixture the web annotation studio consumes
     (web/lib/annotation/fixtures/dtag_mn09_203a.json).
  2. Heavy per-sample arrays to the box directory (gitignored), with a manifest
     pointer. Never commits raw telemetry or large derivatives.

No R / animaltags / plotly runtime is used. Run:

    python3 -m infra.tagtools.bake            # from repo root
    python3 infra/tagtools/bake.py            # direct
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

# Allow `python3 infra/tagtools/bake.py` (direct) as well as `-m`.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from infra.tagtools.pipeline.descriptors import step_descriptors  # noqa: E402
from infra.tagtools.pipeline.io import (  # noqa: E402
    ATTRIBUTION,
    DEFAULT_SOURCE_ROOT,
    ExpertAnnotation,
    LICENSE,
    LICENSE_STATUS,
    SOURCE_POINTER,
    SensorData,
    load_source_bundle,
)
from infra.tagtools.pipeline.steps import PIPELINE_STEPS, StepResult  # noqa: E402

_OUT_DIR = Path(__file__).resolve().parent / "out"
_BOX_DIR = _OUT_DIR / "box"
_WEB_FIXTURE = _REPO_ROOT / "web" / "lib" / "annotation" / "fixtures" / "dtag_mn09_203a.json"

BEHAVIOR_MAPPING_REL = "behavior_mapping.json"
_DOWNSAMPLE_POINTS = 2000


def _load_behavior_mapping(source_root: str) -> Dict[str, str]:
    path = Path(source_root) / BEHAVIOR_MAPPING_REL
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def _downsample(arr: np.ndarray, n: int) -> List[float]:
    if arr.size <= n:
        return [round(float(v), 4) for v in arr]
    idx = np.linspace(0, arr.size - 1, n).astype(int)
    return [round(float(v), 4) for v in arr[idx]]


def _dominant_behavior(
    start: int, end: int, annotations: List[ExpertAnnotation]
) -> str | None:
    """Real classified behavior for a dive window: the expert event with the
    largest sample overlap. No fabrication; returns None if no overlap."""
    best = None
    best_overlap = 0
    for ann in annotations:
        overlap = max(0, min(end, ann.event_end) - max(start, ann.event_start))
        if overlap > best_overlap:
            best_overlap = overlap
            best = ann.event
    return best


def run_steps(sensor: SensorData) -> Dict[str, StepResult]:
    return {step_id: fn(sensor) for step_id, fn in PIPELINE_STEPS.items()}


def build_fixture(source_root: str) -> Dict[str, Any]:
    bundle = load_source_bundle(source_root)
    sensor = bundle.sensor
    results = run_steps(sensor)
    behavior_mapping = _load_behavior_mapping(source_root)

    dive_step = results["tagtools.dive_detection"]
    dive_indices = dive_step.heavy["dive_indices"]
    max_depths = dive_step.heavy["max_depths"]
    durations = dive_step.heavy["durations"]
    depth = sensor.depth_m

    dives: List[Dict[str, Any]] = []
    for i, (start, max_idx, end) in enumerate(dive_indices.tolist()):
        dives.append(
            {
                "dive_id": i + 1,
                "start_sample": int(start),
                "max_depth_sample": int(max_idx),
                "end_sample": int(end),
                "max_depth_m": round(float(max_depths[i]), 3),
                "duration_s": round(float(durations[i]), 2),
                "classified_behavior": _dominant_behavior(
                    int(start), int(end), bundle.annotations
                ),
            }
        )

    fixture: Dict[str, Any] = {
        "schema_version": "1.0.0",
        "meta": {
            "deployment_id": sensor.deployment_id,
            "species": "humpback (Megaptera novaeangliae)",
            "role": "contrast/reference only; never drives an orca",
            "sample_rate_hz": sensor.sample_rate_hz,
            "n_samples": sensor.n_samples,
            "duration_s": round(sensor.n_samples / sensor.sample_rate_hz, 1),
        },
        "behavior_taxonomy": behavior_mapping,
        "expert_annotations": [
            {
                "whale_id": a.whale_id,
                "sample_hz": a.sample_hz,
                "event_start": a.event_start,
                "event_end": a.event_end,
                "state": a.state,
                "event": a.event,
            }
            for a in bundle.annotations
        ],
        "tagtools_steps": [
            {
                "step_id": r.step_id,
                "title": r.title,
                "truth_label": r.truth_label,
                "reproduces_h5_path": r.reproduces_h5_path,
                "summary": r.summary,
                "provenance": r.provenance,
            }
            for r in results.values()
        ],
        "step_descriptors": step_descriptors(),
        "dives": dives,
        "depth_profile_downsampled_m": _downsample(depth, _DOWNSAMPLE_POINTS),
        "odba_profile_downsampled_g": _downsample(
            results["tagtools.odba"].heavy["odba"], _DOWNSAMPLE_POINTS
        ),
        "provenance": bundle.provenance,
        "license": LICENSE,
        "license_status": LICENSE_STATUS,
        "attribution": ATTRIBUTION,
        "source": SOURCE_POINTER,
        "privacy_note": "No human PII. whaleName dropped from fixture; only whaleID retained for provenance.",
    }
    return fixture, results


def write_box(results: Dict[str, StepResult]) -> List[str]:
    _BOX_DIR.mkdir(parents=True, exist_ok=True)
    written: List[str] = []
    for step_id, r in results.items():
        if not r.heavy:
            continue
        path = _BOX_DIR / f"{step_id.replace('.', '_')}.npz"
        np.savez_compressed(path, **r.heavy)
        written.append(str(path))
    return written


def main() -> int:
    source_root = os.environ.get("BSS_DTAG_SOURCE_ROOT", DEFAULT_SOURCE_ROOT)
    print(f"[bake] source_root = {source_root}")
    fixture, results = build_fixture(source_root)

    _WEB_FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    _WEB_FIXTURE.write_text(json.dumps(fixture, indent=2), encoding="utf-8")
    print(f"[bake] wrote web fixture: {_WEB_FIXTURE} ({_WEB_FIXTURE.stat().st_size} bytes)")

    boxed = write_box(results)
    for p in boxed:
        print(f"[bake] boxed heavy array: {p}")

    print("[bake] step summaries:")
    for r in results.values():
        print(f"  - {r.step_id}: {json.dumps(r.summary)}")
    print(f"[bake] dives detected: {len(fixture['dives'])}; "
          f"expert annotations: {len(fixture['expert_annotations'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

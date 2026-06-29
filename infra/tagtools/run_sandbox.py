#!/usr/bin/env python3
"""Sandbox verification for the tagtools studio (BSS-BUILD gate).

Runs one or more pipeline stages over the REAL DTAG sensor data and asserts the
outputs are well-formed. This is the "a tagtools step actually runs in a
sandbox" evidence for the BSS-BUILD gate. No console, no R runtime.

Usage:
    python3 infra/tagtools/run_sandbox.py                 # run all stages
    python3 infra/tagtools/run_sandbox.py tagtools.odba   # run one stage
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from infra.tagtools.pipeline.io import DEFAULT_SOURCE_ROOT, load_sensor_csv  # noqa: E402
from infra.tagtools.pipeline.steps import PIPELINE_STEPS  # noqa: E402


def main(argv: list[str]) -> int:
    source_root = os.environ.get("BSS_DTAG_SOURCE_ROOT", DEFAULT_SOURCE_ROOT)
    requested = argv[1:] or list(PIPELINE_STEPS.keys())

    sensor = load_sensor_csv(source_root)
    print(f"[sandbox] loaded {sensor.n_samples} samples @ {sensor.sample_rate_hz} Hz "
          f"from {sensor.source_path}")

    failures = 0
    for step_id in requested:
        fn = PIPELINE_STEPS.get(step_id)
        if fn is None:
            print(f"[sandbox] FAIL unknown step: {step_id}")
            failures += 1
            continue
        result = fn(sensor)
        ok = bool(result.summary) and all(
            v is not None for v in result.summary.values()
        )
        status = "PASS" if ok else "FAIL"
        if not ok:
            failures += 1
        print(f"[sandbox] {status} {step_id}: {json.dumps(result.summary)}")

    if failures:
        print(f"[sandbox] {failures} step(s) failed")
        return 1
    print(f"[sandbox] all {len(requested)} step(s) passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

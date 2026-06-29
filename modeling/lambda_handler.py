"""AWS Lambda entrypoint for the kernel-fit stage of the orchestrator.

Packaged as a container image (``tools/deployment/aws/Dockerfile.fit``) because
the fit needs scipy/statsmodels, which are deliberately not in the App Runner
image. Invoked by the Step Functions ``FitAndGate`` state. Reads the S3
time-series store, fits + gates the kernels, uploads ``fitted_kernels.json`` and
``fit_report.json`` to the models bucket, and returns a compact summary the
state machine routes on.
"""

from __future__ import annotations

import os
from typing import Any, Dict


def handler(event: Dict[str, Any] | None, context: Any = None) -> Dict[str, Any]:
    # Force aws mode + a writable output dir before importing the fitter
    # (output paths are resolved at import time).
    os.environ.setdefault("ORCAST_STORAGE_BACKEND", "aws")
    os.environ.setdefault("ORCAST_FIT_OUTPUT_DIR", "/tmp/orcast_fit")

    from src.aws_backend.config import settings
    from src.aws_backend.timeseries import build_timeseries_store
    from modeling.fit_kernels import freeze_dataset_snapshot, run_fit

    bin_hours = float((event or {}).get("bin_hours", 1.0))
    store = build_timeseries_store(settings)

    if (event or {}).get("mode") == "freeze_snapshot":
        manifest = freeze_dataset_snapshot(store, bin_hours=bin_hours, write_outputs=True)
        return {
            "status": "frozen",
            "dataset_snapshot_id": manifest["snap_id"],
            "fit_plan_id": manifest.get("fit_plan_id"),
            "stream_count": len(manifest.get("streams", [])),
        }

    report = run_fit(
        store,
        bin_hours=bin_hours,
        write_outputs=True,
        make_figures=False,
        dataset_snapshot_id=(event or {}).get("dataset_snapshot_id"),
    )

    return {
        "status": report.get("status"),
        "confidence": report.get("confidence", 0.0),
        "fit_plan_id": report.get("fit_plan_id"),
        "dataset_snapshot_id": report.get("dataset_snapshot_id"),
        "n_detections": report.get("n_detections"),
        "gates_summary": {
            "cv_gate_pass": (report.get("cv") or {}).get("gate_pass"),
            "time_rescaling_pass": (report.get("time_rescaling") or {}).get("pooled_pass_exp"),
            "pit_calibrated": (report.get("pit") or {}).get("calibrated"),
            "level1_psth": report.get("level1_psth"),
            "mcfadden_r2": (report.get("metrics") or {}).get("mcfadden_r2"),
        },
    }

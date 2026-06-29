from unittest.mock import MagicMock

from modeling import lambda_handler


def test_lambda_handler_freeze_snapshot_mode(monkeypatch):
    manifest = {"snap_id": "snap_test", "fit_plan_id": "fitplan_test", "streams": []}

    monkeypatch.setattr("src.aws_backend.timeseries.build_timeseries_store", lambda _cfg: MagicMock())
    monkeypatch.setattr(
        "modeling.fit_kernels.freeze_dataset_snapshot",
        lambda store, bin_hours=1.0, write_outputs=True: manifest,
    )

    out = lambda_handler.handler({"mode": "freeze_snapshot", "bin_hours": 1.0})
    assert out["status"] == "frozen"
    assert out["dataset_snapshot_id"] == "snap_test"


def test_lambda_handler_fit_accepts_dataset_snapshot_id(monkeypatch):
    report = {"status": "fitted", "confidence": 0.5, "dataset_snapshot_id": "snap_abc", "n_detections": 3}

    monkeypatch.setattr("src.aws_backend.timeseries.build_timeseries_store", lambda _cfg: MagicMock())
    captured = {}

    def _run_fit(store, **kwargs):
        captured.update(kwargs)
        return report

    monkeypatch.setattr("modeling.fit_kernels.run_fit", _run_fit)
    out = lambda_handler.handler({"bin_hours": 1.0, "dataset_snapshot_id": "snap_abc"})
    assert captured.get("dataset_snapshot_id") == "snap_abc"
    assert out["dataset_snapshot_id"] == "snap_abc"

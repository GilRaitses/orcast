"""Tests for the corridor future-departure ETA model (fixtures only, no live calls).

Bucketing is exercised in UTC (``tz="UTC"`` + naive depart times read as UTC) so the
assertions are deterministic regardless of the host's tz database.
"""

import json
from datetime import datetime

import pytest

from modeling.traffic.corridor import predict_eta

ROUTE = 101
OTHER_ROUTE = 999


def _write_history(path, rows):
    with open(path, "w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")


@pytest.fixture()
def history_file(tmp_path):
    """A small synthetic corridor log: a populated Monday 08:00 bin + a later reading."""
    path = tmp_path / "seatac_anacortes.jsonl"
    rows = [
        # Monday 2026-06-15, 08:00-09:00 UTC bin: four measured readings, median 43.
        {"travel_time_id": ROUTE, "name": "SeaTac-Seattle",
         "current_time": 40, "time_updated": "2026-06-15T08:00:00+00:00"},
        {"travel_time_id": ROUTE, "name": "SeaTac-Seattle",
         "current_time": 44, "time_updated": "2026-06-15T08:10:00+00:00"},
        {"travel_time_id": ROUTE, "name": "SeaTac-Seattle",
         "current_time": 42, "time_updated": "2026-06-15T08:20:00+00:00"},
        {"travel_time_id": ROUTE, "name": "SeaTac-Seattle",
         "current_time": 46, "time_updated": "2026-06-15T08:30:00+00:00"},
        # Latest measured reading overall (Wed 17:00), a different bin: current_time 60.
        {"travel_time_id": ROUTE, "name": "SeaTac-Seattle",
         "current_time": 60, "time_updated": "2026-06-17T17:00:00+00:00"},
        # A noise row for a different route that must never leak into ROUTE's model.
        {"travel_time_id": OTHER_ROUTE, "name": "Seattle-Everett",
         "current_time": 999, "time_updated": "2026-06-15T08:05:00+00:00"},
    ]
    _write_history(path, rows)
    return path


def test_modeled_history_bin_returns_labeled_eta_and_interval(history_file):
    # Depart Monday 08:45 UTC -> same Mon/08:00 bin as the four readings.
    result = predict_eta(
        ROUTE, datetime(2026, 6, 15, 8, 45), history_path=history_file, tz="UTC"
    )

    assert result["label"] == "MODELED"
    assert result["basis"]["method"] == "modeled_history"
    assert result["basis"]["n_samples"] == 4
    assert result["basis"]["day_of_week"] == "Mon"
    assert result["basis"]["time_bin"] == "08:00-09:00"

    # Median of [40, 42, 44, 46] is 43; the noise route (999) is excluded.
    assert result["eta_minutes"] == 43.0

    interval = result["interval"]
    assert interval is not None
    assert interval["low_minutes"] <= result["eta_minutes"] <= interval["high_minutes"]
    assert interval["low_minutes"] < interval["high_minutes"]


def test_empty_bin_falls_back_to_latest_measured(history_file):
    # Depart Monday 03:00 UTC -> the 03:00 bin is empty for this route.
    result = predict_eta(
        ROUTE, datetime(2026, 6, 15, 3, 0), history_path=history_file, tz="UTC"
    )

    assert result["label"] == "MODELED"
    assert result["basis"]["method"] == "fallback_latest_measured"
    assert result["basis"]["n_samples"] == 0
    assert result["basis"]["fallback_from_total_samples"] == 5
    # The latest measured reading (Wed 17:00) is 60 minutes.
    assert result["eta_minutes"] == 60.0
    assert result["basis"]["measured_at"].startswith("2026-06-17T17:00:00")
    assert result["interval"] is not None


def test_no_history_for_route_returns_unknown(history_file):
    result = predict_eta(
        12345, datetime(2026, 6, 15, 8, 45), history_path=history_file, tz="UTC"
    )

    assert result["label"] == "MODELED"
    assert result["basis"]["method"] == "no_history"
    assert result["basis"]["n_samples"] == 0
    assert result["eta_minutes"] is None
    assert result["interval"] is None


def test_missing_history_file_is_graceful(tmp_path):
    missing = tmp_path / "does_not_exist.jsonl"
    result = predict_eta(
        ROUTE, datetime(2026, 6, 15, 8, 45), history_path=missing, tz="UTC"
    )

    assert result["eta_minutes"] is None
    assert result["basis"]["method"] == "no_history"


def test_aware_depart_dt_is_converted_into_bucket_tz(history_file):
    # 15:45 UTC == 08:45 America/Los_Angeles (PDT, UTC-7) -> the 08:00 Mon bin.
    aware = datetime.fromisoformat("2026-06-15T15:45:00+00:00")
    result = predict_eta(
        ROUTE, aware, history_path=history_file, tz="America/Los_Angeles"
    )

    # History stamps are UTC; bucketed in Pacific the 08:00 UTC readings move to
    # 01:00 Pacific, so the Pacific 08:45 bin is empty -> graceful fallback, not a
    # crash. The point of this test is the aware->tz conversion path runs cleanly.
    assert result["label"] == "MODELED"
    assert result["basis"]["day_of_week"] == "Mon"
    assert result["basis"]["time_bin"] == "08:00-09:00"

import json

import pytest

from src.aws_backend.sources.bathymetry import BathymetryAdapter


@pytest.fixture
def fixture_asset(tmp_path):
    """A tiny 3-point bathymetry grid asset for offline tests (no network)."""
    asset = {
        "source": "fixture://etopo180",
        "dataset": "test fixture",
        "bounds": {"min_lat": 48.40, "max_lat": 48.70, "min_lng": -123.25, "max_lng": -122.75},
        "resolution_deg": 0.0166667,
        "points": [
            {"lat": 48.45, "lng": -123.20, "depth_m": -120.0},
            {"lat": 48.55, "lng": -123.00, "depth_m": -40.0},
            {"lat": 48.65, "lng": -122.80, "depth_m": 35.0},  # island land (positive)
        ],
    }
    path = tmp_path / "san_juan_bathymetry.json"
    path.write_text(json.dumps(asset), encoding="utf-8")
    return path


def test_load_reads_points(fixture_asset):
    adapter = BathymetryAdapter(asset_path=fixture_asset)
    points = adapter.load()
    assert len(points) == 3
    assert all({"lat", "lng", "depth_m"} <= set(p) for p in points)


def test_depth_at_returns_nearest_point(fixture_asset):
    adapter = BathymetryAdapter(asset_path=fixture_asset)
    # Query very close to the first grid point -> its depth.
    assert adapter.depth_at(48.451, -123.201) == -120.0
    # Query close to the second grid point -> its depth.
    assert adapter.depth_at(48.549, -123.005) == -40.0
    # Closest to the land point -> positive elevation.
    assert adapter.depth_at(48.66, -122.79) == 35.0


def test_depth_at_in_water_is_negative(fixture_asset):
    adapter = BathymetryAdapter(asset_path=fixture_asset)
    depth = adapter.depth_at(48.45, -123.20)
    assert depth is not None and depth < 0


def test_depth_at_nonfinite_returns_none(fixture_asset):
    adapter = BathymetryAdapter(asset_path=fixture_asset)
    assert adapter.depth_at(float("nan"), -123.0) is None


def test_missing_asset_degrades(tmp_path):
    adapter = BathymetryAdapter(asset_path=tmp_path / "does_not_exist.json")
    assert adapter.load() == []
    assert adapter.depth_at(48.55, -123.00) is None
    summary = adapter.summary()
    assert summary["point_count"] == 0
    assert summary["min_depth_m"] is None
    assert summary["max_depth_m"] is None


def test_summary_reports_counts_and_extent(fixture_asset):
    adapter = BathymetryAdapter(asset_path=fixture_asset)
    summary = adapter.summary()
    assert summary["point_count"] == 3
    assert summary["min_depth_m"] == -120.0
    assert summary["max_depth_m"] == 35.0
    assert summary["source"] == "fixture://etopo180"
    assert summary["bounds"]["min_lat"] == 48.40


def test_committed_asset_is_real_bathymetry():
    """The committed asset should load and hold real, mostly-negative depths."""
    adapter = BathymetryAdapter()
    points = adapter.load()
    assert len(points) > 0
    depths = [p["depth_m"] for p in points]
    # Real relief: water dominates this bbox, so most points are below sea level.
    assert sum(1 for d in depths if d < 0) > len(depths) // 2
    summary = adapter.summary()
    assert summary["min_depth_m"] < 0
    assert summary["point_count"] == len(points)

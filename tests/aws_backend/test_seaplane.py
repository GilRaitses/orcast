"""Tests for the Kenmore Air seaplane static table (src/aws_backend/sources/seaplane.py).

No network exists in this module — it is a curated PUBLISHED snapshot. These
tests assert the table is returned, labeled published (never live), filterable by
route + operating day, and that an out-of-season / non-operating day yields an
empty list ("unknown"), never a fabricated departure.
"""

import datetime

from src.aws_backend.sources import seaplane


def test_returns_published_table():
    rows = seaplane.seaplane_schedule()
    assert rows, "expected a non-empty published seaplane table"
    for row in rows:
        assert row["label"] == "published"
        assert row["realtime"] is False
        assert row["carrier"] == "Kenmore Air"
        assert row["source_date"] == seaplane.SOURCE_DATE
        assert "Kenmore Air" in row["source"]
        # Published columns from the recon doc are all present.
        for col in (
            "route",
            "origin",
            "destination",
            "departure_time",
            "arrival_time",
            "days_of_operation",
            "season",
            "terminal",
            "dock",
        ):
            assert col in row


def test_friday_harbor_route_present():
    rows = seaplane.seaplane_schedule()
    fh = [r for r in rows if "Friday Harbor" in r["route"]]
    assert fh, "Lake Union <-> Friday Harbor must be in the published table"
    out = next(r for r in fh if r["origin"] == seaplane._LAKE_UNION)
    assert out["destination"] == "Friday Harbor Seaplane Base"
    assert out["departure_time"] == "09:00"
    assert out["duration_min"] == 45


def test_route_filter_is_case_insensitive_substring():
    orcas = seaplane.seaplane_schedule(route="orcas")
    assert orcas, "substring filter should match West Sound / Rosario (Orcas)"
    for row in orcas:
        haystack = (row["route"] + row["origin"] + row["destination"]).lower()
        assert "orcas" in haystack

    # An unknown route returns empty (never raises).
    assert seaplane.seaplane_schedule(route="Honolulu") == []


def test_day_filter_keeps_operating_in_season_days():
    # Friday, 2026-06-26 is inside the summer window; daily routes operate.
    friday = datetime.date(2026, 6, 26)
    assert friday.weekday() == 4
    rows = seaplane.seaplane_schedule(route="Friday Harbor", day=friday)
    assert rows, "daily Friday Harbor service should operate on an in-season Friday"


def test_day_filter_excludes_non_operating_weekday():
    # Lopez Island only runs Fri/Sat/Sun; a Monday must yield nothing.
    monday = datetime.date(2026, 6, 29)
    assert monday.weekday() == 0
    assert seaplane.seaplane_schedule(route="Lopez", day=monday) == []


def test_day_filter_excludes_out_of_season():
    # January is outside the published summer window -> empty (unknown), not faked.
    winter = datetime.date(2026, 1, 15)
    assert seaplane.seaplane_schedule(route="Friday Harbor", day=winter) == []


def test_returned_rows_are_copies():
    rows = seaplane.seaplane_schedule()
    rows[0]["route"] = "MUTATED"
    fresh = seaplane.seaplane_schedule()
    assert all(r["route"] != "MUTATED" for r in fresh)


def test_source_stamp():
    stamp = seaplane.source_stamp()
    assert stamp["label"] == "published"
    assert stamp["source_date"] == seaplane.SOURCE_DATE
    assert "Kenmore Air" in stamp["source"]

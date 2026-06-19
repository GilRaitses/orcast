from datetime import date

import pytest

from src.aws_backend.sources.salmon import SalmonRunAdapter


class _JsonResponse:
    status_code = 200
    headers = {"content-type": "application/json"}

    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload


def _all_run_indices_valid(series):
    return all(0.0 <= rec["run_index"] <= 1.0 for rec in series)


def test_climatology_fallback_when_live_sources_fail(monkeypatch):
    def boom(*_args, **_kwargs):
        raise RuntimeError("network down")

    monkeypatch.setattr("src.aws_backend.sources.salmon.requests.get", boom)

    series = SalmonRunAdapter().fetch_run_index(2024)

    assert series, "fallback must return a non-empty daily series"
    assert all(rec["source"] == "climatology_fallback" for rec in series)
    assert _all_run_indices_valid(series)

    # Peak run timing must fall in July-August (Fraser summer Chinook).
    peak = max(series, key=lambda rec: rec["run_index"])
    peak_month = date.fromisoformat(peak["t"]).month
    assert peak_month in (7, 8), f"expected July/August peak, got month {peak_month}"
    assert peak["run_index"] == pytest.approx(1.0)


def test_climatology_fallback_on_non_200(monkeypatch):
    class _ServerError:
        status_code = 500
        headers = {"content-type": "text/html"}

        def json(self):
            raise ValueError("no json")

    monkeypatch.setattr(
        "src.aws_backend.sources.salmon.requests.get",
        lambda *a, **k: _ServerError(),
    )

    series = SalmonRunAdapter().fetch_run_index(2024)

    assert series
    assert all(rec["source"] == "climatology_fallback" for rec in series)
    assert _all_run_indices_valid(series)


def test_live_albion_payload_is_used_and_normalized(monkeypatch):
    payload = {
        "data": [
            {"date": "2024-07-01", "cpue": 2.0},
            {"date": "2024-07-10", "cpue": 8.0},
            {"date": "2024-07-20", "cpue": 20.0},  # season peak
            {"date": "2024-08-01", "cpue": 6.0},
            {"date": "2024-08-15", "cpue": 1.0},
        ]
    }

    def fake_get(url, *_args, **_kwargs):
        return _JsonResponse(payload)

    monkeypatch.setattr("src.aws_backend.sources.salmon.requests.get", fake_get)

    series = SalmonRunAdapter().fetch_run_index(2024)

    assert series
    assert all(rec["source"] == "albion" for rec in series)
    assert all(rec["source"] != "climatology_fallback" for rec in series)
    assert _all_run_indices_valid(series)

    # Normalized within season: peak -> 1.0, trough -> 0.0.
    by_date = {rec["t"]: rec for rec in series}
    assert by_date["2024-07-20"]["run_index"] == pytest.approx(1.0)
    assert by_date["2024-08-15"]["run_index"] == pytest.approx(0.0)
    # Fraser preferred; columbia absent on this path.
    assert by_date["2024-07-20"]["fraser_index"] == pytest.approx(1.0)
    assert all(rec["columbia_index"] is None for rec in series)


def test_columbia_fallback_when_fraser_empty(monkeypatch):
    # First call (Fraser) returns an empty/unparseable payload, second call
    # (Columbia/DART) returns usable passage counts.
    calls = {"n": 0}

    def fake_get(url, *_args, **_kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            return _JsonResponse({"data": []})
        return _JsonResponse(
            {
                "data": [
                    {"date": "2024-07-05", "count": 1000},
                    {"date": "2024-07-25", "count": 5000},
                    {"date": "2024-08-20", "count": 500},
                ]
            }
        )

    monkeypatch.setattr("src.aws_backend.sources.salmon.requests.get", fake_get)

    series = SalmonRunAdapter().fetch_run_index(2024)

    assert series
    assert all(rec["source"] == "dart" for rec in series)
    assert _all_run_indices_valid(series)
    by_date = {rec["t"]: rec for rec in series}
    assert by_date["2024-07-25"]["run_index"] == pytest.approx(1.0)
    # Columbia path: run_index falls back to columbia_index, fraser absent.
    assert by_date["2024-07-25"]["columbia_index"] == pytest.approx(1.0)
    assert all(rec["fraser_index"] is None for rec in series)


def test_run_index_always_within_unit_interval(monkeypatch):
    monkeypatch.setattr(
        "src.aws_backend.sources.salmon.requests.get",
        lambda *a, **k: (_ for _ in ()).throw(ConnectionError("offline")),
    )

    for year in (2019, 2024, 2025):
        series = SalmonRunAdapter().fetch_run_index(year)
        assert series
        assert _all_run_indices_valid(series)

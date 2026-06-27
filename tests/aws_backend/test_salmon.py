from datetime import date

import pytest

from src.aws_backend.sources import salmon as salmon_mod
from src.aws_backend.sources.salmon import SalmonRunAdapter


class _JsonResponse:
    status_code = 200
    headers = {"content-type": "application/json"}

    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload


class _CsvResponse:
    """A DART-style CSV HTTP response (content-type csv, ``.text`` body)."""

    status_code = 200
    headers = {"content-type": "text/csv"}

    def __init__(self, text):
        self.text = text

    def json(self):  # pragma: no cover - DART path reads .text, not .json()
        raise ValueError("csv response has no json")


def _all_run_indices_valid(series):
    return all(0.0 <= rec["run_index"] <= 1.0 for rec in series)


@pytest.fixture
def empty_albion_cache(monkeypatch, tmp_path):
    """Point the Albion FOS cache at an empty dir so _fetch_fraser returns {}.

    The real adapter reads the stock-aligned Fraser signal from cached FOS CSVs
    (data/salmon/albion_fos/fosYYYY.csv), not from requests.get. To exercise the
    DART/climatology fallback paths a test must make that cache empty.
    """
    monkeypatch.setattr(salmon_mod, "_ALBION_FOS_CACHE_DIR", tmp_path)
    return tmp_path


def test_climatology_fallback_when_live_sources_fail(empty_albion_cache, monkeypatch):
    def boom(*_args, **_kwargs):
        raise RuntimeError("network down")

    # Albion cache empty (fixture) + DART (requests.get) down -> climatology.
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


def test_climatology_fallback_on_non_200(empty_albion_cache, monkeypatch):
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


def test_cached_albion_is_used_and_normalized(empty_albion_cache, monkeypatch):
    # The real Fraser signal is the cached FOS CSV. Write a controlled one
    # (provenance columns day,mon,year,...,cpue1,...) and assert it is read,
    # normalized within season, and preferred over Columbia.
    (empty_albion_cache / "fos2024.csv").write_text(
        "day,mon,year,netlen,catch1,sets1,effort1,cpue1,catch2,sets2,effort2,cpue2\n"
        "1,Jul,2024,91,2,1,1,2.0,0,0,0,0\n"
        "10,Jul,2024,91,8,1,1,8.0,0,0,0,0\n"
        "20,Jul,2024,91,20,1,1,20.0,0,0,0,0\n"  # season peak
        "1,Aug,2024,91,6,1,1,6.0,0,0,0,0\n"
        "15,Aug,2024,91,1,1,1,1.0,0,0,0,0\n",  # season trough
        encoding="utf-8",
    )

    # Even if a network feed were reachable, the cached Fraser signal wins.
    def boom(*_args, **_kwargs):
        raise RuntimeError("network must not be hit on the Albion path")

    monkeypatch.setattr("src.aws_backend.sources.salmon.requests.get", boom)

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


def test_columbia_fallback_when_fraser_empty(empty_albion_cache, monkeypatch):
    # Albion cache empty (fixture) -> Fraser returns {}. DART returns a real CSV
    # (the adapter parses CSV, not JSON; the adult-Chinook column is "Chin").
    dart_csv = "Date,Chin\n2024-07-05,1000\n2024-07-25,5000\n2024-08-20,500\n"

    monkeypatch.setattr(
        "src.aws_backend.sources.salmon.requests.get",
        lambda *a, **k: _CsvResponse(dart_csv),
    )

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
    # With the real cache present, cached years return the Fraser signal even
    # when the network is down; uncached years fall through to climatology.
    monkeypatch.setattr(
        "src.aws_backend.sources.salmon.requests.get",
        lambda *a, **k: (_ for _ in ()).throw(ConnectionError("offline")),
    )

    for year in (2019, 2024, 2025):
        series = SalmonRunAdapter().fetch_run_index(year)
        assert series
        assert _all_run_indices_valid(series)

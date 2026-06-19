from datetime import date

from src.aws_backend.sources.orcahello import OrcaHelloAdapter
from src.aws_backend.sources.inaturalist import INaturalistAdapter
from src.aws_backend.sources.noaa import NoaaAdapter
from src.aws_backend.sources.base import SourceFetchResult


class _HtmlResponse:
    status_code = 200
    headers = {"content-type": "text/html; charset=utf-8"}
    text = "<html>not detections</html>"


class _JsonArrayResponse:
    status_code = 200
    headers = {"content-type": "application/json; charset=utf-8"}

    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload


# A trimmed real OrcaHello detection (top-level array, hydrophone in-region).
_SAMPLE_DETECTIONS = [
    {
        "id": "9bb69d69-bbd7-4079-bbd7-6593cbb47943",
        "audioUri": "https://example.blob/audiowavs/orcasound_lab.wav",
        "spectrogramUri": "https://example.blob/spectrogramspng/orcasound_lab.png",
        "location": {"name": "Orcasound Lab", "longitude": -123.1726, "latitude": 48.5583},
        "timestamp": "2026-06-19T17:46:52Z",
        "reviewed": False,
        "found": "No",
        "confidence": 76.77,
    },
    {
        "id": "confirmed-1",
        "audioUri": "https://example.blob/audiowavs/haro.wav",
        "location": {"name": "Haro Strait", "longitude": -123.20, "latitude": 48.55},
        "timestamp": "2026-06-19T16:00:00Z",
        "reviewed": True,
        "found": "Yes",
        "confidence": 92.0,
    },
    {
        # Out-of-region hydrophone (Port Townsend) must be dropped.
        "id": "out-of-region",
        "location": {"name": "Port Townsend", "longitude": -122.7606, "latitude": 48.1357},
        "timestamp": "2026-06-19T15:00:00Z",
        "reviewed": False,
        "found": "No",
        "confidence": 50.0,
    },
]


def test_orcahello_rejects_non_json_response(monkeypatch):
    def fake_get(*_args, **_kwargs):
        return _HtmlResponse()

    monkeypatch.setattr("src.aws_backend.sources.orcahello.requests.get", fake_get)

    result = OrcaHelloAdapter().fetch()

    assert result.available is False
    assert result.content_type == "text/html; charset=utf-8"
    assert "non-JSON" in result.error


def test_orcahello_uses_detections_api_host_and_path(monkeypatch):
    captured = {}

    def fake_get(url, *_args, **kwargs):
        captured["url"] = url
        captured["params"] = kwargs.get("params")
        return _JsonArrayResponse(_SAMPLE_DETECTIONS)

    monkeypatch.setattr("src.aws_backend.sources.orcahello.requests.get", fake_get)

    adapter = OrcaHelloAdapter()
    result = adapter.fetch()

    assert result.available is True
    assert captured["url"] == "https://aifororcasdetections.azurewebsites.net/api/detections"
    assert captured["params"]["SortBy"] == "timestamp"
    assert isinstance(result.raw, list)


def test_orcahello_confirmed_endpoint(monkeypatch):
    captured = {}

    def fake_get(url, *_args, **kwargs):
        captured["url"] = url
        return _JsonArrayResponse([])

    monkeypatch.setattr("src.aws_backend.sources.orcahello.requests.get", fake_get)

    OrcaHelloAdapter(confirmed_only=True).fetch()
    assert captured["url"].endswith("/api/detections/confirmed")


def test_orcahello_normalizes_top_level_array():
    result = SourceFetchResult(source="orcahello", available=True, raw=_SAMPLE_DETECTIONS)

    sightings = OrcaHelloAdapter().normalize(result)

    # The out-of-region Port Townsend record is dropped.
    assert len(sightings) == 2
    assert result.skipped_count == 1

    by_id = {s.source_id: s for s in sightings}
    candidate = by_id["9bb69d69-bbd7-4079-bbd7-6593cbb47943"]
    assert candidate.source == "orcahello"
    assert 0.0 <= candidate.confidence <= 1.0
    assert abs(candidate.confidence - 0.7677) < 1e-6
    # Coordinates come from location.* (the hydrophone position).
    assert candidate.latitude == 48.5583
    assert candidate.longitude == -123.1726
    assert candidate.location_name == "Orcasound Lab"
    assert candidate.evidence[0].quality_grade == "unreviewed_acoustic_candidate"

    confirmed = by_id["confirmed-1"]
    assert confirmed.evidence[0].quality_grade == "confirmed_acoustic_detection"


_SAMPLE_WATER_LEVEL = {
    "metadata": {"id": "9449880", "name": "Friday Harbor"},
    "data": [
        {"t": "2024-06-01 00:00", "v": "1.304", "s": "0.005", "f": "0,0,0,0"},
        {"t": "2024-06-01 00:06", "v": "1.286", "s": "0.004", "f": "0,0,0,0"},
        {"t": "2024-06-01 00:12", "v": "", "s": "", "f": "1,0,0,0"},
    ],
}


class _NoaaJsonResponse:
    status_code = 200
    headers = {"content-type": "application/json"}

    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload


def test_fetch_water_level_history_normalizes_rows(monkeypatch):
    captured = {}

    def fake_get(url, *_args, **kwargs):
        captured["url"] = url
        captured["params"] = kwargs.get("params")
        return _NoaaJsonResponse(_SAMPLE_WATER_LEVEL)

    monkeypatch.setattr("src.aws_backend.sources.noaa.requests.get", fake_get)

    series = NoaaAdapter().fetch_water_level_history(
        begin=date(2024, 6, 1), end=date(2024, 6, 2)
    )

    # Blank-value row is skipped; the two valid rows are normalized.
    assert len(series) == 2
    first = series[0]
    assert set(first) == {"t", "value", "station", "product"}
    assert first["product"] == "water_level"
    assert first["station"] == "9449880"
    assert isinstance(first["value"], float)
    assert first["value"] == 1.304
    assert first["t"].startswith("2024-06-01T00:00:00")
    # Date formatting follows NOAA's YYYYMMDD convention.
    assert captured["params"]["begin_date"] == "20240601"
    assert captured["params"]["product"] == "water_level"


def test_fetch_water_level_history_chunks_long_ranges(monkeypatch):
    calls = []

    def fake_get(url, *_args, **kwargs):
        calls.append(kwargs.get("params"))
        return _NoaaJsonResponse({"data": []})

    monkeypatch.setattr("src.aws_backend.sources.noaa.requests.get", fake_get)

    # A 90-day range must be split into multiple <=31-day requests.
    NoaaAdapter().fetch_water_level_history(
        begin=date(2024, 1, 1), end=date(2024, 3, 31)
    )

    assert len(calls) > 1


def test_fetch_currents_history_error_returns_empty(monkeypatch):
    import requests

    def fake_get(*_args, **_kwargs):
        raise requests.RequestException("currents unavailable")

    monkeypatch.setattr("src.aws_backend.sources.noaa.requests.get", fake_get)

    series = NoaaAdapter().fetch_currents_history(
        begin=date(2024, 6, 1), end=date(2024, 6, 2), station="PUG1515"
    )

    assert series == []


def test_inaturalist_allows_missing_species_guess():
    result = SourceFetchResult(
        source="inaturalist",
        available=True,
        raw={
            "results": [
                {
                    "id": 123,
                    "location": "48.5,-123.1",
                    "time_observed_at": "2026-06-12T12:36:00Z",
                    "species_guess": None,
                    "quality_grade": "research",
                    "photos": [],
                    "user": {"login": "observer"},
                    "uri": "https://www.inaturalist.org/observations/123",
                }
            ]
        },
    )

    sightings = INaturalistAdapter().normalize(result)

    assert len(sightings) == 1
    assert sightings[0].common_name == "Killer Whale"


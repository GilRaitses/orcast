from unittest import mock

from src.aws_backend.sources.orcahello_history import OrcaHelloHistoryAdapter


# Page 1: one in-region hydrophone (near 48.55, -123.06) and one out-of-region
# hydrophone (near 47.34, -122.32, well south of the San Juan box).
_PAGE_1 = [
    {
        "id": "in-region-1",
        "audioUri": "https://example.blob/audiowavs/haro.wav",
        "spectrogramUri": "https://example.blob/spectrogramspng/haro.png",
        "location": {"name": "Haro Strait", "latitude": 48.55, "longitude": -123.06},
        "timestamp": "2026-06-19T17:46:52Z",
        "reviewed": True,
        "found": "yes",
        "confidence": 76.77,
    },
    {
        "id": "out-of-region-1",
        "audioUri": "https://example.blob/audiowavs/pugetsound.wav",
        "location": {"name": "Point Robinson", "latitude": 47.34, "longitude": -122.32},
        "timestamp": "2026-06-19T16:00:00Z",
        "reviewed": False,
        "found": "no",
        "confidence": 50.0,
    },
]

# Page 2 is empty, which marks the end of the archive.
_PAGE_2 = []


class _JsonResponse:
    status_code = 200
    headers = {"content-type": "application/json; charset=utf-8"}

    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload


def _paged_get(pages):
    """Return a fake requests.get that serves successive pages by ``Page`` param."""

    def fake_get(url, *args, **kwargs):
        params = kwargs.get("params") or {}
        page = params.get("Page", 1)
        index = page - 1
        payload = pages[index] if index < len(pages) else []
        return _JsonResponse(payload)

    return fake_get


def test_normalization_and_region_filter():
    fake_get = _paged_get([_PAGE_1, _PAGE_2])
    with mock.patch(
        "src.aws_backend.sources.orcahello_history.requests.get", side_effect=fake_get
    ):
        records = OrcaHelloHistoryAdapter().fetch_history(records_per_page=2)

    # in_region_only (default) drops the out-of-region Point Robinson record.
    assert len(records) == 1
    record = records[0]

    assert record["id"] == "in-region-1"
    assert record["station"] == "Haro Strait"
    assert record["latitude"] == 48.55
    assert record["longitude"] == -123.06
    # Confidence scaled from 0-100 to 0-1.
    assert abs(record["confidence"] - 0.7677) < 1e-6
    # Timestamp normalized to an ISO string.
    assert record["t"] is not None
    assert record["t"].startswith("2026-06-19T17:46:52")
    # confirmed = reviewed AND affirmative found.
    assert record["reviewed"] is True
    assert record["found"] == "yes"
    assert record["confirmed"] is True
    assert record["audio_uri"] == "https://example.blob/audiowavs/haro.wav"
    assert record["spectrogram_uri"] == "https://example.blob/spectrogramspng/haro.png"


def test_in_region_only_disabled_keeps_all():
    fake_get = _paged_get([_PAGE_1, _PAGE_2])
    with mock.patch(
        "src.aws_backend.sources.orcahello_history.requests.get", side_effect=fake_get
    ):
        records = OrcaHelloHistoryAdapter().fetch_history(in_region_only=False)

    assert len(records) == 2
    out = next(r for r in records if r["id"] == "out-of-region-1")
    # Unreviewed + negative found is not confirmed.
    assert out["confirmed"] is False
    assert out["reviewed"] is False


def test_confirmed_only_filter():
    fake_get = _paged_get([_PAGE_1, _PAGE_2])
    with mock.patch(
        "src.aws_backend.sources.orcahello_history.requests.get", side_effect=fake_get
    ):
        records = OrcaHelloHistoryAdapter().fetch_history(
            in_region_only=False, confirmed_only=True
        )

    assert len(records) == 1
    assert records[0]["id"] == "in-region-1"
    assert records[0]["confirmed"] is True


def test_paging_stops_on_empty_page():
    fake_get = _paged_get([_PAGE_1, _PAGE_2])
    mocked = mock.Mock(side_effect=fake_get)
    with mock.patch(
        "src.aws_backend.sources.orcahello_history.requests.get", mocked
    ):
        OrcaHelloHistoryAdapter().fetch_history(max_pages=200)

    # Page 1 (data) + page 2 (empty) -> stops; never reaches page 3.
    assert mocked.call_count == 2
    pages_requested = [c.kwargs["params"]["Page"] for c in mocked.call_args_list]
    assert pages_requested == [1, 2]


def test_http_error_stops_and_returns_collected():
    class _ErrorResponse:
        status_code = 500
        headers = {"content-type": "text/html"}
        text = "boom"

    def fake_get(url, *args, **kwargs):
        params = kwargs.get("params") or {}
        if params.get("Page", 1) == 1:
            return _JsonResponse(_PAGE_1)
        return _ErrorResponse()

    with mock.patch(
        "src.aws_backend.sources.orcahello_history.requests.get", side_effect=fake_get
    ):
        records = OrcaHelloHistoryAdapter().fetch_history(in_region_only=False)

    # Page 1 collected, page 2 errored -> no raise, returns page-1 records.
    assert len(records) == 2

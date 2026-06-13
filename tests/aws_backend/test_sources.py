from src.aws_backend.sources.orcahello import OrcaHelloAdapter
from src.aws_backend.sources.inaturalist import INaturalistAdapter
from src.aws_backend.sources.base import SourceFetchResult


class _HtmlResponse:
    status_code = 200
    headers = {"content-type": "text/html; charset=utf-8"}
    text = "<html>not detections</html>"


def test_orcahello_rejects_non_json_response(monkeypatch):
    def fake_get(*_args, **_kwargs):
        return _HtmlResponse()

    monkeypatch.setattr("src.aws_backend.sources.orcahello.requests.get", fake_get)

    result = OrcaHelloAdapter().fetch()

    assert result.available is False
    assert result.content_type == "text/html; charset=utf-8"
    assert "non-JSON" in result.error


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


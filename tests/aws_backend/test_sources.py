from src.aws_backend.sources.orcahello import OrcaHelloAdapter


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


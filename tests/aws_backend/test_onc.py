"""Tests for the ONC (Ocean Networks Canada) hydrophone adapter + relay route.

Covers:
- Graceful degradation when ONC is disabled (200 metadata-only / 503).
- Strict filename validation (valid + malicious inputs) closing the SSRF /
  parameter-injection vector (AX-2).
- The enabled payload shape (with ONC mocked out).
- The ONC token never leaking into payloads or logs.
"""

from unittest import mock

import pytest
import requests
from fastapi.testclient import TestClient

from src.aws_backend.main import app
from src.aws_backend.sources import onc


client = TestClient(app)


# --------------------------------------------------------------------------- #
# Filename validation (AX-2)
# --------------------------------------------------------------------------- #

VALID_FILENAMES = [
    "ICLISTENHF1560_20181004T235903.000Z-spect.png",
    "AXISQ6044PTZACCC8E334C53_20161201T000001.000Z.jpg",
    "ClayoquotSlope_Bullseye_CTD_20170119T000000Z_20170119T003000Z-clean.png",
    "spectrogram.jpeg",
]

MALICIOUS_FILENAMES = [
    "http://evil.example/x.png",            # URL scheme + host
    "https://data.oceannetworks.ca/x.png",  # absolute URL
    "//evil.example/x.png",                 # scheme-relative
    "../../etc/passwd",                      # path traversal
    "foo/../bar.png",                        # embedded traversal
    "dir/sub/file.png",                      # slashes
    "file.png?token=stolen",                 # query separator
    "file.png&token=stolen",                 # param injection
    "file.png#frag",                         # fragment
    "file with space.png",                   # whitespace
    "file\t.png",                            # tab
    "file.png\n",                            # newline
    "file.exe",                              # disallowed extension
    "file.png.exe",                          # double extension trick
    "file",                                  # no extension
    ".png",                                  # empty stem
    "",                                      # empty
    "a" * 300 + ".png",                      # too long
    "f%2e%2e.png",                           # encoded traversal stays literal % (rejected)
    "file;rm -rf.png",                       # shell-ish chars
]


@pytest.mark.parametrize("name", VALID_FILENAMES)
def test_valid_filenames_accepted(name):
    assert onc.is_valid_archive_filename(name) is True
    assert onc.validate_archive_filename(name) == name


@pytest.mark.parametrize("name", MALICIOUS_FILENAMES)
def test_malicious_filenames_rejected(name):
    assert onc.is_valid_archive_filename(name) is False
    with pytest.raises(onc.OncInvalidFilename):
        onc.validate_archive_filename(name)


def test_non_string_filename_rejected():
    assert onc.is_valid_archive_filename(None) is False
    assert onc.is_valid_archive_filename(123) is False


def test_download_archivefile_validates_before_request(monkeypatch):
    """A malicious filename must never reach requests.get."""
    called = {"hit": False}

    def fake_get(*_a, **_k):
        called["hit"] = True
        raise AssertionError("requests.get must not be called for invalid filename")

    monkeypatch.setattr(onc.requests, "get", fake_get)
    with pytest.raises(onc.OncInvalidFilename):
        onc.download_archivefile("../../etc/passwd")
    assert called["hit"] is False


# --------------------------------------------------------------------------- #
# Graceful degradation (disabled)
# --------------------------------------------------------------------------- #

def test_hydrophone_signal_disabled_payload(monkeypatch):
    monkeypatch.setattr(onc, "onc_enabled", lambda: False)
    payload = onc.hydrophone_signal(station="Lime Kiln", lat=48.5, lng=-123.1)
    assert payload["status"] == "success"
    assert payload["enabled"] is False
    assert payload["spectrogram_url"] is None
    assert payload["station"]["name"] == "Lime Kiln"
    assert "ONC_API_TOKEN" in payload["message"]


def test_hydrophone_signal_route_disabled_returns_200(monkeypatch):
    monkeypatch.setattr(onc, "onc_enabled", lambda: False)
    resp = client.get("/api/onc/hydrophone-signal", params={"station": "Lime Kiln"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["enabled"] is False
    assert body["spectrogram_url"] is None


def test_archivefile_route_disabled_returns_503(monkeypatch):
    monkeypatch.setattr(onc, "onc_enabled", lambda: False)
    resp = client.get("/api/onc/archivefile", params={"filename": "valid_20240101T000000.000Z.png"})
    assert resp.status_code == 503


def test_archivefile_route_invalid_filename_returns_400(monkeypatch):
    # Even when enabled, a bad filename is rejected with 400 before any upstream call.
    monkeypatch.setattr(onc, "onc_enabled", lambda: True)
    for bad in ["../../etc/passwd", "http://evil/x.png", "a b.png", "x.exe"]:
        resp = client.get("/api/onc/archivefile", params={"filename": bad})
        assert resp.status_code == 400, bad


# --------------------------------------------------------------------------- #
# Enabled payload shape (ONC mocked)
# --------------------------------------------------------------------------- #

_LOCATIONS = [
    {"locationCode": "LKWA", "locationName": "Lime Kiln", "lat": 48.516, "lon": -123.152},
    {"locationCode": "SEVIP", "locationName": "Strait of Georgia East", "lat": 49.04, "lon": -123.32},
]

_ARCHIVE_FILES = {
    "files": [
        "ICLISTENHF1234_20240101T000000.000Z-spect.png",
        "ICLISTENHF1234_20240102T120000.000Z-spect.png",  # most recent
        "ICLISTENHF1234_20240101T120000.000Z-spect.png",
        "../evil.png",  # malicious entry from upstream must be dropped
        "notes.txt",    # wrong extension dropped
    ]
}


class _JsonResp:
    status_code = 200
    headers = {"Content-Type": "application/json"}

    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload

    def raise_for_status(self):
        return None


def _fake_get_factory():
    def fake_get(url, *_a, **kwargs):
        if url.endswith("/locations"):
            return _JsonResp(_LOCATIONS)
        if url.endswith("/archivefile/location"):
            return _JsonResp(_ARCHIVE_FILES)
        raise AssertionError(f"unexpected url {url}")

    return fake_get


def test_recent_spectrogram_filename_picks_latest_and_filters(monkeypatch):
    monkeypatch.setattr(onc, "_token", lambda: "FAKE")
    monkeypatch.setattr(onc.requests, "get", _fake_get_factory())
    name = onc.recent_spectrogram_filename("LKWA")
    assert name == "ICLISTENHF1234_20240102T120000.000Z-spect.png"
    assert onc.is_valid_archive_filename(name)


def test_recent_spectrogram_uses_fileExtension_param(monkeypatch):
    """ONC rejects ``extension``; the adapter must send ``fileExtension``."""
    captured = {}

    def fake_get(url, *_a, **kwargs):
        captured["params"] = kwargs.get("params")
        return _JsonResp(_ARCHIVE_FILES)

    monkeypatch.setattr(onc, "_token", lambda: "FAKE")
    monkeypatch.setattr(onc.requests, "get", fake_get)
    onc.recent_spectrogram_filename("LKWA")
    assert captured["params"]["fileExtension"] == "png"
    assert "extension" not in captured["params"]


def test_recent_spectrogram_prefers_full_over_small(monkeypatch):
    files = {
        "files": [
            "ICLISTENHF1_20240102T120000.000Z-FFT-spect-small.png",
            "ICLISTENHF1_20240102T120000.000Z-FFT-spect-thumb.png",
            "ICLISTENHF1_20240102T120000.000Z-FFT-spect.png",
        ]
    }
    monkeypatch.setattr(onc, "_token", lambda: "FAKE")
    monkeypatch.setattr(onc.requests, "get", lambda *a, **k: _JsonResp(files))
    name = onc.recent_spectrogram_filename("LKWA")
    assert name == "ICLISTENHF1_20240102T120000.000Z-FFT-spect.png"


def test_recent_spectrogram_400_returns_none(monkeypatch):
    """A 400 (no deployment in range, ONC errorCode 127) degrades to None."""

    class _Resp400:
        status_code = 400
        text = '{"errors":[{"errorCode":127,"errorMessage":"no deployment in range"}]}'

        def raise_for_status(self):
            raise AssertionError("should not raise on handled 400")

    monkeypatch.setattr(onc, "_token", lambda: "FAKE")
    monkeypatch.setattr(onc.requests, "get", lambda *a, **k: _Resp400())
    assert onc.recent_spectrogram_filename("LKWA") is None


def test_hydrophone_signal_enabled_payload_shape(monkeypatch):
    monkeypatch.setattr(onc, "onc_enabled", lambda: True)
    monkeypatch.setattr(onc, "_token", lambda: "FAKE")
    monkeypatch.setattr(onc.requests, "get", _fake_get_factory())

    payload = onc.hydrophone_signal(station="Lime Kiln", lat=48.52, lng=-123.15)

    assert payload["enabled"] is True
    assert payload["station"]["locationCode"] == "LKWA"
    assert payload["station"]["name"] == "Lime Kiln"
    # Proxied, token-free, URL-encoded path.
    assert payload["spectrogram_url"].startswith("/api/be/api/onc/archivefile?filename=")
    assert "ICLISTENHF1234_20240102T120000.000Z-spect.png" in payload["spectrogram_url"]
    assert payload["annotations_available"] is True
    assert "FAKE" not in str(payload)


def test_hydrophone_signal_request_failure_degrades(monkeypatch):
    monkeypatch.setattr(onc, "onc_enabled", lambda: True)
    monkeypatch.setattr(onc, "_token", lambda: "FAKE")

    def boom(*_a, **_k):
        raise requests.RequestException("connection refused")

    monkeypatch.setattr(onc.requests, "get", boom)
    payload = onc.hydrophone_signal(station="Lime Kiln", lat=48.5, lng=-123.1)
    assert payload["enabled"] is False
    assert payload["message"] == "ONC service unreachable."


# --------------------------------------------------------------------------- #
# Token never leaks (payload or logs)
# --------------------------------------------------------------------------- #

def test_redact_strips_token_value(monkeypatch):
    monkeypatch.setenv("ONC_API_TOKEN", "SUPERSECRET123")
    msg = "401 for url: https://data.oceannetworks.ca/api/archivefile/download?filename=x.png&token=SUPERSECRET123"
    redacted = onc._redact(msg)
    assert "SUPERSECRET123" not in redacted
    assert "token=***" in redacted


def test_redact_strips_token_param_even_if_value_unknown():
    msg = "Connecting to .../download?filename=x.png&token=abc123def THEN more"
    redacted = onc._redact(msg)
    assert "abc123def" not in redacted


def test_request_failure_does_not_log_token(monkeypatch, caplog):
    monkeypatch.setenv("ONC_API_TOKEN", "LEAKYTOKEN999")
    monkeypatch.setattr(onc, "onc_enabled", lambda: True)
    monkeypatch.setattr(onc, "_token", lambda: "LEAKYTOKEN999")

    def boom(*_a, **_k):
        raise requests.RequestException(
            "Max retries: url=https://data.oceannetworks.ca/api/locations?token=LEAKYTOKEN999"
        )

    monkeypatch.setattr(onc.requests, "get", boom)
    with caplog.at_level("WARNING"):
        onc.hydrophone_signal(station="X", lat=48.5, lng=-123.1)
    assert "LEAKYTOKEN999" not in caplog.text

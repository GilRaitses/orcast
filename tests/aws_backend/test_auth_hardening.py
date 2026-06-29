"""Auth hardening tests (Wave Set G3 remediation)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.aws_backend.main import app

client = TestClient(app)


@patch("src.aws_backend.auth.settings")
def test_production_rejects_spoofed_reviewer_without_proxy(mock_settings):
    mock_settings.env = "production"
    mock_settings.api_key = "secret-key"
    resp = client.post(
        "/api/decision-records",
        headers={
            "X-ORCAST-Key": "secret-key",
            "X-ORCAST-Reviewer-Id": "evil",
            "X-ORCAST-Reviewer-Email": "evil@example.com",
        },
        json={"verdict": "hold", "reason": "probe"},
    )
    assert resp.status_code == 401


@patch("src.aws_backend.auth.settings")
def test_production_requires_api_key_on_community_list(mock_settings):
    mock_settings.env = "production"
    mock_settings.api_key = "secret-key"
    resp = client.get("/api/community/submissions")
    assert resp.status_code == 401


@patch("src.aws_backend.auth.settings")
def test_production_accepts_trusted_proxy_reviewer(mock_settings):
    mock_settings.env = "production"
    mock_settings.api_key = "secret-key"
    with patch("src.aws_backend.routers.kernel._load_fit_report", return_value={"version": "test"}):
        with patch("src.aws_backend.routers.kernel.load_pending_approval", return_value=None):
            mock_storage = MagicMock()
            with patch("src.aws_backend.routers.kernel._get_storage", return_value=mock_storage):
                mock_storage.put_decision_record.return_value = None
                resp = client.post(
                    "/api/decision-records",
                    headers={
                        "X-ORCAST-Key": "secret-key",
                        "X-ORCAST-Trusted-Proxy": "vercel",
                        "X-ORCAST-Reviewer-Id": "user_123",
                        "X-ORCAST-Reviewer-Email": "reviewer@example.com",
                    },
                    json={"verdict": "hold", "reason": "test"},
                )
    assert resp.status_code == 200

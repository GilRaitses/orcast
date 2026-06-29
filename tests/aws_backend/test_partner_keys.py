import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from src.aws_backend.main import app
from src.aws_backend.partner.keys import MemoryPartnerKeyStore


def test_memory_partner_store_rejects_prefix_keys():
    store = MemoryPartnerKeyStore()
    assert store.verify("orcast_builder_fake") is None
    assert store.verify("orcast_partner_dev_key") is not None


def test_partner_verify_requires_api_key_when_configured():
    with patch.dict(os.environ, {"ORCAST_API_KEY": "internal-key"}, clear=False):
        client = TestClient(app)
        assert client.post("/api/partner/verify", json={"key": "x"}).status_code == 401
        ok = client.post(
            "/api/partner/verify",
            json={"key": "orcast_partner_dev_key"},
            headers={"X-ORCAST-Key": "internal-key"},
        )
        assert ok.status_code == 200
        assert ok.json()["tier"] == "builder"

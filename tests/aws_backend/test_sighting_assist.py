from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from src.aws_backend.main import app
from src.aws_backend.sighting_assist.local_llm import _template_reply


client = TestClient(app)


def test_template_reply_mentions_three_questions():
    ctx = {
        "user_message": "I saw a dorsal fin",
        "forecast": {
            "effective_confidence": 0.0,
            "confidence_raw": 0.0,
            "intensity": 0.001,
            "promoted": False,
        },
        "spatial": {"note": "Temporal-only pilot."},
        "level0_detector_qc": {
            "status": "active",
            "n_reviewed_labels": 100,
            "confirmed_fraction": 0.1,
            "false_positive_rate": 0.6,
        },
        "nearby_sample": [{"source": "obis", "distance_km": 2.0}],
        "integrity_conditions": ["Single station"],
        "glossary_anchors": {
            "encounter_likelihood": "/glossary#fitness-gates",
            "integrity": "/glossary#integrity-conditions",
            "level0_qc": "/glossary#level0-detector-qc",
            "provenance": "/glossary#provenance",
            "level1_psth": "/glossary#level1-psth",
        },
    }
    out = _template_reply(ctx)
    assert out["source"] == "template"
    assert "Encounter likelihood" in out["reply"]
    assert "Was what you saw an orca?" in out["reply"]
    assert "Should you report it?" in out["reply"]


def test_sighting_assist_status():
    resp = client.get("/api/sighting-assist/status")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    assert "narration_backend" in body
    assert "bedrock_enabled" in body


@patch("src.aws_backend.sighting_assist.local_llm._bedrock_chat")
@patch("src.aws_backend.sighting_assist.local_llm.settings")
def test_compose_reply_bedrock(mock_settings, mock_bedrock):
    mock_settings.enable_bedrock = True
    mock_settings.llm_enabled = False
    mock_settings.bedrock_sighting_model_id = "anthropic.claude-3-haiku-20240307-v1:0"
    mock_bedrock.return_value = "Bedrock says maybe."
    from src.aws_backend.sighting_assist.local_llm import compose_reply

    out = compose_reply({"user_message": "fin?", "glossary_anchors": {}})
    assert out["source"] == "bedrock"
    assert "Bedrock says maybe." in out["reply"]


@patch("src.aws_backend.sighting_assist.local_llm._bedrock_chat")
@patch("src.aws_backend.sighting_assist.local_llm.settings")
def test_compose_reply_bedrock_falls_back(mock_settings, mock_bedrock):
    mock_settings.enable_bedrock = True
    mock_settings.llm_enabled = False
    mock_bedrock.side_effect = RuntimeError("access denied")
    from src.aws_backend.sighting_assist.local_llm import compose_reply

    out = compose_reply(
        {
            "user_message": "fin?",
            "forecast": {
                "effective_confidence": 0,
                "confidence_raw": 0,
                "intensity": 0.001,
                "promoted": False,
            },
            "spatial": {},
            "level0_detector_qc": {},
            "nearby_sample": [],
            "integrity_conditions": [],
            "glossary_anchors": {
                "encounter_likelihood": "/glossary#fitness-gates",
                "provenance": "/glossary#provenance",
                "level1_psth": "/glossary#level1-psth",
            },
        }
    )
    assert out["source"] == "template"
    assert out.get("llm_error")


def test_sighting_assist_out_of_bounds():
    resp = client.post(
        "/api/sighting-assist",
        json={"lat": 10.0, "lng": 10.0, "message": "orca?"},
    )
    assert resp.status_code == 422


@patch("src.aws_backend.routers.sighting_assist.compose_reply")
@patch("src.aws_backend.routers.sighting_assist.build_sighting_context")
def test_sighting_assist_endpoint(mock_build, mock_compose):
    mock_build.return_value = {
        "user_message": "orca?",
        "cell": {"lat": 48.55, "lng": -123.05, "when": "2026-01-01T00:00:00+00:00"},
        "forecast": {
            "effective_confidence": 0,
            "confidence_raw": 0,
            "intensity": 0.01,
            "promoted": False,
        },
        "integrity_conditions": ["Single station"],
        "glossary_anchors": {
            "encounter_likelihood": "/glossary#fitness-gates",
        },
    }
    mock_compose.return_value = {
        "reply": "Bedrock says maybe.",
        "source": "bedrock",
        "model": "anthropic.claude-3-haiku-20240307-v1:0",
    }
    resp = client.post(
        "/api/sighting-assist",
        json={"lat": 48.5465, "lng": -123.03, "message": "I saw a fin"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["source"] == "bedrock"
    assert body["reply"] == "Bedrock says maybe."

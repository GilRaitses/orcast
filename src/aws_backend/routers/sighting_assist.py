"""Conversational sighting check grounded in provenance + gates."""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from ..sighting_assist import build_sighting_context, compose_reply, llm_status

router = APIRouter()


class SightingAssistRequest(BaseModel):
    lat: float = Field(..., description="Where the observer was (or map pin)")
    lng: float
    message: str = Field(..., min_length=1, max_length=2000)
    when: Optional[str] = Field(default=None, description="ISO8601 observation time; defaults to now")
    station: Optional[str] = None
    evidence_assets: list = Field(default_factory=list, description="Metadata refs for uploaded images/audio")


@router.get("/api/sighting-assist/status")
def sighting_assist_status() -> Dict[str, Any]:
    """Narration backend status (Bedrock enabled, model id, fallback mode)."""
    return {"status": "success", **llm_status()}


@router.post("/api/sighting-assist")
def sighting_assist(payload: SightingAssistRequest) -> Dict[str, Any]:
    """Interpret a possible orca sighting using only API-grounded facts."""
    # Build a human-readable evidence note for the narration prompt
    evidence_note = ""
    if payload.evidence_assets:
        parts = []
        for a in payload.evidence_assets[:5]:
            kind = a.get("kind", "file")
            name = a.get("filename", "upload")
            parts.append(f"{kind}: {name}")
        evidence_note = "Observer uploaded evidence, " + ", ".join(parts) + ". "

    augmented_message = evidence_note + payload.message if evidence_note else payload.message

    context = build_sighting_context(
        payload.lat,
        payload.lng,
        when=payload.when,
        station=payload.station,
        message=augmented_message,
    )
    context["evidence_assets"] = payload.evidence_assets
    narration = compose_reply(context)
    return {
        "status": "success",
        "cell": context["cell"],
        "reply": narration["reply"],
        "source": narration["source"],
        "model": narration.get("model"),
        "llm_error": narration.get("llm_error"),
        "context_summary": {
            "effective_confidence": context["forecast"]["effective_confidence"],
            "intensity": context["forecast"]["intensity"],
            "promoted": context["forecast"]["promoted"],
            "integrity_conditions": context["integrity_conditions"][:6],
            "level0_status": (context.get("level0_detector_qc") or {}).get("status"),
        },
        "glossary_links": list((context.get("glossary_anchors") or {}).values()),
        "submit_path": "/moderation",
    }

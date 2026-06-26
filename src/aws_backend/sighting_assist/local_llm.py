"""Sighting narration: Amazon Bedrock (production) or template fallback."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple

import requests

from ..config import settings

SYSTEM_PROMPT = """You are ORCAST Sighting Check — an evidence interpreter for the Salish Sea pilot region.

Rules (never break these):
1. Separate three questions: (a) encounter likelihood from the temporal model, (b) whether the user's specific sighting was likely an orca, (c) whether they should report it.
2. Use ONLY numbers and facts from the JSON context. If a fact is missing, say you don't know.
3. The kernel model is temporal-only in this pilot — do NOT claim the model pinpoints orcas at a map coordinate.
4. Level 0 detector QC describes acoustic detector labels, not visual sightings — say so when relevant.
5. Never claim certainty about the user's observation. Common misIDs: harbor porpoise, seal, log, boat wake.
6. End with a short "Sources" bullet list using the glossary paths from context.glossary_anchors (copy paths exactly, e.g. /glossary#level0-detector-qc).
7. Keep the reply under 220 words, plain language, 2-4 short paragraphs."""


def llm_status() -> Dict[str, Any]:
    """Report which narration backend is active (Bedrock vs template vs optional Ollama)."""
    status: Dict[str, Any] = {
        "bedrock_enabled": settings.enable_bedrock,
        "bedrock_model": settings.bedrock_sighting_model_id,
        "narration_backend": "template",
        "fallback": "template",
    }

    if settings.enable_bedrock:
        status["narration_backend"] = "bedrock"
        status["setup_hint"] = (
            "Set ORCAST_ENABLE_BEDROCK=true on App Runner; IAM role needs bedrock:InvokeModel."
        )
        return status

    if settings.llm_enabled:
        base = settings.llm_base_url.rstrip("/")
        reachable = False
        error: Optional[str] = None
        try:
            resp = requests.get(f"{base}/api/tags", timeout=3)
            if resp.ok:
                reachable = True
                status["narration_backend"] = "ollama"
            else:
                error = f"tags HTTP {resp.status_code}"
        except Exception as exc:
            error = str(exc)
        status.update(
            {
                "llm_enabled": True,
                "llm_base_url": base,
                "llm_model": settings.llm_model,
                "llm_reachable": reachable,
                "error": error,
                "setup_hint": "Dev-only: ollama pull phi3:mini && ollama serve",
            }
        )
        if not reachable:
            status["narration_backend"] = "template"
        return status

    status["setup_hint"] = "Enable ORCAST_ENABLE_BEDROCK=true for AWS narration, or use template fallback."
    return status


def compose_reply(context: Dict[str, Any]) -> Dict[str, Any]:
    """Return narrated reply; Bedrock when enabled, else template (optional Ollama in dev)."""
    if settings.enable_bedrock:
        try:
            text = _bedrock_chat(context)
            return {
                "reply": text,
                "source": "bedrock",
                "model": settings.bedrock_sighting_model_id,
            }
        except Exception as exc:
            fallback = _template_reply(context)
            fallback["llm_error"] = str(exc)
            return fallback

    if settings.llm_enabled:
        try:
            text, model = _ollama_chat(context)
            return {"reply": text, "source": "ollama", "model": model}
        except Exception as exc:
            fallback = _template_reply(context)
            fallback["llm_error"] = str(exc)
            return fallback

    return _template_reply(context)


def _bedrock_chat(context: Dict[str, Any]) -> str:
    import boto3

    user_content = (
        "User sighting question:\n"
        f"{context.get('user_message') or '(no detail provided)'}\n\n"
        "Ground-truth JSON (cite only these facts):\n"
        f"{json.dumps(context, indent=2, default=str)}"
    )
    client = boto3.client("bedrock-runtime", region_name=settings.aws_region)
    response = client.invoke_model(
        modelId=settings.bedrock_sighting_model_id,
        body=json.dumps(
            {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": settings.llm_max_tokens,
                "temperature": settings.llm_temperature,
                "system": SYSTEM_PROMPT,
                "messages": [{"role": "user", "content": user_content}],
            }
        ),
    )
    payload = json.loads(response["body"].read())
    text = (payload.get("content") or [{}])[0].get("text") or ""
    if not text.strip():
        raise RuntimeError("Bedrock returned an empty message")
    return text.strip()


def _ollama_chat(context: Dict[str, Any]) -> Tuple[str, str]:
    base = settings.llm_base_url.rstrip("/")
    user_content = (
        "User sighting question:\n"
        f"{context.get('user_message') or '(no detail provided)'}\n\n"
        "Ground-truth JSON (cite only these facts):\n"
        f"{json.dumps(context, indent=2, default=str)}"
    )
    payload = {
        "model": settings.llm_model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        "stream": False,
        "options": {
            "temperature": settings.llm_temperature,
            "num_predict": settings.llm_max_tokens,
        },
    }
    resp = requests.post(
        f"{base}/api/chat",
        json=payload,
        timeout=settings.llm_timeout_seconds,
    )
    if not resp.ok:
        raise RuntimeError(f"Ollama chat HTTP {resp.status_code}: {resp.text[:200]}")
    message = (resp.json().get("message") or {}).get("content") or ""
    if not message.strip():
        raise RuntimeError("Ollama returned an empty message")
    return message.strip(), settings.llm_model


def _template_reply(context: Dict[str, Any]) -> Dict[str, Any]:
    """Deterministic narration when Bedrock (or Ollama) is unavailable."""
    fc = context.get("forecast") or {}
    eff = fc.get("effective_confidence")
    eff_pct = round(float(eff or 0) * 100) if eff is not None else 0
    raw_pct = round(float(fc.get("confidence_raw") or 0) * 100)
    intensity = fc.get("intensity")
    promoted = fc.get("promoted")
    spatial = context.get("spatial") or {}
    level0 = context.get("level0_detector_qc") or {}
    nearby = context.get("nearby_sample") or []
    integrity = context.get("integrity_conditions") or []
    anchors = context.get("glossary_anchors") or {}
    user_msg = context.get("user_message") or ""

    lines: List[str] = []

    lines.append(
        "**Encounter likelihood (model, not your sighting):** "
        f"The temporal forecast at this time has effective confidence {eff_pct}% "
        f"(raw fit {raw_pct}%, intensity {intensity}). "
        "This model describes timing patterns for the pilot region — it does not verify an individual dorsal fin or acoustic ping at your pin. "
        f"{spatial.get('note', '')}"
    )

    if level0.get("status") == "active":
        cf = level0.get("confirmed_fraction")
        fpr = level0.get("false_positive_rate")
        n = level0.get("n_reviewed_labels")
        cf_s = f"{float(cf):.3f}" if cf is not None else "n/a"
        fpr_s = f"{float(fpr):.3f}" if fpr is not None else "n/a"
        lines.append(
            "**Was what you saw an orca?** "
            "We cannot confirm your observation from the spike-train model alone. "
            f"Level 0 detector QC on reviewed acoustic labels ({n} labels) shows "
            f"confirmed fraction {cf_s} and false-positive rate {fpr_s} when humans review detector outputs — "
            "visual shore sightings are different evidence. "
            "Harbor porpoise, seals, logs, and boat wakes are common confusions. "
            f"See {anchors.get('level0_qc', '/glossary#level0-detector-qc')}."
        )
    else:
        lines.append(
            "**Was what you saw an orca?** "
            "The system cannot verify individual sightings yet; treat your observation as unconfirmed until reviewed. "
            "Describe behavior, group size, and direction in a community report."
        )

    if nearby:
        sample = ", ".join(
            f"{n.get('source')} @ {n.get('distance_km')}km" for n in nearby[:3]
        )
        lines.append(
            f"**Nearby evidence (unordered proximity sample, not recency):** {sample}."
        )

    if integrity:
        lines.append(
            "**Integrity conditions for this fit:** "
            + "; ".join(integrity[:4])
            + (f" (+{len(integrity) - 4} more)" if len(integrity) > 4 else "")
            + f". Details: {anchors.get('integrity', '/glossary#integrity-conditions')}."
        )

    lines.append(
        "**Should you report it?** "
        "Yes, if you are unsure — submit a shore report for moderation. "
        "It enters the queue with low weight until a reviewer approves attribution. "
        f"Promoted forecast: {'yes' if promoted else 'no — confidence capped until human promotion'}."
    )

    if user_msg:
        lines.append(f"*You wrote:* “{user_msg[:280]}”")

    lines.append(
        "**Sources:** "
        f"{anchors.get('encounter_likelihood', '/glossary#fitness-gates')}, "
        f"{anchors.get('provenance', '/glossary#provenance')}, "
        f"{anchors.get('level1_psth', '/glossary#level1-psth')}."
    )

    return {
        "reply": "\n\n".join(lines),
        "source": "template",
        "model": None,
    }

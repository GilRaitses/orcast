"""Exploration guide narration — Bedrock or template, grounded in read-only tools."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from ..config import settings
from ..sighting_assist.local_llm import llm_status
from .models import GuideReply
from .tools import fetch_forecast_cell, fetch_gates, fetch_hotspots, fetch_provenance

SYSTEM_PROMPT = """You are the ORCAST Exploration Guide — you help users navigate gates, provenance, and map context.

Rules (never break these):
1. You are NOT a forecast oracle. You explain what the gates and provenance already show.
2. Use ONLY facts from the JSON tool outputs. If data is missing, say you don't know.
3. Always mention effective confidence vs raw confidence when promotion matters.
4. Link users to /gates for gate details and to the map for provenance — use the deep_links provided.
5. Never suggest approving moderation, promotion, or writing decision records.
6. Keep replies under 250 words, plain language, 2-4 short paragraphs.
7. End with a "Navigate" bullet list of deep links (labels from context)."""


def build_exploration_context(
    message: str,
    *,
    viewport: Optional[Dict[str, Any]] = None,
    focus: Optional[Dict[str, Any]] = None,
    skills: Optional[List[str]] = None,
) -> tuple[Dict[str, Any], List[Dict[str, str]], List[Dict[str, str]], List[str], List[str], List[str]]:
    """Gather read-only tool outputs for guide narration (no LLM)."""
    if skills is not None:
        from ..casting.skills import run_skills

        result = run_skills(skills, message, viewport=viewport, focus=focus)
        return (
            result.context,
            result.citations,
            result.deep_links,
            result.tools_used,
            result.gate_ids,
            result.provenance_refs,
        )

    tools_used: List[str] = []
    context: Dict[str, Any] = {"user_message": message}

    gates = fetch_gates()
    context["gates"] = gates
    tools_used.append("fetch_gates")

    lat = lng = None
    if viewport:
        lat = viewport.get("lat")
        lng = viewport.get("lng")
    if focus and focus.get("cell"):
        try:
            parts = str(focus["cell"]).split(",")
            lat = float(parts[0].strip())
            lng = float(parts[1].strip())
        except (ValueError, IndexError):
            pass
    if lat is not None and lng is not None:
        context["provenance"] = fetch_provenance(float(lat), float(lng))
        context["forecast_cell"] = fetch_forecast_cell(float(lat), float(lng))
        tools_used.extend(["fetch_provenance", "fetch_forecast_cell"])
    else:
        context["hotspots"] = fetch_hotspots(limit=5)
        tools_used.append("fetch_hotspots")

    citations = [
        {"label": "Fitness gates", "href": "/gates"},
        {"label": "Glossary", "href": "/glossary"},
    ]
    deep_links = [{"label": "Open gates page", "href": "/gates"}]
    if lat is not None and lng is not None:
        deep_links.append(
            {
                "label": "Map provenance",
                "href": f"/?lat={lat}&lng={lng}&provenance=1",
            }
        )
        deep_links.append(
            {
                "label": "Explore this pin",
                "href": f"/explore?lat={lat}&lng={lng}",
            }
        )

    gate_ids = _extract_gate_ids(gates)
    provenance_refs: List[str] = []
    if lat is not None and lng is not None:
        provenance_refs.append(f"{lat},{lng}")

    return context, citations, deep_links, tools_used, gate_ids, provenance_refs


def compose_guide_reply(
    message: str,
    *,
    viewport: Optional[Dict[str, Any]] = None,
    focus: Optional[Dict[str, Any]] = None,
    gateway_reply: Optional[str] = None,
    gateway_model: Optional[str] = None,
    instructions: Optional[str] = None,
    skills: Optional[List[str]] = None,
    prefetched: Optional[
        tuple[
            Dict[str, Any],
            List[Dict[str, str]],
            List[Dict[str, str]],
            List[str],
            List[str],
            List[str],
        ]
    ] = None,
    model_id: Optional[str] = None,
) -> GuideReply:
    if prefetched is not None:
        context, citations, deep_links, tools_used, gate_ids, provenance_refs = prefetched
    else:
        context, citations, deep_links, tools_used, gate_ids, provenance_refs = build_exploration_context(
            message,
            viewport=viewport,
            focus=focus,
            skills=skills,
        )

    system_prompt = instructions or SYSTEM_PROMPT
    bedrock_model = model_id or settings.bedrock_sighting_model_id

    if gateway_reply and gateway_reply.strip():
        return GuideReply(
            reply=gateway_reply.strip(),
            citations=citations,
            deep_links=deep_links,
            source="ai_gateway",
            model=gateway_model,
            tools_used=tools_used,
            gate_ids=gate_ids,
            provenance_refs=provenance_refs,
        )

    if settings.enable_bedrock:
        try:
            text = _bedrock_guide(context, system_prompt, bedrock_model)
            return GuideReply(
                reply=text,
                citations=citations,
                deep_links=deep_links,
                source="bedrock",
                model=bedrock_model,
                tools_used=tools_used,
                gate_ids=gate_ids,
                provenance_refs=provenance_refs,
            )
        except Exception as exc:
            fallback = _template_guide(context, citations, deep_links, tools_used, gate_ids, provenance_refs)
            fallback.llm_error = str(exc)
            return fallback

    return _template_guide(context, citations, deep_links, tools_used, gate_ids, provenance_refs)


def guide_status() -> Dict[str, Any]:
    status = llm_status()
    status["guide_backend"] = status.get("narration_backend", "template")
    return status


def _bedrock_guide(
    context: Dict[str, Any],
    system_prompt: str = SYSTEM_PROMPT,
    model_id: Optional[str] = None,
) -> str:
    import boto3

    user_content = (
        f"User question:\n{context.get('user_message')}\n\n"
        "Tool JSON (cite only these facts):\n"
        f"{json.dumps(context, indent=2, default=str)}"
    )
    client = boto3.client("bedrock-runtime", region_name=settings.aws_region)
    response = client.invoke_model(
        modelId=model_id or settings.bedrock_sighting_model_id,
        body=json.dumps(
            {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": settings.llm_max_tokens,
                "temperature": settings.llm_temperature,
                "system": system_prompt,
                "messages": [{"role": "user", "content": user_content}],
            }
        ),
    )
    payload = json.loads(response["body"].read())
    text = (payload.get("content") or [{}])[0].get("text") or ""
    if not text.strip():
        raise RuntimeError("Bedrock returned an empty message")
    return text.strip()


def _template_guide(
    context: Dict[str, Any],
    citations: List[Dict[str, str]],
    deep_links: List[Dict[str, str]],
    tools_used: List[str],
    gate_ids: List[str],
    provenance_refs: List[str],
) -> GuideReply:
    gates = context.get("gates") or {}
    eff = gates.get("effective_confidence")
    eff_pct = round(float(eff or 0) * 100) if eff is not None else 0
    raw = gates.get("confidence")
    raw_pct = round(float(raw or 0) * 100) if raw is not None else 0
    promoted = gates.get("promoted")
    status = gates.get("status", "unknown")

    lines = [
        "**Exploration guide (template mode):** "
        f"The fit status is `{status}`. Effective confidence is {eff_pct}% "
        f"(raw {raw_pct}%). Promoted: {'yes' if promoted else 'no'}.",
        "Open **Gates** for level-1 PSTH, cross-validation, time-rescaling, and PIT verdicts. "
        "This guide does not replace those records.",
    ]

    prov = context.get("provenance")
    if prov and prov.get("status") == "success":
        lines.append(
            f"**Map cell ({prov.get('lat')}, {prov.get('lng')}):** "
            f"intensity {prov.get('intensity')} — temporal model only, not a sighting verifier."
        )
    elif context.get("hotspots"):
        hs = (context["hotspots"].get("hotspots") or [])[:3]
        if hs:
            sample = ", ".join(f"{h.get('lat')},{h.get('lng')}" for h in hs)
            lines.append(f"**Sample hotspot cells:** {sample}. Pick a map pin for cell provenance.")

    lines.append(
        "**Navigate:** "
        + ", ".join(f"[{d['label']}]({d['href']})" for d in deep_links)
    )

    return GuideReply(
        reply="\n\n".join(lines),
        citations=citations,
        deep_links=deep_links,
        source="template",
        model=None,
        tools_used=tools_used,
        gate_ids=gate_ids,
        provenance_refs=provenance_refs,
    )


def _extract_gate_ids(gates: Dict[str, Any]) -> List[str]:
    ids: List[str] = []
    block = gates.get("gates") or {}
    for name, payload in block.items():
        if isinstance(payload, dict) and payload:
            ids.append(name)
    repr_id = gates.get("repr_id")
    if repr_id:
        ids.append(f"repr:{repr_id}")
    return ids

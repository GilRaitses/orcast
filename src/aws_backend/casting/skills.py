"""Skill catalog and manifest-driven dispatch for managed agents."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from ..exploration.tools import (
    fetch_data_status,
    fetch_decision_records,
    fetch_environmental,
    fetch_forecast_cell,
    fetch_gates,
    fetch_hotspots,
    fetch_ingestion_status,
    fetch_live_hydrophones,
    fetch_pending_approval,
    fetch_provenance,
    fetch_realtime_events,
    fetch_review_dossier_summary,
    fetch_snapshot_manifest,
    fetch_supervisor_recommendation,
    fetch_verified_sightings,
)
from .manifest import SkillSpec, enabled_skill_ids, get_skill, load_manifest
from .studio_skills import STUDIO_DISPATCH

SkillFn = Callable[..., Dict[str, Any]]

_DISPATCH: Dict[str, SkillFn] = {
    "fetch_gates": lambda **_kw: fetch_gates(),
    "fetch_provenance": fetch_provenance,
    "fetch_hotspots": fetch_hotspots,
    "fetch_forecast_cell": fetch_forecast_cell,
    "fetch_environmental": lambda **_kw: fetch_environmental(),
    "fetch_live_hydrophones": lambda **_kw: fetch_live_hydrophones(),
    "fetch_realtime_events": lambda **_kw: fetch_realtime_events(),
    "fetch_data_status": lambda **_kw: fetch_data_status(),
    "fetch_verified_sightings": lambda **_kw: fetch_verified_sightings(),
    "fetch_review_dossier_summary": lambda **_kw: fetch_review_dossier_summary(),
    "fetch_decision_records": lambda **_kw: fetch_decision_records(),
    "fetch_supervisor_recommendation": lambda **_kw: fetch_supervisor_recommendation(),
    "fetch_pending_approval": lambda **_kw: fetch_pending_approval(),
    "fetch_snapshot_manifest": lambda **_kw: fetch_snapshot_manifest(),
    "fetch_ingestion_status": lambda **_kw: fetch_ingestion_status(),
}

# BSS managed HUD skills (poster viz, tagtools steps, behavior capture) extend
# the Central Casting dispatch. Net-new; tiers/honesty preserved in the manifest.
_DISPATCH.update(STUDIO_DISPATCH)

# Backward-compatible alias for tests and policy imports.
SKILL_CATALOG: Dict[str, SkillFn] = {
    sid: _DISPATCH[sid] for sid in enabled_skill_ids() if sid in _DISPATCH
}


@dataclass
class SkillRunResult:
    context: Dict[str, Any]
    citations: List[Dict[str, str]]
    deep_links: List[Dict[str, str]]
    tools_used: List[str]
    gate_ids: List[str]
    provenance_refs: List[str]
    annotations: List[Dict[str, Any]] = field(default_factory=list)
    step_records: List[Dict[str, Any]] = field(default_factory=list)


def _resolve_pin(
    viewport: Optional[Dict[str, Any]],
    focus: Optional[Dict[str, Any]],
) -> Tuple[Optional[float], Optional[float]]:
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
        return float(lat), float(lng)
    return None, None


def _should_run_skill(spec: SkillSpec, has_pin: bool) -> bool:
    if spec.geo_required and not has_pin:
        return False
    return True


def _invoke_skill(
    skill_id: str,
    *,
    lat: Optional[float],
    lng: Optional[float],
) -> Tuple[Dict[str, Any], str, List[str], int]:
    fn = _DISPATCH.get(skill_id)
    if fn is None:
        return {"status": "error", "message": "no handler"}, "error", [], 0
    started = time.perf_counter()
    try:
        if skill_id in ("fetch_provenance", "fetch_forecast_cell"):
            payload = fn(lat=float(lat), lng=float(lng))  # type: ignore[arg-type]
        else:
            payload = fn()
        status = str(payload.get("status", "success"))
        refs: List[str] = []
        if skill_id == "fetch_gates":
            refs.extend(_extract_gate_ids(payload))
        if lat is not None and lng is not None and skill_id in ("fetch_provenance", "fetch_forecast_cell"):
            refs.append(f"{lat},{lng}")
        duration_ms = int((time.perf_counter() - started) * 1000)
        return payload, status, refs, duration_ms
    except Exception as exc:
        duration_ms = int((time.perf_counter() - started) * 1000)
        return (
            {"status": "error", "message": str(exc)},
            "error",
            [],
            duration_ms,
        )


def _annotations_for_skill(
    skill_id: str,
    payload: Dict[str, Any],
    *,
    lat: Optional[float],
    lng: Optional[float],
) -> List[Dict[str, Any]]:
    annotations: List[Dict[str, Any]] = []
    if payload.get("status") in (None, "error", "not_fitted", "not_available", "none"):
        return annotations

    if skill_id == "fetch_gates":
        artifact = {}
        if payload.get("repr_id"):
            artifact["repr_id"] = payload["repr_id"]
        if payload.get("run_id"):
            artifact["run_id"] = payload["run_id"]
        annotations.append(
            {
                "type": "gate_citation",
                "label": "Fitness gates",
                "href": "/gates",
                "artifact": artifact or None,
            }
        )
    elif skill_id in ("fetch_provenance", "fetch_forecast_cell") and lat is not None:
        annotations.append(
            {
                "type": "provenance_citation",
                "label": "Map provenance",
                "href": f"/?lat={lat}&lng={lng}&provenance=1",
                "lat": lat,
                "lng": lng,
            }
        )
    elif skill_id == "fetch_hotspots":
        annotations.append({"type": "deep_link", "label": "Open map", "href": "/"})
    elif skill_id in ("fetch_realtime_events", "fetch_verified_sightings"):
        annotations.append(
            {
                "type": "evidence_citation",
                "label": "Recent sightings",
                "href": "/",
            }
        )
    elif skill_id == "fetch_environmental":
        annotations.append(
            {
                "type": "evidence_citation",
                "label": "Environmental conditions",
                "href": "/",
            }
        )
    elif skill_id == "fetch_live_hydrophones":
        annotations.append(
            {
                "type": "evidence_citation",
                "label": "Hydrophone stations",
                "href": "/",
            }
        )
    elif skill_id == "fetch_decision_records":
        annotations.append(
            {
                "type": "decision_citation",
                "label": "Decision audit log",
                "href": "/decisions",
            }
        )
    elif skill_id == "fetch_review_dossier_summary":
        annotations.append(
            {
                "type": "artifact_citation",
                "label": "Review dossier",
                "href": "/review-dossier/latest",
            }
        )
    elif skill_id in ("fetch_supervisor_recommendation", "fetch_pending_approval"):
        annotations.append(
            {
                "type": "gate_citation",
                "label": "Promotion gates",
                "href": "/gates",
            }
        )
    return [a for a in annotations if a.get("artifact") is not None or a.get("href")]


def run_skills(
    skill_names: List[str],
    message: str,
    *,
    viewport: Optional[Dict[str, Any]] = None,
    focus: Optional[Dict[str, Any]] = None,
) -> SkillRunResult:
    """Execute named skills via manifest rules and build narration context."""
    context: Dict[str, Any] = {"user_message": message}
    tools_used: List[str] = []
    step_records: List[Dict[str, Any]] = []
    annotations: List[Dict[str, Any]] = []
    lat, lng = _resolve_pin(viewport, focus)
    has_pin = lat is not None and lng is not None

    for skill_id in skill_names:
        spec = get_skill(skill_id)
        if spec is None or not spec.enabled:
            continue
        if not _should_run_skill(spec, has_pin):
            continue
        payload, status, refs, duration_ms = _invoke_skill(skill_id, lat=lat, lng=lng)
        step_records.append(
            {
                "type": "skill_invocation",
                "skill": skill_id,
                "input": {"lat": lat, "lng": lng} if has_pin and spec.geo_required else {},
                "output_status": status,
                "duration_ms": duration_ms,
                "grounding_refs": refs,
            }
        )
        if status in ("error",):
            continue
        tools_used.append(skill_id)
        context_key = skill_id.removeprefix("fetch_")
        context[context_key] = payload
        annotations.extend(_annotations_for_skill(skill_id, payload, lat=lat, lng=lng))

    citations = [
        {"label": "Fitness gates", "href": "/gates"},
        {"label": "Glossary", "href": "/glossary"},
    ]
    deep_links = [{"label": "Open gates page", "href": "/gates"}]
    if has_pin:
        deep_links.append(
            {"label": "Map provenance", "href": f"/?lat={lat}&lng={lng}&provenance=1"}
        )
        deep_links.append(
            {"label": "Explore this pin", "href": f"/explore?lat={lat}&lng={lng}"}
        )

    gate_ids = _extract_gate_ids(context.get("gates") or {})
    provenance_refs: List[str] = []
    if has_pin:
        provenance_refs.append(f"{lat},{lng}")

    return SkillRunResult(
        context=context,
        citations=citations,
        deep_links=deep_links,
        tools_used=tools_used,
        gate_ids=gate_ids,
        provenance_refs=provenance_refs,
        annotations=annotations,
        step_records=step_records,
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


def manifest_skill_ids() -> List[str]:
    return list(load_manifest().keys())

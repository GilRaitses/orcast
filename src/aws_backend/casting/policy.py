"""Policy enforcement for managed agent skills and deep links."""

from __future__ import annotations

from typing import Dict, List

from fastapi import HTTPException

from .manifest import validate_agent_skills
from .models import ManagedAgent
from .skills import SKILL_CATALOG


def validate_skill_plan(skill_ids: List[str], *, public_route: bool = True) -> None:
    try:
        validate_agent_skills(skill_ids, public_route=public_route)
    except ValueError as exc:
        msg = str(exc)
        if msg.startswith("unknown_skills"):
            raise HTTPException(
                status_code=400,
                detail={"error": "invalid_ui_intent", "reason": "unknown_skills", "skills": skill_ids},
            ) from exc
        if msg.startswith("disabled_skills"):
            raise HTTPException(
                status_code=400,
                detail={"error": "invalid_ui_intent", "reason": "disabled_skills", "message": msg},
            ) from exc
        if msg.startswith("tier_blocked"):
            raise HTTPException(
                status_code=400,
                detail={"error": "invalid_ui_intent", "reason": "tier_blocked"},
            ) from exc
        raise HTTPException(status_code=400, detail={"error": "invalid_ui_intent", "message": msg}) from exc


def validate_skills(agent: ManagedAgent, *, public_route: bool = True) -> None:
    try:
        validate_agent_skills(agent.skills, public_route=public_route)
    except ValueError as exc:
        msg = str(exc)
        if msg.startswith("unknown_skills"):
            raise HTTPException(
                status_code=400,
                detail={"error": "unknown_skills", "skills": agent.skills},
            ) from exc
        if msg.startswith("disabled_skills"):
            raise HTTPException(
                status_code=400,
                detail={"error": "disabled_skills", "message": msg},
            ) from exc
        if msg.startswith("tier_blocked"):
            raise HTTPException(
                status_code=400,
                detail={"error": "tier_blocked", "message": "T2/T3 skills require keyed routes"},
            ) from exc
        raise HTTPException(status_code=400, detail=msg) from exc

    unknown = [s for s in agent.skills if s not in SKILL_CATALOG]
    if unknown:
        raise HTTPException(
            status_code=400,
            detail={"error": "unknown_skills", "skills": unknown},
        )
    if agent.policy.write_tools:
        raise HTTPException(
            status_code=400,
            detail="write_tools not supported in Wave Set M",
        )


def filter_deep_links(
    agent: ManagedAgent,
    deep_links: List[Dict[str, str]],
) -> List[Dict[str, str]]:
    allowed = set(agent.policy.allowed_deep_links)
    if not allowed:
        return deep_links
    filtered: List[Dict[str, str]] = []
    for link in deep_links:
        href = link.get("href", "")
        path = href.split("?")[0] if href.startswith("/") else href
        if any(path == a or path.startswith(f"{a}?") or href.startswith(a) for a in allowed):
            filtered.append(link)
        elif any(href.startswith(a) for a in allowed):
            filtered.append(link)
    return filtered or deep_links

"""Managed agent interactions API (Concierge invoke-by-ID)."""

from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, model_validator

from ..auth import ReviewerIdentity, require_api_key, reviewer_identity
from ..casting.concierge import prepare_interaction, run_interaction
from ..casting.planner import DEFAULT_PLANNER_ID, plan_interaction
from ..casting.registry import build_managed_agent_store
from ..config import settings
from ..exploration.db import aurora_configured
from ..exploration.limits import ExploreLimitError, assert_turn_quota
from ..exploration.session_store import SessionStore, exploration_status

router = APIRouter()
_store = build_managed_agent_store()
logger = logging.getLogger(__name__)


class InlineAgentSpec(BaseModel):
    instructions: str = Field(..., min_length=1, max_length=8000)
    skills: list[str] = Field(..., min_length=1, max_length=32)
    version: Optional[str] = Field(default="inline", max_length=32)
    data_bindings: Optional[Dict[str, str]] = None
    model: Optional[Dict[str, str]] = None
    policy: Optional[Dict[str, Any]] = None


class InteractionRequest(BaseModel):
    session_id: str = Field(..., min_length=8, max_length=64)
    message: str = Field(..., min_length=1, max_length=2000)
    agent_id: Optional[str] = Field(default=None, max_length=64)
    agent_version: Optional[str] = Field(default=None, max_length=32)
    agent: Optional[InlineAgentSpec] = None
    viewport: Optional[Dict[str, Any]] = None
    focus: Optional[Dict[str, Any]] = None
    gateway_reply: Optional[str] = Field(default=None, max_length=8000)
    gateway_model: Optional[str] = Field(default=None, max_length=120)

    @model_validator(mode="after")
    def require_agent_source(self) -> "InteractionRequest":
        if not self.agent_id and self.agent is None:
            raise ValueError("agent_id or agent inline spec required")
        return self


def _require_aurora() -> None:
    if not aurora_configured():
        raise HTTPException(
            status_code=503,
            detail="Interactions require ORCAST_DATABASE_URL. See docs/devpost/casting/MANAGED_AGENTS_CONTRACT.md",
        )


def _inline_dict(payload: InteractionRequest) -> Optional[Dict[str, Any]]:
    if payload.agent is None:
        return None
    return payload.agent.model_dump(exclude_none=True)


def casting_status() -> Dict[str, Any]:
    base = exploration_status()
    base.update(
        {
            "casting_enabled": bool(settings.managed_agents_table or settings.storage_backend != "aws"),
            "managed_agents_table": settings.managed_agents_table or None,
        }
    )
    return base


def _interaction_response(result) -> Dict[str, Any]:
    return {
        "status": "success",
        "interaction_id": result.interaction_id,
        "reply": result.guide.reply,
        "citations": result.guide.citations,
        "deep_links": result.guide.deep_links,
        "source": result.guide.source,
        "model": result.guide.model,
        "tools_used": result.guide.tools_used,
        "llm_error": result.guide.llm_error,
        "managed_agent_id": result.managed_agent_id,
        "agent_version": result.agent_version,
        "resolved_spec_hash": result.resolved_spec_hash,
        "hydration_mode": result.hydration_mode,
        "skills_invoked": result.skills_invoked,
        "steps": result.steps,
        "annotations": result.annotations,
    }


def _prepare_response(result) -> Dict[str, Any]:
    return {
        "status": "success",
        "managed_agent_id": result.managed_agent_id,
        "agent_version": result.agent_version,
        "resolved_spec_hash": result.resolved_spec_hash,
        "hydration_mode": result.hydration_mode,
        "context": result.context,
        "citations": result.citations,
        "deep_links": result.deep_links,
        "tools_used": result.tools_used,
        "gate_ids": result.gate_ids,
        "provenance_refs": result.provenance_refs,
        "steps": result.steps,
        "annotations": result.annotations,
    }


@router.get("/api/interactions/status")
def interactions_status() -> Dict[str, Any]:
    return {"status": "success", **casting_status()}


class PlanRequest(InteractionRequest):
    surface_state: Optional[Dict[str, Any]] = None
    narrate: bool = False

    @model_validator(mode="after")
    def require_agent_source(self) -> "PlanRequest":
        return self


def _plan_response(result) -> Dict[str, Any]:
    prep = result.prepare
    body: Dict[str, Any] = {
        "status": "success",
        "ui_intent": result.ui_intent,
        "resolved_spec_hash": result.resolved_spec_hash,
        "managed_agent_id": prep.managed_agent_id,
        "agent_version": prep.agent_version,
        "hydration_mode": prep.hydration_mode,
        "prepare": {
            "context": prep.context,
            "citations": prep.citations,
            "deep_links": prep.deep_links,
            "tools_used": prep.tools_used,
            "gate_ids": prep.gate_ids,
            "provenance_refs": prep.provenance_refs,
            "steps": prep.steps,
            "annotations": prep.annotations,
        },
    }
    return body


@router.post("/api/interactions/plan", dependencies=[Depends(require_api_key)])
def plan_cast_interaction(
    payload: PlanRequest,
    identity: ReviewerIdentity = Depends(reviewer_identity),
) -> Dict[str, Any]:
    """Surface planner — validated ui_intent + executed skill_plan.

    Exposed publicly via the same-origin proxy for anonymous-first access
    (HANDOFF_CHARTER B2). Anonymous turns (no proxy-stamped reviewer identity)
    are restricted to public T0/T1 skills; keyed T2/T3 skills require a
    signed-in reviewer, so the public planner simply omits those panels.
    """
    _require_aurora()
    # public_route=True forbids T2/T3 skills even if a crafted inline agent or
    # message tries to request them. Reviewers stamped by the trusted proxy keep
    # full keyed access.
    public_route = identity.reviewer_id is None
    store = SessionStore()
    if not store.session_exists(payload.session_id):
        raise HTTPException(status_code=404, detail="Session not found")

    inline = _inline_dict(payload)
    try:
        result = plan_interaction(
            _store,
            session_id=payload.session_id,
            agent_id=payload.agent_id or DEFAULT_PLANNER_ID,
            agent_version=payload.agent_version,
            message=payload.message,
            viewport=payload.viewport,
            focus=payload.focus,
            inline_agent=inline,
            public_route=public_route,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={"error": "invalid_ui_intent", "message": str(exc)},
        ) from exc

    response = _plan_response(result)

    if payload.narrate:
        from ..casting.concierge import _resolve_cast_agent
        from ..exploration.guide import compose_guide_reply

        agent, _ = _resolve_cast_agent(
            _store,
            agent_id=payload.agent_id or DEFAULT_PLANNER_ID,
            agent_version=payload.agent_version,
            inline_agent=inline,
            session_id=payload.session_id,
        )
        prep = result.prepare
        guide = compose_guide_reply(
            payload.message,
            viewport=payload.viewport,
            focus=payload.focus,
            instructions=agent.instructions,
            skills=list(result.ui_intent.get("skill_plan") or []),
            prefetched=(
                prep.context,
                prep.citations,
                prep.deep_links,
                prep.tools_used,
                prep.gate_ids,
                prep.provenance_refs,
            ),
            model_id=agent.model.get("model_id"),
        )
        response["reply"] = guide.reply
        response["source"] = guide.source
        response["model"] = guide.model

        # Durability (ORCHESTRATOR_NARRATOR_FRAMEWORK.md sec 5): persist the
        # planned ui_intent turn so planner mode has multi-turn history and the
        # step trace is replayable. Persistence failure must not fail the turn.
        interaction_id = str(uuid.uuid4())
        response["interaction_id"] = interaction_id
        try:
            store.save_interaction_exchange(
                payload.session_id,
                payload.message,
                guide,
                interaction_id=interaction_id,
                managed_agent_id=prep.managed_agent_id,
                agent_version=prep.agent_version,
                resolved_spec_hash=result.resolved_spec_hash,
                hydration_mode=prep.hydration_mode,
                skills_invoked=list(result.ui_intent.get("skill_plan") or []),
                interaction_steps=prep.steps,
            )
        except Exception as exc:  # noqa: BLE001 - persistence is best-effort
            logger.warning("plan turn persistence failed: %s", exc)

    return response


class NarrateRequest(InteractionRequest):
    """Second-phase narration input for the panels-first turn.

    Carries the grounded context that ``/plan`` already produced so narration can
    run Bedrock WITHOUT re-dispatching skills or live source calls.
    """

    skill_plan: list[str] = Field(default_factory=list, max_length=32)
    context: Dict[str, Any] = Field(default_factory=dict)
    citations: list[Dict[str, Any]] = Field(default_factory=list)
    deep_links: list[Dict[str, Any]] = Field(default_factory=list)
    tools_used: list[str] = Field(default_factory=list)
    gate_ids: list[str] = Field(default_factory=list)
    provenance_refs: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def require_agent_source(self) -> "NarrateRequest":
        return self


@router.post("/api/interactions/narrate", dependencies=[Depends(require_api_key)])
def narrate_cast_interaction(payload: NarrateRequest) -> Dict[str, Any]:
    """Compose the Bedrock narration for an already-planned turn.

    ``/plan`` returns validated panels + grounded ``prepare`` context quickly; the
    client paints panels immediately, then calls this with that same context to
    fetch the ~5s narration asynchronously. The grounded context is reused as-is
    (``prefetched``), so no skills or live source calls run a second time, and
    first paint is never gated on the narration model.
    """
    _require_aurora()
    store = SessionStore()
    if not store.session_exists(payload.session_id):
        raise HTTPException(status_code=404, detail="Session not found")

    inline = _inline_dict(payload)
    from ..casting.concierge import _resolve_cast_agent
    from ..exploration.guide import compose_guide_reply

    agent, _ = _resolve_cast_agent(
        _store,
        agent_id=payload.agent_id or DEFAULT_PLANNER_ID,
        agent_version=payload.agent_version,
        inline_agent=inline,
        session_id=payload.session_id,
    )
    prefetched = (
        payload.context,
        payload.citations,
        payload.deep_links,
        payload.tools_used,
        payload.gate_ids,
        payload.provenance_refs,
    )
    guide = compose_guide_reply(
        payload.message,
        viewport=payload.viewport,
        focus=payload.focus,
        instructions=agent.instructions,
        skills=list(payload.skill_plan),
        prefetched=prefetched,
        model_id=agent.model.get("model_id"),
    )

    interaction_id = str(uuid.uuid4())
    try:
        store.save_interaction_exchange(
            payload.session_id,
            payload.message,
            guide,
            interaction_id=interaction_id,
            managed_agent_id=payload.agent_id or DEFAULT_PLANNER_ID,
            agent_version=payload.agent_version or "inline",
            resolved_spec_hash="",
            hydration_mode="inline" if inline else "managed",
            skills_invoked=list(payload.skill_plan),
            interaction_steps=[],
        )
    except Exception as exc:  # noqa: BLE001 - persistence is best-effort
        logger.warning("narrate turn persistence failed: %s", exc)

    return {
        "status": "success",
        "interaction_id": interaction_id,
        "reply": guide.reply,
        "source": guide.source,
        "model": guide.model,
        "citations": guide.citations,
        "deep_links": guide.deep_links,
    }


@router.post("/api/interactions/prepare")
def prepare_cast_interaction(payload: InteractionRequest) -> Dict[str, Any]:
    """Return grounded tool context for Vercel AI Gateway narration (no LLM, no persist)."""
    _require_aurora()
    store = SessionStore()
    if not store.session_exists(payload.session_id):
        raise HTTPException(status_code=404, detail="Session not found")

    inline = _inline_dict(payload)
    try:
        result = prepare_interaction(
            _store,
            session_id=payload.session_id,
            agent_id=payload.agent_id,
            agent_version=payload.agent_version,
            message=payload.message,
            viewport=payload.viewport,
            focus=payload.focus,
            inline_agent=inline,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return _prepare_response(result)


@router.post("/api/interactions")
def create_interaction(payload: InteractionRequest) -> Dict[str, Any]:
    _require_aurora()
    store = SessionStore()
    if not store.session_exists(payload.session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    try:
        assert_turn_quota(payload.session_id)
    except ExploreLimitError as exc:
        raise HTTPException(status_code=429, detail={"error": exc.code, "message": exc.message}) from exc

    inline = _inline_dict(payload)
    try:
        result = run_interaction(
            _store,
            session_id=payload.session_id,
            agent_id=payload.agent_id,
            agent_version=payload.agent_version,
            message=payload.message,
            viewport=payload.viewport,
            focus=payload.focus,
            gateway_reply=payload.gateway_reply,
            gateway_model=payload.gateway_model,
            inline_agent=inline,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    store.save_interaction_exchange(
        payload.session_id,
        payload.message,
        result.guide,
        interaction_id=result.interaction_id,
        managed_agent_id=result.managed_agent_id,
        agent_version=result.agent_version,
        resolved_spec_hash=result.resolved_spec_hash,
        hydration_mode=result.hydration_mode,
        skills_invoked=result.skills_invoked,
        interaction_steps=result.steps,
    )

    return _interaction_response(result)

"""Managed agent interactions API (Concierge invoke-by-ID)."""

from __future__ import annotations

import json
import logging
import threading
import time
import uuid
from typing import Any, Dict, Iterator, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, model_validator

from ..auth import ReviewerIdentity, require_api_key, reviewer_identity
from ..casting.concierge import prepare_interaction, run_interaction
from ..casting.planner import DEFAULT_PLANNER_ID, plan_interaction
from ..casting.registry import build_managed_agent_store
from ..config import settings
from ..exploration.db import aurora_configured
from ..exploration.limits import ExploreLimitError, assert_turn_quota
from ..exploration.models import GuideReply
from ..exploration.session_store import SessionStore, exploration_status

router = APIRouter()
_store = build_managed_agent_store()
logger = logging.getLogger(__name__)

# WS6 M3: bound concurrent narration streams per process. Each sync boto3 stream
# holds one AnyIO threadpool thread across chunk waits, so an unbounded number of
# long-lived streams could starve the pool shared with sync DB calls. A stream
# that cannot acquire a slot emits a busy error and the client falls back to the
# non-streamed JSON /narrate.
_stream_semaphore = threading.BoundedSemaphore(settings.stream_max_concurrent)


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


try:  # psycopg is optional until the DB driver is installed (see exploration.db)
    import psycopg
except ImportError:  # pragma: no cover - exercised only when the driver is absent
    psycopg = None  # type: ignore[assignment]

# A configured-but-unreachable database (connection refused, auth, or timeout) or
# an unmigrated schema (missing table) raises from the connection layer.
# ``aurora_configured`` only checks that the connection env var is present, so
# without this guard such a failure escapes a turn handler as an unhandled 500.
# Map it to the same 503 the config check already returns.
_DB_UNAVAILABLE_ERRORS: tuple[type[BaseException], ...] = (
    (RuntimeError, psycopg.Error) if psycopg is not None else (RuntimeError,)
)


def _require_aurora() -> None:
    if not aurora_configured():
        raise HTTPException(
            status_code=503,
            detail="Interactions require ORCAST_DATABASE_URL. See docs/devpost/casting/MANAGED_AGENTS_CONTRACT.md",
        )


def _require_session(store: SessionStore, session_id: str) -> None:
    """Resolve the session, degrading a real DB connection or migration failure
    to 503 rather than letting it surface as an unhandled 500.

    ``_require_aurora`` passes when the connection env var is merely present, so a
    host that is unreachable or a schema that is not migrated only fails here,
    inside ``session_exists``. The turn handlers map ``LookupError`` and
    ``ValueError`` only, so this converts the DB-layer error to the documented
    503 instead.
    """
    try:
        exists = store.session_exists(session_id)
    except _DB_UNAVAILABLE_ERRORS as exc:
        raise HTTPException(
            status_code=503,
            detail="Interactions require a reachable, migrated database. See docs/devpost/casting/MANAGED_AGENTS_CONTRACT.md",
        ) from exc
    if not exists:
        raise HTTPException(status_code=404, detail="Session not found")


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
    _require_session(store, payload.session_id)

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
        from ..exploration.guide import _is_public_version, compose_guide_reply

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
            public=_is_public_version(agent.version),
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
    from ..exploration.guide import _is_public_version, compose_guide_reply

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
        public=_is_public_version(agent.version),
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


def _sse_frame(event: str, data: Dict[str, Any]) -> str:
    """One SSE frame: an ``event:`` line, a ``data:`` line, and a blank separator."""
    return f"event: {event}\ndata: {json.dumps(data, separators=(',', ':'), default=str)}\n\n"


def _narrate_stream_events(
    payload: "NarrateRequest",
    agent: Any,
    store: SessionStore,
    interaction_id: str,
    inline: Optional[Dict[str, Any]],
) -> Iterator[str]:
    """Sync generator: emit meta -> token(s) -> done (or error).

    Sync ``def`` on purpose so Starlette iterates it in a threadpool, keeping the
    synchronous boto3 stream off the event loop. Labels/citations/deep_links/
    provenance ride the prefetched plan context and are emitted in the opening
    ``meta`` event byte-identical to the panels-first split; only the prose
    streams. The exchange is persisted exactly once, after a successful stream;
    an aborted or failed stream persists nothing (no partial DB turn).
    """
    # WS6 M3: take a concurrency slot. If the pool is saturated, refuse fast with
    # a busy error so the client falls back to JSON rather than queueing a thread.
    if not _stream_semaphore.acquire(blocking=False):
        logger.warning("narrate stream rejected: concurrency cap reached")
        yield _sse_frame("error", {"error": "stream_busy", "message": "Too many concurrent streams"})
        return

    try:
        prefetched = (
            payload.context,
            payload.citations,
            payload.deep_links,
            payload.tools_used,
            payload.gate_ids,
            payload.provenance_refs,
        )
        model = agent.model.get("model_id") or settings.bedrock_sighting_model_id

        yield _sse_frame(
            "meta",
            {
                "interaction_id": interaction_id,
                "citations": payload.citations,
                "deep_links": payload.deep_links,
                "source": "bedrock" if settings.enable_bedrock else None,
                "model": model,
            },
        )

        parts: list[str] = []
        final_source = "bedrock"
        final_model = model
        try:
            if settings.enable_bedrock:
                from ..exploration.guide import _bedrock_guide_stream

                # WS6 M3: hard per-stream wall-clock cap, independent of the
                # Vercel maxDuration on the proxy leg.
                deadline = time.monotonic() + settings.stream_max_seconds
                for text in _bedrock_guide_stream(payload.context, agent.instructions, model):
                    if time.monotonic() > deadline:
                        raise RuntimeError("Stream exceeded wall-clock cap")
                    parts.append(text)
                    yield _sse_frame("token", {"text": text})
                full = "".join(parts).strip()
                if not full:
                    raise RuntimeError("Bedrock stream returned an empty message")
            else:
                # No Bedrock: compose the non-streamed reply (template / gateway)
                # and emit it as a single token so the client contract is identical.
                from ..exploration.guide import _is_public_version, compose_guide_reply

                composed = compose_guide_reply(
                    payload.message,
                    viewport=payload.viewport,
                    focus=payload.focus,
                    instructions=agent.instructions,
                    skills=list(payload.skill_plan),
                    prefetched=prefetched,
                    model_id=model,
                    public=_is_public_version(agent.version),
                )
                full = composed.reply
                final_source = composed.source
                final_model = composed.model
                yield _sse_frame("token", {"text": full})
        except Exception as exc:  # noqa: BLE001 - a failed stream falls back, never persists
            logger.warning("narrate stream failed: %s", exc)
            yield _sse_frame("error", {"error": "stream_failed", "message": str(exc)})
            return

        guide = GuideReply(
            reply=full,
            citations=list(payload.citations),
            deep_links=list(payload.deep_links),
            source=final_source,
            model=final_model,
            tools_used=list(payload.tools_used),
            gate_ids=list(payload.gate_ids),
            provenance_refs=list(payload.provenance_refs),
        )
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
            logger.warning("narrate stream persistence failed: %s", exc)

        yield _sse_frame("done", {"reply": full, "source": final_source, "model": final_model})
    finally:
        # Always release on completion, error, or GeneratorExit (client abort).
        _stream_semaphore.release()


@router.post("/api/interactions/narrate/stream", dependencies=[Depends(require_api_key)])
def narrate_cast_interaction_stream(payload: NarrateRequest) -> StreamingResponse:
    """SSE variant of ``/narrate`` for the live console (App Runner lane).

    Reached only through the dedicated streaming Vercel route whose upstream is
    App Runner (the cloudflared path buffers SSE). Streams ``meta`` -> ``token``
    -> ``done`` over ``text/event-stream``. The non-streamed ``/narrate`` JSON
    path remains as the guaranteed fallback; a buffered or failed stream falls
    back there, it never hangs.
    """
    _require_aurora()
    store = SessionStore()
    if not store.session_exists(payload.session_id):
        raise HTTPException(status_code=404, detail="Session not found")

    # WS6 B1: gate minting like the other turn paths. A streamed turn costs a
    # Bedrock invocation, so enforce the per-session turn quota before streaming
    # (the per-IP rate bucket is enforced at the dedicated Vercel route).
    try:
        assert_turn_quota(payload.session_id)
    except ExploreLimitError as exc:
        raise HTTPException(status_code=429, detail={"error": exc.code, "message": exc.message}) from exc

    inline = _inline_dict(payload)
    from ..casting.concierge import _resolve_cast_agent

    agent, _ = _resolve_cast_agent(
        _store,
        agent_id=payload.agent_id or DEFAULT_PLANNER_ID,
        agent_version=payload.agent_version,
        inline_agent=inline,
        session_id=payload.session_id,
    )
    interaction_id = str(uuid.uuid4())
    return StreamingResponse(
        _narrate_stream_events(payload, agent, store, interaction_id, inline),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


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

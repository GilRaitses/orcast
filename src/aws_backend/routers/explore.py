"""Public exploration guide API (Aurora session history + grounded narration)."""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from ..config import settings
from ..exploration.db import aurora_configured
from ..exploration.guide import compose_guide_reply
from ..exploration.limits import ExploreLimitError, assert_session_quota, assert_turn_quota
from ..exploration.session_store import SessionStore, exploration_status

try:  # connection-level failures (e.g. RDS unreachable from this host) -> 503, not 500
    import psycopg

    _DB_UNREACHABLE: tuple = (psycopg.OperationalError, psycopg.InterfaceError)
except Exception:  # pragma: no cover - psycopg optional
    _DB_UNREACHABLE = ()

router = APIRouter()


def _db_unavailable(exc: Exception) -> HTTPException:
    return HTTPException(
        status_code=503,
        detail="Exploration database is temporarily unreachable; explore history is unavailable right now.",
    )


class CreateSessionRequest(BaseModel):
    title: Optional[str] = Field(default=None, max_length=200)


class ExploreTurnRequest(BaseModel):
    session_id: str = Field(..., min_length=8, max_length=64)
    message: str = Field(..., min_length=1, max_length=2000)
    viewport: Optional[Dict[str, Any]] = None
    focus: Optional[Dict[str, Any]] = None
    gateway_reply: Optional[str] = Field(default=None, max_length=8000)
    gateway_model: Optional[str] = Field(default=None, max_length=120)


def _require_aurora() -> None:
    if not aurora_configured():
        raise HTTPException(
            status_code=503,
            detail="Exploration guide requires ORCAST_DATABASE_URL (Aurora). See docs/devpost/exploration/CONTRACT.md",
        )


@router.post("/api/explore/prepare")
def explore_prepare(payload: ExploreTurnRequest) -> Dict[str, Any]:
    """Return grounded tool context for Vercel AI Gateway narration (no LLM)."""
    _require_aurora()
    store = SessionStore()
    try:
        session_exists = store.session_exists(payload.session_id)
    except _DB_UNREACHABLE as exc:
        raise _db_unavailable(exc) from exc
    if not session_exists:
        raise HTTPException(status_code=404, detail="Session not found")
    from ..exploration.guide import build_exploration_context

    context, citations, deep_links, tools_used, gate_ids, provenance_refs = build_exploration_context(
        payload.message,
        viewport=payload.viewport,
        focus=payload.focus,
    )
    return {
        "status": "success",
        "context": context,
        "citations": citations,
        "deep_links": deep_links,
        "tools_used": tools_used,
        "gate_ids": gate_ids,
        "provenance_refs": provenance_refs,
    }


@router.get("/api/explore/status")
def explore_status() -> Dict[str, Any]:
    return {"status": "success", **exploration_status()}


def _keyed_automation(request: Request) -> bool:
    key = request.headers.get("x-orcast-key") or request.headers.get("X-ORCAST-Key")
    return bool(settings.api_key and key == settings.api_key)


@router.post("/api/explore/sessions")
def create_session(payload: CreateSessionRequest, request: Request) -> Dict[str, Any]:
    _require_aurora()
    client_ip = request.client.host if request.client else None
    store = SessionStore()
    try:
        if not _keyed_automation(request):
            assert_session_quota(client_ip)
        session_id = store.create_session(title=payload.title, client_ip=client_ip)
    except ExploreLimitError as exc:
        raise HTTPException(status_code=429, detail={"error": exc.code, "message": exc.message}) from exc
    except _DB_UNREACHABLE as exc:
        raise _db_unavailable(exc) from exc
    return {"status": "success", "session_id": session_id}


@router.post("/api/explore/turn")
def explore_turn(payload: ExploreTurnRequest) -> Dict[str, Any]:
    _require_aurora()
    store = SessionStore()
    try:
        session_exists = store.session_exists(payload.session_id)
    except _DB_UNREACHABLE as exc:
        raise _db_unavailable(exc) from exc
    if not session_exists:
        raise HTTPException(status_code=404, detail="Session not found")
    try:
        assert_turn_quota(payload.session_id)
    except ExploreLimitError as exc:
        raise HTTPException(status_code=429, detail={"error": exc.code, "message": exc.message}) from exc
    except _DB_UNREACHABLE as exc:
        raise _db_unavailable(exc) from exc

    guide = compose_guide_reply(
        payload.message,
        viewport=payload.viewport,
        focus=payload.focus,
        gateway_reply=payload.gateway_reply,
        gateway_model=payload.gateway_model,
        public=True,
    )
    try:
        store.save_exchange(payload.session_id, payload.message, guide)
    except _DB_UNREACHABLE as exc:
        raise _db_unavailable(exc) from exc

    return {
        "status": "success",
        "reply": guide.reply,
        "citations": guide.citations,
        "deep_links": guide.deep_links,
        "source": guide.source,
        "model": guide.model,
        "tools_used": guide.tools_used,
        "llm_error": guide.llm_error,
    }

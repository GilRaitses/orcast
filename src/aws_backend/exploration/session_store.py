"""Persist exploration sessions and turns in Aurora PostgreSQL."""

from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any, Dict, List, Optional

from ..config import settings
from ..sighting_assist.local_llm import llm_status
from .db import aurora_configured, aurora_connected, get_connection
from .limits import session_expires_at
from .models import ExplorationTurn, GuideReply


def exploration_status() -> Dict[str, Any]:
    base = llm_status()
    enabled = aurora_configured()
    connected = aurora_connected() if enabled else False
    base.update(
        {
            "aurora_enabled": enabled,
            "aurora_connected": connected,
            "postgres_engine": "rds" if enabled else None,
            "exploration_backend": "postgres" if connected else ("disabled" if not enabled else "unreachable"),
        }
    )
    if not enabled:
        base["setup_hint"] = "Set ORCAST_DATABASE_URL on App Runner and run migrations/001_initial.sql"
    return base


class SessionStore:
    """Postgres-backed session store."""

    def create_session(
        self,
        *,
        title: Optional[str] = None,
        client_ip: Optional[str] = None,
    ) -> str:
        session_id = str(uuid.uuid4())
        ip_hash = None
        if client_ip:
            ip_hash = hashlib.sha256(client_ip.encode("utf-8")).hexdigest()[:16]
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO exploration_sessions (id, title, client_ip_hash, expires_at)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (session_id, title, ip_hash, session_expires_at()),
                )
            conn.commit()
        return session_id

    def session_exists(self, session_id: str) -> bool:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT 1 FROM exploration_sessions WHERE id = %s",
                    (session_id,),
                )
                return cur.fetchone() is not None

    def append_turn(self, session_id: str, turn: ExplorationTurn) -> None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO exploration_turns (
                      session_id, role, content, tool_calls_json,
                      gate_ids, provenance_refs, model, source,
                      interaction_id, managed_agent_id, agent_version,
                      resolved_spec_hash, hydration_mode, skills_invoked,
                      interaction_steps
                    )
                    VALUES (%s, %s, %s, %s::jsonb, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
                    """,
                    (
                        session_id,
                        turn.role,
                        turn.content,
                        json.dumps(turn.tool_calls),
                        turn.gate_ids,
                        turn.provenance_refs,
                        turn.model,
                        turn.source,
                        turn.interaction_id,
                        turn.managed_agent_id,
                        turn.agent_version,
                        turn.resolved_spec_hash,
                        turn.hydration_mode,
                        turn.skills_invoked or None,
                        json.dumps(turn.interaction_steps) if turn.interaction_steps else None,
                    ),
                )
            conn.commit()

    def list_turns(self, session_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT role, content, tool_calls_json, gate_ids, provenance_refs, model, source, created_at
                    FROM exploration_turns
                    WHERE session_id = %s
                    ORDER BY created_at ASC
                    LIMIT %s
                    """,
                    (session_id, limit),
                )
                rows = cur.fetchall()
        return [
            {
                "role": row[0],
                "content": row[1],
                "tool_calls": row[2] or [],
                "gate_ids": row[3] or [],
                "provenance_refs": row[4] or [],
                "model": row[5],
                "source": row[6],
                "created_at": row[7].isoformat() if row[7] else None,
            }
            for row in rows
        ]

    def save_exchange(
        self,
        session_id: str,
        user_message: str,
        guide: GuideReply,
    ) -> None:
        self.append_turn(
            session_id,
            ExplorationTurn(role="user", content=user_message),
        )
        self.append_turn(
            session_id,
            ExplorationTurn(
                role="assistant",
                content=guide.reply,
                tool_calls=[{"name": t} for t in guide.tools_used],
                gate_ids=guide.gate_ids,
                provenance_refs=guide.provenance_refs,
                model=guide.model,
                source=guide.source,
            ),
        )

    def save_interaction_exchange(
        self,
        session_id: str,
        user_message: str,
        guide: GuideReply,
        *,
        interaction_id: str,
        managed_agent_id: str,
        agent_version: str,
        resolved_spec_hash: str,
        hydration_mode: str,
        skills_invoked: List[str],
        interaction_steps: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        self.append_turn(
            session_id,
            ExplorationTurn(role="user", content=user_message),
        )
        self.append_turn(
            session_id,
            ExplorationTurn(
                role="assistant",
                content=guide.reply,
                tool_calls=[{"name": t} for t in guide.tools_used],
                gate_ids=guide.gate_ids,
                provenance_refs=guide.provenance_refs,
                model=guide.model,
                source=guide.source,
                interaction_id=interaction_id,
                managed_agent_id=managed_agent_id,
                agent_version=agent_version,
                resolved_spec_hash=resolved_spec_hash,
                hydration_mode=hydration_mode,
                skills_invoked=skills_invoked,
                interaction_steps=interaction_steps,
            ),
        )


def store_available() -> bool:
    return aurora_configured() and settings.storage_backend != "memory"

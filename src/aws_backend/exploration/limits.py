"""Exploration session retention and abuse limits."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from ..config import settings
from .db import get_connection


class ExploreLimitError(Exception):
    """Raised when explore abuse limits are exceeded."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def purge_expired_sessions() -> int:
    """Delete sessions past expires_at (cascade turns). Returns rows removed."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM exploration_sessions
                WHERE expires_at IS NOT NULL AND expires_at < now()
                """
            )
            deleted = cur.rowcount
        conn.commit()
    return deleted


def assert_session_quota(client_ip: str | None) -> None:
    if not client_ip:
        return
    ip_hash = _hash_ip(client_ip)
    since = datetime.now(timezone.utc) - timedelta(days=1)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*) FROM exploration_sessions
                WHERE client_ip_hash = %s AND created_at >= %s
                """,
                (ip_hash, since),
            )
            count = cur.fetchone()[0]
    if count >= settings.explore_max_sessions_per_ip_day:
        raise ExploreLimitError(
            "session_quota",
            f"Max {settings.explore_max_sessions_per_ip_day} exploration sessions per day",
        )


def assert_turn_quota(session_id: str) -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*) FROM exploration_turns
                WHERE session_id = %s AND role = 'user'
                """,
                (session_id,),
            )
            count = cur.fetchone()[0]
    if count >= settings.explore_max_turns_per_session:
        raise ExploreLimitError(
            "turn_quota",
            f"Max {settings.explore_max_turns_per_session} turns per session",
        )


def session_expires_at() -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=settings.explore_retention_days)


def _hash_ip(client_ip: str) -> str:
    import hashlib

    return hashlib.sha256(client_ip.encode("utf-8")).hexdigest()[:16]

"""Apply exploration SQL migrations at startup (idempotent)."""

from __future__ import annotations

from pathlib import Path

from .db import aurora_configured, get_connection

_MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


def run_pending_migrations() -> None:
    if not aurora_configured():
        return
    if not _MIGRATIONS_DIR.is_dir():
        return
    for path in sorted(_MIGRATIONS_DIR.glob("*.sql")):
        sql = path.read_text(encoding="utf-8")
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
            conn.commit()

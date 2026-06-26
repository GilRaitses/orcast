"""Postgres connection helper for exploration sessions."""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Iterator, Optional

from ..config import settings

try:
    import psycopg
except ImportError:  # pragma: no cover - optional until requirements installed
    psycopg = None  # type: ignore


def _db_host() -> str:
    return os.getenv("ORCAST_DB_HOST", "").strip()


def _db_password() -> str:
    return os.getenv("ORCAST_DB_PASSWORD", "").strip()


def aurora_configured() -> bool:
    if _db_host() and _db_password():
        return True
    return bool(settings.database_url.strip())


def _connect_kwargs() -> dict:
    host = _db_host()
    password = _db_password()
    if host and password:
        return {
            "host": host,
            "port": int(os.getenv("ORCAST_DB_PORT", "5432")),
            "dbname": os.getenv("ORCAST_DB_NAME", "orcast_explore"),
            "user": os.getenv("ORCAST_DB_USER", "orcast"),
            "password": password,
            "connect_timeout": 5,
        }
    if settings.database_url.strip():
        return {"conninfo": settings.database_url, "connect_timeout": 5}
    raise RuntimeError("ORCAST_DATABASE_URL or ORCAST_DB_HOST/PASSWORD is not configured")


def aurora_connected() -> bool:
    if not aurora_configured():
        return False
    if psycopg is None:
        return False
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
        return True
    except Exception:
        return False


@contextmanager
def get_connection() -> Iterator["psycopg.Connection"]:
    if not aurora_configured():
        raise RuntimeError("ORCAST_DATABASE_URL is not configured")
    if psycopg is None:
        raise RuntimeError("psycopg is not installed")
    with psycopg.connect(**_connect_kwargs()) as conn:
        yield conn

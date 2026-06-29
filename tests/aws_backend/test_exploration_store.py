"""Tests for exploration session store (mocked Postgres)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.aws_backend.exploration.models import ExplorationTurn, GuideReply
from src.aws_backend.exploration.session_store import SessionStore


@pytest.fixture
def mock_conn():
    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value.__enter__ = MagicMock(return_value=cursor)
    conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    cursor.fetchone.return_value = (1,)
    cursor.fetchall.return_value = []
    return conn, cursor


@patch("src.aws_backend.exploration.session_store.get_connection")
def test_create_session(mock_get_connection, mock_conn):
    conn, cursor = mock_conn
    mock_get_connection.return_value.__enter__ = MagicMock(return_value=conn)
    mock_get_connection.return_value.__exit__ = MagicMock(return_value=False)

    store = SessionStore()
    session_id = store.create_session(title="test", client_ip="127.0.0.1")
    assert len(session_id) == 36
    assert cursor.execute.called


@patch("src.aws_backend.exploration.session_store.get_connection")
def test_save_exchange(mock_get_connection, mock_conn):
    conn, cursor = mock_conn
    mock_get_connection.return_value.__enter__ = MagicMock(return_value=conn)
    mock_get_connection.return_value.__exit__ = MagicMock(return_value=False)

    store = SessionStore()
    guide = GuideReply(
        reply="hello",
        citations=[{"label": "Gates", "href": "/gates"}],
        deep_links=[{"label": "Gates", "href": "/gates"}],
        source="template",
        model=None,
        tools_used=["fetch_gates"],
    )
    store.save_exchange("00000000-0000-0000-0000-000000000001", "question?", guide)
    assert cursor.execute.call_count >= 2


@patch("src.aws_backend.exploration.db.aurora_configured", return_value=False)
def test_exploration_status_disabled(mock_configured):
    from src.aws_backend.exploration.session_store import exploration_status

    status = exploration_status()
    assert status["aurora_enabled"] is False
    assert status["aurora_connected"] is False

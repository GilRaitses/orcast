"""Tests for exploration abuse limits."""

from unittest.mock import MagicMock, patch

import pytest

from src.aws_backend.exploration.limits import ExploreLimitError, assert_session_quota, assert_turn_quota


@patch("src.aws_backend.exploration.limits.get_connection")
@patch("src.aws_backend.exploration.limits.settings")
def test_session_quota_blocks(mock_settings, mock_get_connection):
    mock_settings.explore_max_sessions_per_ip_day = 2
    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value.__enter__ = MagicMock(return_value=cursor)
    conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    cursor.fetchone.return_value = (2,)
    mock_get_connection.return_value.__enter__ = MagicMock(return_value=conn)
    mock_get_connection.return_value.__exit__ = MagicMock(return_value=False)

    with pytest.raises(ExploreLimitError) as exc:
        assert_session_quota("203.0.113.1")
    assert exc.value.code == "session_quota"


@patch("src.aws_backend.exploration.limits.get_connection")
@patch("src.aws_backend.exploration.limits.settings")
def test_turn_quota_blocks(mock_settings, mock_get_connection):
    mock_settings.explore_max_turns_per_session = 3
    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value.__enter__ = MagicMock(return_value=cursor)
    conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    cursor.fetchone.return_value = (3,)
    mock_get_connection.return_value.__enter__ = MagicMock(return_value=conn)
    mock_get_connection.return_value.__exit__ = MagicMock(return_value=False)

    with pytest.raises(ExploreLimitError) as exc:
        assert_turn_quota("00000000-0000-0000-0000-000000000001")
    assert exc.value.code == "turn_quota"

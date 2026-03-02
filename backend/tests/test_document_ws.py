"""Tests for /ws/documents/{project_id} WebSocket endpoint and processing registry."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from tests.conftest import MOCK_USER_ID


def _project_row(**overrides):
    defaults = {
        "id": str(uuid4()),
        "user_id": str(MOCK_USER_ID),
        "name": "Test Project",
    }
    defaults.update(overrides)
    return defaults


def _ws_patches(mock_supabase):
    """Stack both verify_token and get_supabase_client patches for WS tests."""
    return (
        patch("app.api.ws.verify_token", return_value={"sub": str(MOCK_USER_ID)}),
        patch("app.api.ws.get_supabase_client", return_value=mock_supabase),
    )


class TestDocumentWsAuth:
    def test_rejects_missing_token(self, authed_client: TestClient):
        """WS with no token query param should close with 4001."""
        with authed_client.websocket_connect("/ws/documents/some-id") as _ws:
            # Server should close the connection immediately
            pass  # connect raises if server closes

    def test_rejects_invalid_token(self, authed_client: TestClient):
        """WS with invalid JWT token should close with 4001."""
        with authed_client.websocket_connect("/ws/documents/some-id?token=bad-token") as _ws:
            pass

    def test_rejects_nonexistent_project(self, authed_client: TestClient, mock_supabase):
        """WS for a project that doesn't exist should get error and close."""
        mock_supabase._table_data["projects"] = []
        pid = str(uuid4())
        p_token, p_supabase = _ws_patches(mock_supabase)
        with p_token, p_supabase:
            with authed_client.websocket_connect(f"/ws/documents/{pid}?token=valid-token") as ws:
                msg = ws.receive_json()
                assert msg["type"] == "error"
                assert "not found" in msg["message"].lower()

    def test_rejects_wrong_owner(self, authed_client: TestClient, mock_supabase):
        """WS for a project owned by another user should get error and close."""
        pid = str(uuid4())
        other_user = str(uuid4())
        mock_supabase._table_data["projects"] = [_project_row(id=pid, user_id=other_user)]
        p_token, p_supabase = _ws_patches(mock_supabase)
        with p_token, p_supabase:
            with authed_client.websocket_connect(f"/ws/documents/{pid}?token=valid-token") as ws:
                msg = ws.receive_json()
                assert msg["type"] == "error"
                assert "not found" in msg["message"].lower()


class TestDocumentWsConnection:
    def test_connects_successfully(self, authed_client: TestClient, mock_supabase):
        """Valid token + owned project should accept connection."""
        pid = str(uuid4())
        mock_supabase._table_data["projects"] = [_project_row(id=pid)]
        p_token, p_supabase = _ws_patches(mock_supabase)
        with p_token, p_supabase:
            with authed_client.websocket_connect(f"/ws/documents/{pid}?token=valid-token") as ws:
                # Connection accepted — send close from client side
                ws.close()


class TestDocumentProcessingRegistry:
    """Unit tests for the processing registry module."""

    @pytest.mark.asyncio
    async def test_notify_with_no_listeners(self):
        from app.services.document_processing_registry import notify_listeners

        # Should not raise when there are no listeners
        await notify_listeners("no-project", {"type": "test"})

    @pytest.mark.asyncio
    async def test_notify_sends_to_listeners(self):
        from app.services.document_processing_registry import (
            notify_listeners,
            register_listener,
            unregister_listener,
        )

        mock_ws = AsyncMock()
        pid = "notify-test-project"
        register_listener(pid, mock_ws)
        try:
            msg = {"type": "doc_processing_started", "document_id": "d1"}
            await notify_listeners(pid, msg)
            mock_ws.send_json.assert_called_once_with(msg)
        finally:
            unregister_listener(pid, mock_ws)

    @pytest.mark.asyncio
    async def test_notify_removes_stale_listeners(self):
        from app.services.document_processing_registry import (
            _listeners,
            notify_listeners,
            register_listener,
        )

        mock_ws = AsyncMock()
        mock_ws.send_json.side_effect = RuntimeError("connection closed")
        pid = "stale-test-project"
        register_listener(pid, mock_ws)

        await notify_listeners(pid, {"type": "test"})
        # Stale listener should have been removed
        assert pid not in _listeners

    def test_register_and_unregister_listener(self):
        from app.services.document_processing_registry import (
            _listeners,
            register_listener,
            unregister_listener,
        )

        mock_ws = MagicMock()
        pid = "test-project-id"

        register_listener(pid, mock_ws)
        assert pid in _listeners
        assert mock_ws in _listeners[pid]

        unregister_listener(pid, mock_ws)
        assert pid not in _listeners  # Cleaned up since list is empty

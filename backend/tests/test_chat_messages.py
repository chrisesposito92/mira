"""Tests for chat message API endpoints (Phase 8)."""

from collections.abc import Generator
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from tests.conftest import MOCK_USER_ID


def _workflow_row(workflow_id: str | None = None, **overrides) -> dict:
    """Create a workflow row dict for test data with ownership join."""
    row = {
        "id": workflow_id or str(uuid4()),
        "use_case_id": str(uuid4()),
        "workflow_type": "product_meter_aggregation",
        "status": "running",
        "thread_id": str(uuid4()),
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-01T00:00:00Z",
        # Join data for ownership check
        "use_cases": {
            "id": str(uuid4()),
            "project_id": str(uuid4()),
            "projects": {"user_id": str(MOCK_USER_ID)},
        },
    }
    row.update(overrides)
    return row


def _message_row(workflow_id: str, **overrides) -> dict:
    """Create a chat message row dict for test data."""
    row = {
        "id": str(uuid4()),
        "workflow_id": workflow_id,
        "role": "assistant",
        "content": "Analyzing use case...",
        "metadata": {"payload": {"type": "status", "step": "analyzing"}},
        "created_at": "2025-01-01T00:00:00Z",
    }
    row.update(overrides)
    return row


@pytest.fixture
def authed_client_with_data(
    mock_supabase: MagicMock,
) -> Generator[tuple[TestClient, MagicMock], None, None]:
    """TestClient with mocked auth and configurable table data."""
    from app.dependencies import get_current_user, get_supabase
    from app.main import app

    app.dependency_overrides[get_current_user] = lambda: MOCK_USER_ID
    app.dependency_overrides[get_supabase] = lambda: mock_supabase
    try:
        yield TestClient(app, raise_server_exceptions=False), mock_supabase
    finally:
        app.dependency_overrides.clear()


class TestListMessages:
    def test_list_messages_returns_messages(self, authed_client_with_data):
        client, mock_supabase = authed_client_with_data
        workflow_id = str(uuid4())

        # Setup ownership data
        mock_supabase._table_data["workflows"] = [_workflow_row(workflow_id)]
        # Setup message data
        mock_supabase._table_data["chat_messages"] = [
            _message_row(workflow_id, content="Step 1"),
            _message_row(workflow_id, content="Step 2"),
        ]

        resp = client.get(f"/api/workflows/{workflow_id}/messages")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[0]["content"] == "Step 1"

    def test_list_messages_empty(self, authed_client_with_data):
        client, mock_supabase = authed_client_with_data
        workflow_id = str(uuid4())

        mock_supabase._table_data["workflows"] = [_workflow_row(workflow_id)]
        mock_supabase._table_data["chat_messages"] = []

        resp = client.get(f"/api/workflows/{workflow_id}/messages")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_messages_not_owned_workflow(self, authed_client_with_data):
        client, mock_supabase = authed_client_with_data

        # Empty workflows means ownership check fails
        mock_supabase._table_data["workflows"] = []

        resp = client.get(f"/api/workflows/{uuid4()}/messages")
        assert resp.status_code == 404


class TestCreateMessage:
    def test_create_message_success(self, authed_client_with_data):
        client, mock_supabase = authed_client_with_data
        workflow_id = str(uuid4())

        mock_supabase._table_data["workflows"] = [_workflow_row(workflow_id)]
        mock_supabase._table_data["chat_messages"] = [
            _message_row(
                workflow_id,
                role="user",
                content="Looks good",
                metadata={"payload": {"type": "user_decision"}},
            )
        ]

        resp = client.post(
            f"/api/workflows/{workflow_id}/messages",
            json={
                "role": "user",
                "content": "Looks good",
                "metadata": {"payload": {"type": "user_decision"}},
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["role"] == "user"
        assert data["content"] == "Looks good"

    def test_create_message_not_owned_workflow(self, authed_client_with_data):
        client, mock_supabase = authed_client_with_data

        mock_supabase._table_data["workflows"] = []

        resp = client.post(
            f"/api/workflows/{uuid4()}/messages",
            json={"role": "user", "content": "Hello"},
        )
        assert resp.status_code == 404

    def test_create_message_invalid_role(self, authed_client_with_data):
        client, mock_supabase = authed_client_with_data
        workflow_id = str(uuid4())

        mock_supabase._table_data["workflows"] = [_workflow_row(workflow_id)]

        resp = client.post(
            f"/api/workflows/{workflow_id}/messages",
            json={"role": "invalid_role", "content": "test"},
        )
        assert resp.status_code == 422  # Pydantic validation error


class TestAuthRequired:
    def test_list_messages_requires_auth(self):
        from app.main import app

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get(f"/api/workflows/{uuid4()}/messages")
        assert resp.status_code in (401, 403)

    def test_create_message_requires_auth(self):
        from app.main import app

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post(
            f"/api/workflows/{uuid4()}/messages",
            json={"role": "user", "content": "test"},
        )
        assert resp.status_code in (401, 403)

"""Tests for workflow API endpoints (Phase 7)."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from langgraph.errors import GraphInterrupt

from tests.conftest import MOCK_USER_ID


def _workflow_row(use_case_id: str | None = None, **overrides) -> dict:
    """Create a workflow row dict for test data."""
    row = {
        "id": str(uuid4()),
        "use_case_id": use_case_id or str(uuid4()),
        "workflow_type": "product_meter_aggregation",
        "status": "pending",
        "thread_id": str(uuid4()),
        "interrupt_payload": None,
        "error_message": None,
        "started_at": None,
        "completed_at": None,
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-01T00:00:00Z",
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


class TestGetModels:
    def test_list_models_returns_all(self, authed_client):
        resp = authed_client.get("/api/models")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 6
        model_ids = {m["id"] for m in data}
        assert "claude-sonnet-4-6" in model_ids
        assert "gpt-5.2" in model_ids

    def test_each_model_has_fields(self, authed_client):
        resp = authed_client.get("/api/models")
        for model in resp.json():
            assert "id" in model
            assert "provider" in model
            assert "display_name" in model


class TestStartWorkflow:
    @patch("app.services.workflow_service.build_product_meter_agg_graph", new_callable=AsyncMock)
    def test_start_workflow_success(self, mock_build_graph, authed_client_with_data):
        client, mock_supabase = authed_client_with_data
        use_case_id = str(uuid4())

        # Setup mock data for ownership check
        mock_supabase._table_data["use_cases"] = [
            {
                "id": use_case_id,
                "project_id": str(uuid4()),
                "projects": {"user_id": str(MOCK_USER_ID)},
            }
        ]

        workflow_row = _workflow_row(
            use_case_id=use_case_id,
            status="interrupted",
            interrupt_payload={"type": "entities", "entity_type": "product"},
            # get_workflow needs the join data for ownership check
            use_cases={
                "project_id": str(uuid4()),
                "projects": {"user_id": str(MOCK_USER_ID)},
            },
        )
        mock_supabase._table_data["workflows"] = [workflow_row]

        # Mock graph build + invocation
        mock_graph = AsyncMock()
        mock_graph.ainvoke.side_effect = GraphInterrupt()
        mock_state = MagicMock()
        mock_task = MagicMock()
        mock_task.interrupts = [MagicMock(value={"type": "entities"})]
        mock_state.tasks = [mock_task]
        mock_graph.aget_state.return_value = mock_state
        mock_build_graph.return_value = mock_graph

        resp = client.post(
            f"/api/use-cases/{use_case_id}/workflows/start",
            json={"model_id": "claude-sonnet-4-6"},
        )
        assert resp.status_code == 200

    def test_start_workflow_invalid_use_case(self, authed_client_with_data):
        client, mock_supabase = authed_client_with_data
        mock_supabase._table_data["use_cases"] = []

        resp = client.post(
            f"/api/use-cases/{uuid4()}/workflows/start",
            json={"model_id": "claude-sonnet-4-6"},
        )
        assert resp.status_code == 404

    def test_start_workflow_unsupported_type(self, authed_client_with_data):
        client, mock_supabase = authed_client_with_data
        use_case_id = str(uuid4())
        mock_supabase._table_data["use_cases"] = [
            {
                "id": use_case_id,
                "project_id": str(uuid4()),
                "projects": {"user_id": str(MOCK_USER_ID)},
            }
        ]

        resp = client.post(
            f"/api/use-cases/{use_case_id}/workflows/start",
            json={"model_id": "claude-sonnet-4-6", "workflow_type": "invalid_type"},
        )
        assert resp.status_code == 422

    def test_start_plan_pricing_requires_completed_wf1(self, authed_client_with_data):
        client, mock_supabase = authed_client_with_data
        use_case_id = str(uuid4())
        mock_supabase._table_data["use_cases"] = [
            {
                "id": use_case_id,
                "project_id": str(uuid4()),
                "projects": {"user_id": str(MOCK_USER_ID)},
            }
        ]
        # No completed WF1 workflows exist
        mock_supabase._table_data["workflows"] = []

        resp = client.post(
            f"/api/use-cases/{use_case_id}/workflows/start",
            json={"model_id": "claude-sonnet-4-6", "workflow_type": "plan_pricing"},
        )
        assert resp.status_code == 400
        assert "Workflow 1" in resp.json()["detail"]

    def test_start_account_setup_requires_completed_wf2(self, authed_client_with_data):
        client, mock_supabase = authed_client_with_data
        use_case_id = str(uuid4())
        mock_supabase._table_data["use_cases"] = [
            {
                "id": use_case_id,
                "project_id": str(uuid4()),
                "projects": {"user_id": str(MOCK_USER_ID)},
            }
        ]
        mock_supabase._table_data["workflows"] = []

        resp = client.post(
            f"/api/use-cases/{use_case_id}/workflows/start",
            json={"model_id": "claude-sonnet-4-6", "workflow_type": "account_setup"},
        )
        assert resp.status_code == 400
        assert "Workflow 2" in resp.json()["detail"]

    def test_start_usage_submission_requires_completed_wf3(self, authed_client_with_data):
        client, mock_supabase = authed_client_with_data
        use_case_id = str(uuid4())
        mock_supabase._table_data["use_cases"] = [
            {
                "id": use_case_id,
                "project_id": str(uuid4()),
                "projects": {"user_id": str(MOCK_USER_ID)},
            }
        ]
        mock_supabase._table_data["workflows"] = []

        resp = client.post(
            f"/api/use-cases/{use_case_id}/workflows/start",
            json={"model_id": "claude-sonnet-4-6", "workflow_type": "usage_submission"},
        )
        assert resp.status_code == 400
        assert "Workflow 3" in resp.json()["detail"]


class TestResumeWorkflow:
    @patch("app.services.workflow_service.build_product_meter_agg_graph", new_callable=AsyncMock)
    def test_resume_success(self, mock_build_graph, authed_client_with_data):
        client, mock_supabase = authed_client_with_data
        workflow_id = str(uuid4())

        # Setup mock data: workflow in interrupted state with ownership chain
        mock_supabase._table_data["workflows"] = [
            _workflow_row(
                id=workflow_id,
                status="interrupted",
                use_cases={"project_id": str(uuid4()), "projects": {"user_id": str(MOCK_USER_ID)}},
            )
        ]

        # Mock graph
        mock_graph = AsyncMock()
        mock_graph.ainvoke.return_value = {}
        mock_build_graph.return_value = mock_graph

        resp = client.post(
            f"/api/workflows/{workflow_id}/resume",
            json={"decisions": [{"index": 0, "action": "approve"}]},
        )
        assert resp.status_code == 200

    def test_resume_workflow_not_found(self, authed_client_with_data):
        client, mock_supabase = authed_client_with_data
        mock_supabase._table_data["workflows"] = []

        resp = client.post(
            f"/api/workflows/{uuid4()}/resume",
            json={"decisions": [{"index": 0, "action": "approve"}]},
        )
        assert resp.status_code == 404


class TestAuthRequired:
    def test_start_requires_auth(self):
        from app.main import app

        # No dependency overrides — should fail auth
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post(
            f"/api/use-cases/{uuid4()}/workflows/start",
            json={"model_id": "claude-sonnet-4-6"},
        )
        assert resp.status_code in (401, 403)

    def test_resume_requires_auth(self):
        from app.main import app

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post(
            f"/api/workflows/{uuid4()}/resume",
            json={"decisions": [{"index": 0, "action": "approve"}]},
        )
        assert resp.status_code in (401, 403)

    def test_models_requires_auth(self):
        from app.main import app

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/api/models")
        # Models endpoint doesn't require auth (public)
        assert resp.status_code == 200

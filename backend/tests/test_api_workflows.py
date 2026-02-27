"""Tests for /api/workflows endpoints (read-only)."""

from datetime import datetime
from uuid import uuid4

from tests.conftest import MOCK_USER_ID


def _use_case_row(**overrides):
    defaults = {
        "id": str(uuid4()),
        "project_id": str(uuid4()),
        "projects": {"user_id": str(MOCK_USER_ID)},
    }
    defaults.update(overrides)
    return defaults


def _workflow_row(**overrides):
    defaults = {
        "id": str(uuid4()),
        "use_case_id": str(uuid4()),
        "workflow_type": "product_meter_aggregation",
        "status": "pending",
        "thread_id": None,
        "interrupt_payload": None,
        "error_message": None,
        "started_at": None,
        "completed_at": None,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }
    defaults.update(overrides)
    return defaults


class TestListWorkflows:
    def test_list_success(self, authed_client, mock_supabase):
        ucid = str(uuid4())
        mock_supabase._table_data["use_cases"] = [_use_case_row(id=ucid)]
        mock_supabase._table_data["workflows"] = [_workflow_row(use_case_id=ucid)]
        resp = authed_client.get(f"/api/use-cases/{ucid}/workflows")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_list_empty(self, authed_client, mock_supabase):
        ucid = str(uuid4())
        mock_supabase._table_data["use_cases"] = [_use_case_row(id=ucid)]
        mock_supabase._table_data["workflows"] = []
        resp = authed_client.get(f"/api/use-cases/{ucid}/workflows")
        assert resp.status_code == 200
        assert resp.json() == []


class TestGetWorkflow:
    def test_get_success(self, authed_client, mock_supabase):
        wid = str(uuid4())
        row = _workflow_row(id=wid)
        row["use_cases"] = {
            "project_id": str(uuid4()),
            "projects": {"user_id": str(MOCK_USER_ID)},
        }
        mock_supabase._table_data["workflows"] = [row]
        resp = authed_client.get(f"/api/workflows/{wid}")
        assert resp.status_code == 200

    def test_get_not_found(self, authed_client, mock_supabase):
        mock_supabase._table_data["workflows"] = []
        resp = authed_client.get(f"/api/workflows/{uuid4()}")
        assert resp.status_code == 404

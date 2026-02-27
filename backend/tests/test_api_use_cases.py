"""Tests for /api/use-cases and /api/projects/{id}/use-cases endpoints."""

from datetime import datetime
from uuid import uuid4

from tests.conftest import MOCK_USER_ID


def _project_row(**overrides):
    defaults = {
        "id": str(uuid4()),
        "user_id": str(MOCK_USER_ID),
        "name": "Test Project",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }
    defaults.update(overrides)
    return defaults


def _use_case_row(**overrides):
    defaults = {
        "id": str(uuid4()),
        "project_id": str(uuid4()),
        "title": "Test Use Case",
        "description": None,
        "status": "draft",
        "contract_start_date": None,
        "billing_frequency": None,
        "currency": "USD",
        "target_billing_model": None,
        "notes": None,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }
    defaults.update(overrides)
    return defaults


class TestCreateUseCase:
    def test_create_success(self, authed_client, mock_supabase):
        pid = str(uuid4())
        # Project lookup for ownership check
        mock_supabase._table_data["projects"] = [_project_row(id=pid)]
        mock_supabase._table_data["use_cases"] = [_use_case_row(project_id=pid)]
        resp = authed_client.post(f"/api/projects/{pid}/use-cases", json={"title": "New Use Case"})
        assert resp.status_code == 201


class TestListUseCases:
    def test_list_success(self, authed_client, mock_supabase):
        pid = str(uuid4())
        mock_supabase._table_data["projects"] = [_project_row(id=pid)]
        mock_supabase._table_data["use_cases"] = [
            _use_case_row(project_id=pid),
            _use_case_row(project_id=pid),
        ]
        resp = authed_client.get(f"/api/projects/{pid}/use-cases")
        assert resp.status_code == 200
        assert len(resp.json()) == 2


class TestGetUseCase:
    def test_get_success(self, authed_client, mock_supabase):
        ucid = str(uuid4())
        row = _use_case_row(id=ucid)
        row["projects"] = {"user_id": str(MOCK_USER_ID)}
        mock_supabase._table_data["use_cases"] = [row]
        resp = authed_client.get(f"/api/use-cases/{ucid}")
        assert resp.status_code == 200

    def test_get_not_found(self, authed_client, mock_supabase):
        mock_supabase._table_data["use_cases"] = []
        resp = authed_client.get(f"/api/use-cases/{uuid4()}")
        assert resp.status_code == 404


class TestUpdateUseCase:
    def test_update_success(self, authed_client, mock_supabase):
        ucid = str(uuid4())
        row = _use_case_row(id=ucid)
        row["projects"] = {"user_id": str(MOCK_USER_ID)}
        mock_supabase._table_data["use_cases"] = [row]
        resp = authed_client.patch(f"/api/use-cases/{ucid}", json={"title": "Updated Title"})
        assert resp.status_code == 200


class TestDeleteUseCase:
    def test_delete_success(self, authed_client, mock_supabase):
        ucid = str(uuid4())
        row = _use_case_row(id=ucid)
        row["projects"] = {"user_id": str(MOCK_USER_ID)}
        mock_supabase._table_data["use_cases"] = [row]
        resp = authed_client.delete(f"/api/use-cases/{ucid}")
        assert resp.status_code == 204

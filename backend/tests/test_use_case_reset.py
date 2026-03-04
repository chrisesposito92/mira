"""Tests for POST /api/use-cases/{id}/reset endpoint."""

from datetime import datetime
from uuid import uuid4

from tests.conftest import MOCK_USER_ID

_OTHER_USER_ID = "99999999-8888-7777-6666-555555555555"


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


class TestResetUseCase:
    def test_reset_success(self, authed_client, mock_supabase):
        ucid = str(uuid4())
        row = _use_case_row(id=ucid)
        row["projects"] = {"user_id": str(MOCK_USER_ID)}
        mock_supabase._table_data["use_cases"] = [row]
        mock_supabase._table_data["generated_objects"] = [
            {"id": str(uuid4())},
            {"id": str(uuid4())},
        ]
        mock_supabase._table_data["workflows"] = []

        resp = authed_client.post(f"/api/use-cases/{ucid}/reset")
        assert resp.status_code == 200
        body = resp.json()
        assert "message" in body
        assert "objects" in body["message"]
        assert "workflows" in body["message"]

    def test_reset_not_found(self, authed_client, mock_supabase):
        mock_supabase._table_data["use_cases"] = []
        resp = authed_client.post(f"/api/use-cases/{uuid4()}/reset")
        assert resp.status_code == 404

    def test_reset_wrong_owner(self, authed_client, mock_supabase):
        ucid = str(uuid4())
        row = _use_case_row(id=ucid)
        row["projects"] = {"user_id": _OTHER_USER_ID}
        mock_supabase._table_data["use_cases"] = [row]

        resp = authed_client.post(f"/api/use-cases/{ucid}/reset")
        assert resp.status_code == 404

    def test_reset_blocked_by_active_workflow(self, authed_client, mock_supabase):
        ucid = str(uuid4())
        row = _use_case_row(id=ucid)
        row["projects"] = {"user_id": str(MOCK_USER_ID)}
        mock_supabase._table_data["use_cases"] = [row]
        mock_supabase._table_data["workflows"] = [
            {"id": str(uuid4()), "status": "running"},
        ]

        resp = authed_client.post(f"/api/use-cases/{ucid}/reset")
        assert resp.status_code == 409
        assert "active" in resp.json()["detail"].lower()

    def test_reset_empty_data(self, authed_client, mock_supabase):
        ucid = str(uuid4())
        row = _use_case_row(id=ucid)
        row["projects"] = {"user_id": str(MOCK_USER_ID)}
        mock_supabase._table_data["use_cases"] = [row]
        mock_supabase._table_data["generated_objects"] = []
        mock_supabase._table_data["workflows"] = []

        resp = authed_client.post(f"/api/use-cases/{ucid}/reset")
        assert resp.status_code == 200
        body = resp.json()
        assert "0 objects" in body["message"]
        assert "0 workflows" in body["message"]

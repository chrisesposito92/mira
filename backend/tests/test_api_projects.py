"""Tests for /api/projects endpoints."""

from datetime import datetime
from uuid import uuid4

from tests.conftest import MOCK_USER_ID


def _project_row(**overrides):
    defaults = {
        "id": str(uuid4()),
        "user_id": str(MOCK_USER_ID),
        "name": "Test Project",
        "customer_name": None,
        "description": None,
        "org_connection_id": None,
        "default_model_id": None,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }
    defaults.update(overrides)
    return defaults


class TestCreateProject:
    def test_create_success(self, authed_client, mock_supabase):
        row = _project_row(name="New Project")
        mock_supabase._table_data["projects"] = [row]
        resp = authed_client.post("/api/projects", json={"name": "New Project"})
        assert resp.status_code == 201
        assert resp.json()["name"] == "New Project"

    def test_create_missing_name(self, authed_client):
        resp = authed_client.post("/api/projects", json={})
        assert resp.status_code == 422


class TestListProjects:
    def test_list_empty(self, authed_client, mock_supabase):
        mock_supabase._table_data["projects"] = []
        resp = authed_client.get("/api/projects")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_with_data(self, authed_client, mock_supabase):
        mock_supabase._table_data["projects"] = [_project_row(), _project_row()]
        resp = authed_client.get("/api/projects")
        assert resp.status_code == 200
        assert len(resp.json()) == 2


class TestGetProject:
    def test_get_success(self, authed_client, mock_supabase):
        pid = str(uuid4())
        mock_supabase._table_data["projects"] = [_project_row(id=pid)]
        resp = authed_client.get(f"/api/projects/{pid}")
        assert resp.status_code == 200

    def test_get_not_found(self, authed_client, mock_supabase):
        mock_supabase._table_data["projects"] = []
        resp = authed_client.get(f"/api/projects/{uuid4()}")
        assert resp.status_code == 404


class TestUpdateProject:
    def test_update_success(self, authed_client, mock_supabase):
        pid = str(uuid4())
        row = _project_row(id=pid)
        mock_supabase._table_data["projects"] = [row]
        resp = authed_client.patch(f"/api/projects/{pid}", json={"name": "Updated"})
        assert resp.status_code == 200


class TestDeleteProject:
    def test_delete_success(self, authed_client, mock_supabase):
        pid = str(uuid4())
        mock_supabase._table_data["projects"] = [_project_row(id=pid)]
        resp = authed_client.delete(f"/api/projects/{pid}")
        assert resp.status_code == 204


class TestProjectNoAuth:
    def test_no_auth(self):
        from fastapi.testclient import TestClient

        from app.main import app

        app.dependency_overrides.clear()
        try:
            client = TestClient(app, raise_server_exceptions=False)
            resp = client.get("/api/projects")
            assert resp.status_code in (401, 403)
        finally:
            app.dependency_overrides.clear()

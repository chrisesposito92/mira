"""Tests for /api/diagrams endpoints."""

from datetime import datetime
from uuid import uuid4

from tests.conftest import MOCK_USER_ID


def _diagram_row(**overrides):
    defaults = {
        "id": str(uuid4()),
        "user_id": str(MOCK_USER_ID),
        "customer_name": "Acme Corp",
        "title": "",
        "project_id": None,
        "content": {"systems": [], "connections": [], "settings": {}},
        "schema_version": 1,
        "thumbnail_base64": None,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }
    defaults.update(overrides)
    return defaults


def _diagram_list_row(**overrides):
    """Row for list queries -- excludes content but includes thumbnail_base64."""
    defaults = {
        "id": str(uuid4()),
        "user_id": str(MOCK_USER_ID),
        "customer_name": "Acme Corp",
        "title": "",
        "project_id": None,
        "schema_version": 1,
        "thumbnail_base64": None,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }
    defaults.update(overrides)
    return defaults


class TestCreateDiagram:
    def test_create_success(self, authed_client, mock_supabase):
        row = _diagram_row(customer_name="Test Corp")
        mock_supabase._table_data["diagrams"] = [row]
        resp = authed_client.post("/api/diagrams", json={"customer_name": "Test Corp"})
        assert resp.status_code == 201
        assert resp.json()["customer_name"] == "Test Corp"

    def test_create_missing_name(self, authed_client):
        resp = authed_client.post("/api/diagrams", json={})
        assert resp.status_code == 422

    def test_create_with_project_id(self, authed_client, mock_supabase):
        pid = str(uuid4())
        row = _diagram_row(project_id=pid)
        mock_supabase._table_data["diagrams"] = [row]
        # Project must exist and belong to user for ownership check
        mock_supabase._table_data["projects"] = [{"id": pid, "user_id": str(MOCK_USER_ID)}]
        resp = authed_client.post(
            "/api/diagrams",
            json={"customer_name": "Acme", "project_id": pid},
        )
        assert resp.status_code == 201
        assert resp.json()["project_id"] == pid

    def test_create_with_foreign_project_id(self, authed_client, mock_supabase):
        """Creating a diagram with another user's project_id should fail."""
        pid = str(uuid4())
        mock_supabase._table_data["diagrams"] = [_diagram_row()]
        mock_supabase._table_data["projects"] = []  # Project not found for this user
        resp = authed_client.post(
            "/api/diagrams",
            json={"customer_name": "Acme", "project_id": pid},
        )
        assert resp.status_code == 404

    def test_schema_version(self, authed_client, mock_supabase):
        row = _diagram_row()
        mock_supabase._table_data["diagrams"] = [row]
        resp = authed_client.post("/api/diagrams", json={"customer_name": "Acme"})
        assert resp.status_code == 201
        assert resp.json()["schema_version"] == 1


class TestListDiagrams:
    def test_list_empty(self, authed_client, mock_supabase):
        mock_supabase._table_data["diagrams"] = []
        resp = authed_client.get("/api/diagrams")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_with_data(self, authed_client, mock_supabase):
        mock_supabase._table_data["diagrams"] = [
            _diagram_list_row(),
            _diagram_list_row(),
        ]
        resp = authed_client.get("/api/diagrams")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_list_excludes_content(self, authed_client, mock_supabase):
        """List response should NOT contain content but SHOULD include thumbnail_base64."""
        mock_supabase._table_data["diagrams"] = [_diagram_list_row()]
        resp = authed_client.get("/api/diagrams")
        assert resp.status_code == 200
        item = resp.json()[0]
        assert "content" not in item
        assert item.get("thumbnail_base64") is None

    def test_list_includes_thumbnail(self, authed_client, mock_supabase):
        """List response should include thumbnail_base64 when present."""
        mock_supabase._table_data["diagrams"] = [
            _diagram_list_row(thumbnail_base64="data:image/png;base64,AAAA")
        ]
        resp = authed_client.get("/api/diagrams")
        assert resp.status_code == 200
        assert resp.json()[0]["thumbnail_base64"] == "data:image/png;base64,AAAA"


class TestGetDiagram:
    def test_get_success(self, authed_client, mock_supabase):
        did = str(uuid4())
        mock_supabase._table_data["diagrams"] = [_diagram_row(id=did)]
        resp = authed_client.get(f"/api/diagrams/{did}")
        assert resp.status_code == 200

    def test_get_not_found(self, authed_client, mock_supabase):
        mock_supabase._table_data["diagrams"] = []
        resp = authed_client.get(f"/api/diagrams/{uuid4()}")
        assert resp.status_code == 404


class TestUpdateDiagram:
    """Tests for PATCH /api/diagrams/{id}.
    Addresses review concern: both reviewers flagged missing update endpoint.
    """

    def test_update_customer_name(self, authed_client, mock_supabase):
        did = str(uuid4())
        updated_row = _diagram_row(id=did, customer_name="Updated Corp")
        mock_supabase._table_data["diagrams"] = [updated_row]
        resp = authed_client.patch(
            f"/api/diagrams/{did}",
            json={"customer_name": "Updated Corp"},
        )
        assert resp.status_code == 200
        assert resp.json()["customer_name"] == "Updated Corp"

    def test_update_not_found(self, authed_client, mock_supabase):
        mock_supabase._table_data["diagrams"] = []
        resp = authed_client.patch(
            f"/api/diagrams/{uuid4()}",
            json={"customer_name": "New Name"},
        )
        assert resp.status_code == 404

    def test_update_content(self, authed_client, mock_supabase):
        did = str(uuid4())
        new_content = {
            "systems": [{"id": "sys-1", "name": "Test System", "x": 100, "y": 200}],
            "connections": [],
            "settings": {"background_color": "#1a1f36", "show_labels": True},
        }
        updated_row = _diagram_row(id=did, content=new_content)
        mock_supabase._table_data["diagrams"] = [updated_row]
        resp = authed_client.patch(
            f"/api/diagrams/{did}",
            json={"content": new_content},
        )
        assert resp.status_code == 200
        assert len(resp.json()["content"]["systems"]) == 1


class TestDeleteDiagram:
    def test_delete_success(self, authed_client, mock_supabase):
        did = str(uuid4())
        mock_supabase._table_data["diagrams"] = [_diagram_row(id=did)]
        resp = authed_client.delete(f"/api/diagrams/{did}")
        assert resp.status_code == 204

"""Tests for /api/org-connections endpoints."""

from datetime import datetime
from uuid import uuid4

from tests.conftest import MOCK_USER_ID


def _conn_row(**overrides):
    defaults = {
        "id": str(uuid4()),
        "user_id": str(MOCK_USER_ID),
        "org_id": "org-abc",
        "org_name": "Test Org",
        "api_url": "https://api.m3ter.com",
        "encrypted_client_id": "enc_cid",
        "encrypted_client_secret": "enc_csec",
        "status": "untested",
        "last_tested_at": None,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }
    defaults.update(overrides)
    return defaults


class TestCreateOrgConnection:
    def test_create_success(self, authed_client, mock_supabase, fernet_key):
        row = _conn_row()
        mock_supabase._table_data["org_connections"] = [row]
        resp = authed_client.post(
            "/api/org-connections",
            json={
                "org_id": "org-abc",
                "org_name": "Test Org",
                "client_id": "cid-123",
                "client_secret": "csec-456",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        # client_secret and encrypted fields should NOT be in response
        assert "client_secret" not in data
        assert "encrypted_client_id" not in data
        assert "encrypted_client_secret" not in data


class TestListOrgConnections:
    def test_list_strips_secrets(self, authed_client, mock_supabase):
        mock_supabase._table_data["org_connections"] = [_conn_row()]
        resp = authed_client.get("/api/org-connections")
        assert resp.status_code == 200
        for item in resp.json():
            assert "encrypted_client_id" not in item
            assert "encrypted_client_secret" not in item


class TestGetOrgConnection:
    def test_get_success(self, authed_client, mock_supabase):
        cid = str(uuid4())
        mock_supabase._table_data["org_connections"] = [_conn_row(id=cid)]
        resp = authed_client.get(f"/api/org-connections/{cid}")
        assert resp.status_code == 200

    def test_get_not_found(self, authed_client, mock_supabase):
        mock_supabase._table_data["org_connections"] = []
        resp = authed_client.get(f"/api/org-connections/{uuid4()}")
        assert resp.status_code == 404


class TestUpdateOrgConnection:
    def test_update_success(self, authed_client, mock_supabase, fernet_key):
        cid = str(uuid4())
        mock_supabase._table_data["org_connections"] = [_conn_row(id=cid)]
        resp = authed_client.patch(f"/api/org-connections/{cid}", json={"org_name": "Updated Org"})
        assert resp.status_code == 200


class TestDeleteOrgConnection:
    def test_delete_success(self, authed_client, mock_supabase):
        cid = str(uuid4())
        mock_supabase._table_data["org_connections"] = [_conn_row(id=cid)]
        resp = authed_client.delete(f"/api/org-connections/{cid}")
        assert resp.status_code == 204

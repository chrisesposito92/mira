"""Tests for /api/objects and /api/use-cases/{id}/objects endpoints."""

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


def _object_row(**overrides):
    defaults = {
        "id": str(uuid4()),
        "use_case_id": str(uuid4()),
        "entity_type": "product",
        "name": "Test Product",
        "code": "test-product",
        "status": "draft",
        "data": {"key": "value"},
        "m3ter_id": None,
        "depends_on": None,
        "validation_errors": None,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }
    defaults.update(overrides)
    return defaults


class TestListObjects:
    def test_list_success(self, authed_client, mock_supabase):
        ucid = str(uuid4())
        mock_supabase._table_data["use_cases"] = [_use_case_row(id=ucid)]
        mock_supabase._table_data["generated_objects"] = [
            _object_row(use_case_id=ucid),
        ]
        resp = authed_client.get(f"/api/use-cases/{ucid}/objects")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_list_with_filters(self, authed_client, mock_supabase):
        ucid = str(uuid4())
        mock_supabase._table_data["use_cases"] = [_use_case_row(id=ucid)]
        mock_supabase._table_data["generated_objects"] = [
            _object_row(use_case_id=ucid, entity_type="meter"),
        ]
        resp = authed_client.get(f"/api/use-cases/{ucid}/objects?entity_type=meter&status=draft")
        assert resp.status_code == 200


class TestGetObject:
    def test_get_success(self, authed_client, mock_supabase):
        oid = str(uuid4())
        row = _object_row(id=oid)
        row["use_cases"] = {"project_id": str(uuid4()), "projects": {"user_id": str(MOCK_USER_ID)}}
        mock_supabase._table_data["generated_objects"] = [row]
        resp = authed_client.get(f"/api/objects/{oid}")
        assert resp.status_code == 200

    def test_get_not_found(self, authed_client, mock_supabase):
        mock_supabase._table_data["generated_objects"] = []
        resp = authed_client.get(f"/api/objects/{uuid4()}")
        assert resp.status_code == 404


class TestUpdateObject:
    def test_update_status(self, authed_client, mock_supabase):
        oid = str(uuid4())
        row = _object_row(id=oid)
        row["use_cases"] = {"project_id": str(uuid4()), "projects": {"user_id": str(MOCK_USER_ID)}}
        mock_supabase._table_data["generated_objects"] = [row]
        resp = authed_client.patch(f"/api/objects/{oid}", json={"status": "approved"})
        assert resp.status_code == 200


class TestBulkUpdate:
    def test_bulk_success(self, authed_client, mock_supabase):
        oid1, oid2 = str(uuid4()), str(uuid4())
        row1 = _object_row(id=oid1)
        row1["use_cases"] = {
            "project_id": str(uuid4()),
            "projects": {"user_id": str(MOCK_USER_ID)},
        }
        row2 = _object_row(id=oid2)
        row2["use_cases"] = {
            "project_id": str(uuid4()),
            "projects": {"user_id": str(MOCK_USER_ID)},
        }
        mock_supabase._table_data["generated_objects"] = [row1, row2]
        resp = authed_client.post(
            "/api/objects/bulk-status",
            json={"ids": [oid1, oid2], "status": "approved"},
        )
        assert resp.status_code == 200
        assert "2 objects" in resp.json()["message"]


class TestCreateObject:
    def test_create_success(self, authed_client, mock_supabase):
        ucid = str(uuid4())
        mock_supabase._table_data["use_cases"] = [_use_case_row(id=ucid)]
        mock_supabase._table_data["generated_objects"] = [
            _object_row(use_case_id=ucid, status="draft", validation_errors=[]),
        ]
        resp = authed_client.post(
            f"/api/use-cases/{ucid}/objects",
            json={
                "entity_type": "product",
                "name": "My Product",
                "code": "my_product",
                "data": {
                    "name": "My Product",
                    "code": "my_product",
                    "customFields": {},
                },
            },
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["status"] == "draft"
        assert body["entity_type"] == "product"

    def test_create_with_validation_errors(self, authed_client, mock_supabase):
        ucid = str(uuid4())
        mock_supabase._table_data["use_cases"] = [_use_case_row(id=ucid)]
        mock_supabase._table_data["generated_objects"] = [
            _object_row(
                use_case_id=ucid,
                status="draft",
                validation_errors=[
                    {
                        "field": "name",
                        "message": "Name is required",
                        "severity": "error",
                    }
                ],
            ),
        ]
        resp = authed_client.post(
            f"/api/use-cases/{ucid}/objects",
            json={"entity_type": "product", "data": {}},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["validation_errors"] is not None

    def test_create_requires_ownership(self, authed_client, mock_supabase):
        ucid = str(uuid4())
        mock_supabase._table_data["use_cases"] = []  # No matching use case
        resp = authed_client.post(
            f"/api/use-cases/{ucid}/objects",
            json={"entity_type": "product", "name": "Test"},
        )
        assert resp.status_code == 404


class TestGetTemplates:
    def test_templates_returns_all_entity_types(self, authed_client, mock_supabase):
        resp = authed_client.get("/api/objects/templates")
        assert resp.status_code == 200
        body = resp.json()
        # Should have templates for all entity types that have schemas
        assert "product" in body
        assert "meter" in body
        assert "aggregation" in body
        assert "plan_template" in body
        assert "plan" in body
        assert "pricing" in body
        assert "account" in body
        assert "account_plan" in body
        assert "measurement" in body

    def test_product_template_has_required_fields(self, authed_client, mock_supabase):
        resp = authed_client.get("/api/objects/templates")
        body = resp.json()
        product = body["product"]
        assert "name" in product
        assert "code" in product

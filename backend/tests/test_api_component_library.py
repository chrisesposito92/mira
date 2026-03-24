"""Tests for /api/component-library endpoints."""

from datetime import datetime
from uuid import uuid4


def _component_row(**overrides):
    defaults = {
        "id": str(uuid4()),
        "slug": "stripe",
        "name": "Stripe",
        "domain": "stripe.com",
        "category": "Billing/Payments",
        "logo_base64": None,
        "is_native_connector": True,
        "display_order": 20,
        "created_at": datetime.now().isoformat(),
    }
    defaults.update(overrides)
    return defaults


class TestListComponents:
    def test_list_success(self, authed_client, mock_supabase):
        mock_supabase._table_data["component_library"] = [
            _component_row(),
            _component_row(
                slug="snowflake",
                name="Snowflake",
                category="Analytics",
                is_native_connector=False,
            ),
        ]
        resp = authed_client.get("/api/component-library")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_categories(self, authed_client, mock_supabase):
        mock_supabase._table_data["component_library"] = [
            _component_row(category="CRM"),
        ]
        resp = authed_client.get("/api/component-library")
        assert resp.status_code == 200
        assert resp.json()[0]["category"] == "CRM"

    def test_native_connector_flag(self, authed_client, mock_supabase):
        mock_supabase._table_data["component_library"] = [
            _component_row(is_native_connector=True),
        ]
        resp = authed_client.get("/api/component-library")
        assert resp.status_code == 200
        assert resp.json()[0]["is_native_connector"] is True

    def test_slug_in_response(self, authed_client, mock_supabase):
        mock_supabase._table_data["component_library"] = [
            _component_row(slug="salesforce"),
        ]
        resp = authed_client.get("/api/component-library")
        assert resp.status_code == 200
        assert resp.json()[0]["slug"] == "salesforce"


class TestGetComponent:
    def test_get_success(self, authed_client, mock_supabase):
        cid = str(uuid4())
        mock_supabase._table_data["component_library"] = [_component_row(id=cid)]
        resp = authed_client.get(f"/api/component-library/{cid}")
        assert resp.status_code == 200

    def test_not_found(self, authed_client, mock_supabase):
        mock_supabase._table_data["component_library"] = []
        resp = authed_client.get(f"/api/component-library/{uuid4()}")
        assert resp.status_code == 404

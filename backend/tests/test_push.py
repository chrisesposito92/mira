"""Tests for Phase 12: m3ter Push & Sync Integration."""

import time
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import httpx
import pytest

from tests.conftest import MOCK_USER_ID

# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────


def _use_case_row(**overrides):
    defaults = {
        "id": str(uuid4()),
        "project_id": str(uuid4()),
        "projects": {
            "user_id": str(MOCK_USER_ID),
            "org_connection_id": str(uuid4()),
        },
    }
    defaults.update(overrides)
    return defaults


def _object_row(**overrides):
    defaults = {
        "id": str(uuid4()),
        "use_case_id": str(uuid4()),
        "entity_type": "product",
        "name": "Test Product",
        "code": "test_product",
        "status": "approved",
        "data": {"name": "Test Product", "code": "test_product", "customFields": {}},
        "m3ter_id": None,
        "depends_on": None,
        "validation_errors": None,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }
    defaults.update(overrides)
    return defaults


def _org_connection_row(**overrides):
    defaults = {
        "id": str(uuid4()),
        "org_id": "test-org-id",
        "api_url": "https://api.m3ter.com",
        "client_id": "encrypted_client_id",
        "client_secret": "encrypted_client_secret",
    }
    defaults.update(overrides)
    return defaults


# ─────────────────────────────────────────────────────────────
# Part 1: M3terClient Tests
# ─────────────────────────────────────────────────────────────


class TestM3terClientTokenCaching:
    """Test token cache: fresh call, cached reuse, expired refresh."""

    @pytest.fixture(autouse=True)
    def clear_cache(self):
        """Clear the class-level token cache between tests."""
        from app.m3ter.client import M3terClient

        M3terClient._token_cache.clear()
        yield
        M3terClient._token_cache.clear()

    @pytest.mark.asyncio
    async def test_fresh_token_fetched(self):
        """First call should fetch a new token from the auth endpoint."""
        from app.m3ter.client import M3terClient

        client = M3terClient("org1", "https://api.m3ter.com", "cid", "csecret")

        mock_response = MagicMock()
        mock_response.json.return_value = {"access_token": "fresh-token-123"}
        mock_response.raise_for_status = MagicMock()

        with patch.object(client, "_get_client") as mock_get:
            mock_http = AsyncMock()
            mock_http.post.return_value = mock_response
            mock_get.return_value = mock_http

            token = await client.authenticate()

        assert token == "fresh-token-123"
        assert client._token == "fresh-token-123"

    @pytest.mark.asyncio
    async def test_cached_token_reused(self):
        """Second call should return cached token without HTTP call."""
        from app.m3ter.client import M3terClient

        client = M3terClient("org1", "https://api.m3ter.com", "cid", "csecret")

        # Manually seed the cache
        M3terClient._token_cache[("cid", "csecret")] = (
            "cached-token",
            time.monotonic() + 10000,
        )

        token = await client.authenticate()
        assert token == "cached-token"

    @pytest.mark.asyncio
    async def test_expired_token_refreshed(self):
        """Expired token should trigger a fresh fetch."""
        from app.m3ter.client import M3terClient

        client = M3terClient("org1", "https://api.m3ter.com", "cid", "csecret")

        # Seed with expired entry
        M3terClient._token_cache[("cid", "csecret")] = (
            "expired-token",
            time.monotonic() - 1,
        )

        mock_response = MagicMock()
        mock_response.json.return_value = {"access_token": "new-token"}
        mock_response.raise_for_status = MagicMock()

        with patch.object(client, "_get_client") as mock_get:
            mock_http = AsyncMock()
            mock_http.post.return_value = mock_response
            mock_get.return_value = mock_http

            token = await client.authenticate()

        assert token == "new-token"


class TestM3terClientRetryLogic:
    """Test retry behavior for Config API requests."""

    @pytest.fixture(autouse=True)
    def clear_cache(self):
        from app.m3ter.client import M3terClient

        M3terClient._token_cache.clear()
        yield
        M3terClient._token_cache.clear()

    @pytest.mark.asyncio
    async def test_retryable_status_triggers_retry(self):
        """429/5xx should trigger retries with backoff."""
        from app.m3ter.client import M3terClient

        client = M3terClient("org1", "https://api.m3ter.com", "cid", "csecret")

        # Seed token cache
        M3terClient._token_cache[("cid", "csecret")] = (
            "token",
            time.monotonic() + 10000,
        )

        # First two calls return 503, third succeeds
        fail_response = MagicMock()
        fail_response.status_code = 503
        fail_response.raise_for_status = MagicMock(
            side_effect=httpx.HTTPStatusError("503", request=MagicMock(), response=fail_response)
        )

        ok_response = MagicMock()
        ok_response.status_code = 200
        ok_response.raise_for_status = MagicMock()
        ok_response.json.return_value = {"id": "created-123"}

        with patch.object(client, "_get_client") as mock_get:
            mock_http = AsyncMock()
            mock_http.request = AsyncMock(side_effect=[fail_response, fail_response, ok_response])
            mock_get.return_value = mock_http

            with patch("app.m3ter.client.asyncio.sleep", new_callable=AsyncMock):
                result = await client._config_api_request(
                    "POST", "/organizations/org1/products", {"name": "Test"}
                )

        assert result == {"id": "created-123"}
        assert mock_http.request.call_count == 3

    @pytest.mark.asyncio
    async def test_non_retryable_status_raises_immediately(self):
        """400/404 should raise immediately without retry."""
        from app.m3ter.client import M3terClient

        client = M3terClient("org1", "https://api.m3ter.com", "cid", "csecret")

        M3terClient._token_cache[("cid", "csecret")] = (
            "token",
            time.monotonic() + 10000,
        )

        fail_response = MagicMock()
        fail_response.status_code = 400
        fail_response.raise_for_status = MagicMock(
            side_effect=httpx.HTTPStatusError("400", request=MagicMock(), response=fail_response)
        )

        with patch.object(client, "_get_client") as mock_get:
            mock_http = AsyncMock()
            mock_http.request = AsyncMock(return_value=fail_response)
            mock_get.return_value = mock_http

            with pytest.raises(httpx.HTTPStatusError):
                await client._config_api_request(
                    "POST", "/organizations/org1/products", {"name": "Test"}
                )

        # Should only have been called once (no retry)
        assert mock_http.request.call_count == 1


class TestM3terClientEntityMethods:
    """Test per-entity CRUD methods delegate to _config_api_request."""

    @pytest.fixture(autouse=True)
    def clear_cache(self):
        from app.m3ter.client import M3terClient

        M3terClient._token_cache.clear()
        yield
        M3terClient._token_cache.clear()

    @pytest.mark.asyncio
    async def test_create_product(self):
        from app.m3ter.client import M3terClient

        client = M3terClient("org1", "https://api.m3ter.com", "cid", "csecret")

        with patch.object(client, "_config_api_request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = {"id": "prod-123"}
            result = await client.create_product({"name": "Test"})

        assert result == {"id": "prod-123"}
        mock_req.assert_called_once_with("POST", "/organizations/org1/products", {"name": "Test"})

    @pytest.mark.asyncio
    async def test_create_pricing_uses_plan_id_in_path(self):
        from app.m3ter.client import M3terClient

        client = M3terClient("org1", "https://api.m3ter.com", "cid", "csecret")

        with patch.object(client, "_config_api_request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = {"id": "pricing-123"}
            result = await client.create_pricing("plan-456", {"startDate": "2024-01-01"})

        assert result == {"id": "pricing-123"}
        mock_req.assert_called_once_with(
            "POST",
            "/organizations/org1/plans/plan-456/pricing",
            {"startDate": "2024-01-01"},
        )

    @pytest.mark.asyncio
    async def test_submit_measurements_uses_ingest_api(self):
        from app.m3ter.client import M3terClient

        client = M3terClient("org1", "https://api.m3ter.com", "cid", "csecret")

        with patch.object(client, "_ingest_api_post", new_callable=AsyncMock) as mock_ingest:
            mock_ingest.return_value = {"accepted": 1}
            result = await client.submit_measurements([{"uid": "m1", "meter": "api_calls"}])

        assert result == {"accepted": 1}
        mock_ingest.assert_called_once_with([{"uid": "m1", "meter": "api_calls"}])

    @pytest.mark.asyncio
    async def test_create_meter(self):
        from app.m3ter.client import M3terClient

        client = M3terClient("org1", "https://api.m3ter.com", "cid", "csecret")

        with patch.object(client, "_config_api_request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = {"id": "meter-123"}
            result = await client.create_meter({"name": "API Meter"})

        mock_req.assert_called_once_with(
            "POST", "/organizations/org1/meters", {"name": "API Meter"}
        )
        assert result == {"id": "meter-123"}

    @pytest.mark.asyncio
    async def test_create_account_plan(self):
        from app.m3ter.client import M3terClient

        client = M3terClient("org1", "https://api.m3ter.com", "cid", "csecret")

        with patch.object(client, "_config_api_request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = {"id": "ap-123"}
            result = await client.create_account_plan({"accountId": "a1", "planId": "p1"})

        mock_req.assert_called_once_with(
            "POST",
            "/organizations/org1/accountplans",
            {"accountId": "a1", "planId": "p1"},
        )
        assert result == {"id": "ap-123"}

    @pytest.mark.asyncio
    async def test_close_client(self):
        from app.m3ter.client import M3terClient

        client = M3terClient("org1", "https://api.m3ter.com", "cid", "csecret")

        # Get the internal client so it's initialized
        internal = client._get_client()
        assert internal is not None
        assert not internal.is_closed

        await client.close()
        assert client._client is None


# ─────────────────────────────────────────────────────────────
# Part 2: Mapper Tests
# ─────────────────────────────────────────────────────────────


class TestPayloadMapper:
    """Test allowlist-based payload mapping."""

    def test_product_maps_allowed_fields(self):
        from app.m3ter.mapper import map_entity_to_m3ter_payload
        from app.schemas.common import EntityType

        data = {
            "id": "mira-uuid",
            "index": 0,
            "name": "My Product",
            "code": "my_product",
            "customFields": {"env": "prod"},
            "extra_field": "should_be_stripped",
        }
        result = map_entity_to_m3ter_payload(EntityType.product, data)
        assert result == {
            "name": "My Product",
            "code": "my_product",
            "customFields": {"env": "prod"},
        }
        assert "id" not in result
        assert "index" not in result
        assert "extra_field" not in result

    def test_meter_maps_allowed_fields(self):
        from app.m3ter.mapper import map_entity_to_m3ter_payload
        from app.schemas.common import EntityType

        data = {
            "id": "mira-uuid",
            "name": "API Meter",
            "code": "api_meter",
            "productId": "prod-uuid",
            "dataFields": [{"code": "requests", "category": "MEASURE"}],
            "derivedFields": [],
        }
        result = map_entity_to_m3ter_payload(EntityType.meter, data)
        assert result["name"] == "API Meter"
        assert result["productId"] == "prod-uuid"
        assert result["dataFields"] == [{"code": "requests", "category": "MEASURE"}]
        assert "id" not in result

    def test_none_values_stripped(self):
        from app.m3ter.mapper import map_entity_to_m3ter_payload
        from app.schemas.common import EntityType

        data = {
            "name": "My Product",
            "code": "my_product",
            "customFields": None,
        }
        result = map_entity_to_m3ter_payload(EntityType.product, data)
        assert "customFields" not in result

    def test_internal_fields_stripped(self):
        from app.m3ter.mapper import map_entity_to_m3ter_payload
        from app.schemas.common import EntityType

        data = {"id": "uuid1", "index": 3, "name": "Test", "code": "test"}
        result = map_entity_to_m3ter_payload(EntityType.product, data)
        assert "id" not in result
        assert "index" not in result

    def test_aggregation_maps_correctly(self):
        from app.m3ter.mapper import map_entity_to_m3ter_payload
        from app.schemas.common import EntityType

        data = {
            "name": "Total API Calls",
            "code": "total_api_calls",
            "meterId": "meter-uuid",
            "aggregation": "SUM",
            "targetField": "requests",
            "rounding": "UP",
            "quantityPerUnit": 1.0,
            "unit": "requests",
            "segmentedFields": ["region"],
        }
        result = map_entity_to_m3ter_payload(EntityType.aggregation, data)
        assert result["aggregation"] == "SUM"
        assert result["rounding"] == "UP"
        assert result["quantityPerUnit"] == 1.0
        assert result["unit"] == "requests"
        assert result["segmentedFields"] == ["region"]
        # Single wildcard segment auto-generated when segmentedFields present
        assert result["segments"] == [{"region": "*"}]

    def test_aggregation_wildcard_segments_auto_generated(self):
        from app.m3ter.mapper import map_entity_to_m3ter_payload
        from app.schemas.common import EntityType

        data = {
            "name": "Token Usage by Model",
            "code": "token_usage_by_model",
            "meterId": "meter-uuid",
            "aggregation": "SUM",
            "targetField": "tokens",
            "quantityPerUnit": 1.0,
            "unit": "tokens",
            "segmentedFields": ["model", "tier"],
        }
        result = map_entity_to_m3ter_payload(EntityType.aggregation, data)
        # Single combined wildcard segment for all fields
        assert result["segments"] == [{"model": "*", "tier": "*"}]

    def test_aggregation_explicit_segments_preserved(self):
        from app.m3ter.mapper import map_entity_to_m3ter_payload
        from app.schemas.common import EntityType

        data = {
            "name": "Usage by Region",
            "code": "usage_by_region",
            "meterId": "meter-uuid",
            "aggregation": "SUM",
            "targetField": "requests",
            "quantityPerUnit": 1.0,
            "unit": "requests",
            "segmentedFields": ["region"],
            "segments": [{"region": "us-east"}, {"region": "eu-west"}],
        }
        result = map_entity_to_m3ter_payload(EntityType.aggregation, data)
        # Explicit segments should be preserved, not overwritten with wildcards
        assert result["segments"] == [{"region": "us-east"}, {"region": "eu-west"}]

    def test_aggregation_no_segments_without_segmented_fields(self):
        from app.m3ter.mapper import map_entity_to_m3ter_payload
        from app.schemas.common import EntityType

        data = {
            "name": "Total Requests",
            "code": "total_requests",
            "meterId": "meter-uuid",
            "aggregation": "SUM",
            "targetField": "requests",
            "quantityPerUnit": 1.0,
            "unit": "requests",
        }
        result = map_entity_to_m3ter_payload(EntityType.aggregation, data)
        # No segmentedFields means no segments should be added
        assert "segments" not in result

    def test_pricing_maps_correctly(self):
        from app.m3ter.mapper import map_entity_to_m3ter_payload
        from app.schemas.common import EntityType

        data = {
            "planId": "plan-uuid",
            "planTemplateId": "pt-uuid",
            "aggregationId": "agg-uuid",
            "type": "DEBIT",
            "code": "api_pricing",
            "cumulative": True,
            "startDate": "2024-01-01",
            "pricingBands": [{"lowerLimit": 0, "unitPrice": 0.01}],
            "customFields": {},
        }
        result = map_entity_to_m3ter_payload(EntityType.pricing, data)
        assert result["planId"] == "plan-uuid"
        assert result["pricingBands"] == [{"lowerLimit": 0, "unitPrice": 0.01}]

    def test_account_maps_correctly(self):
        from app.m3ter.mapper import map_entity_to_m3ter_payload
        from app.schemas.common import EntityType

        data = {
            "name": "Acme Corp",
            "code": "acme",
            "emailAddress": "billing@acme.com",
            "currency": "USD",
            "address": {"addressLine1": "123 Main St"},
            "parentAccountId": None,
            "purchaseOrderNumber": "PO-001",
            "daysBeforeBillDue": 30,
        }
        result = map_entity_to_m3ter_payload(EntityType.account, data)
        assert result["emailAddress"] == "billing@acme.com"
        assert "parentAccountId" not in result  # None stripped

    def test_measurements_mapper(self):
        from app.m3ter.mapper import map_measurements_to_m3ter_payload

        measurements = [
            {
                "id": "mira-uuid",
                "index": 0,
                "uid": "m1",
                "meter": "api_calls",
                "account": "acme",
                "ts": "2024-01-15T10:30:00Z",
                "measure": {"requests": 100},
                "extra": "stripped",
            }
        ]
        result = map_measurements_to_m3ter_payload(measurements)
        assert len(result) == 1
        assert result[0]["uid"] == "m1"
        assert result[0]["meter"] == "api_calls"
        assert "id" not in result[0]
        assert "index" not in result[0]
        assert "extra" not in result[0]

    def test_plan_template_maps_correctly(self):
        from app.m3ter.mapper import map_entity_to_m3ter_payload
        from app.schemas.common import EntityType

        data = {
            "name": "Standard Plan",
            "code": "standard",
            "productId": "prod-uuid",
            "currency": "USD",
            "standingCharge": 10.0,
            "billFrequency": "MONTHLY",
            "billFrequencyInterval": 1,
            "minimumSpend": 5.0,
            "customFields": {},
        }
        result = map_entity_to_m3ter_payload(EntityType.plan_template, data)
        assert result["currency"] == "USD"
        assert result["billFrequency"] == "MONTHLY"

    def test_account_plan_maps_correctly(self):
        from app.m3ter.mapper import map_entity_to_m3ter_payload
        from app.schemas.common import EntityType

        data = {
            "accountId": "acct-uuid",
            "planId": "plan-uuid",
            "startDate": "2024-01-01",
            "endDate": "2025-01-01",
            "customFields": {},
        }
        result = map_entity_to_m3ter_payload(EntityType.account_plan, data)
        assert result["accountId"] == "acct-uuid"
        assert result["planId"] == "plan-uuid"
        assert result["startDate"] == "2024-01-01"

    def test_unsupported_entity_type_raises(self):
        from app.m3ter.mapper import map_entity_to_m3ter_payload
        from app.schemas.common import EntityType

        with pytest.raises(ValueError, match="No field allowlist"):
            map_entity_to_m3ter_payload(EntityType.compound_aggregation, {})


# ─────────────────────────────────────────────────────────────
# Part 3: ReferenceResolver Tests
# ─────────────────────────────────────────────────────────────


class TestReferenceResolver:
    """Test reference resolution: register, resolve, pre-load, errors."""

    def test_register_and_resolve(self):
        from app.m3ter.entities import ReferenceResolver
        from app.schemas.common import EntityType

        resolver = ReferenceResolver()
        resolver.register("mira-prod-1", "m3ter-prod-1")

        data = {"name": "Test Meter", "productId": "mira-prod-1"}
        resolved = resolver.resolve_references(EntityType.meter, data)
        assert resolved["productId"] == "m3ter-prod-1"

    def test_preload_from_db(self):
        from app.m3ter.entities import ReferenceResolver
        from app.schemas.common import EntityType

        pushed_objects = [
            {"id": "mira-1", "status": "pushed", "m3ter_id": "m3ter-1"},
            {"id": "mira-2", "status": "approved", "m3ter_id": None},  # Not pushed
        ]

        resolver = ReferenceResolver()
        resolver.preload_from_db(pushed_objects)

        data = {"productId": "mira-1"}
        resolved = resolver.resolve_references(EntityType.meter, data)
        assert resolved["productId"] == "m3ter-1"

    def test_missing_reference_raises_error(self):
        from app.m3ter.entities import ReferenceResolutionError, ReferenceResolver
        from app.schemas.common import EntityType

        resolver = ReferenceResolver()

        data = {"productId": "nonexistent-uuid"}
        with pytest.raises(ReferenceResolutionError) as exc_info:
            resolver.resolve_references(EntityType.meter, data)

        assert exc_info.value.field == "productId"
        assert exc_info.value.referenced_id == "nonexistent-uuid"

    def test_none_reference_skipped(self):
        from app.m3ter.entities import ReferenceResolver
        from app.schemas.common import EntityType

        resolver = ReferenceResolver()

        data = {"name": "Test", "productId": None}
        resolved = resolver.resolve_references(EntityType.meter, data)
        assert resolved["productId"] is None

    def test_no_reference_fields_pass_through(self):
        from app.m3ter.entities import ReferenceResolver
        from app.schemas.common import EntityType

        resolver = ReferenceResolver()

        data = {"name": "My Product", "code": "my_product"}
        resolved = resolver.resolve_references(EntityType.product, data)
        assert resolved == data

    def test_multiple_references_resolved(self):
        from app.m3ter.entities import ReferenceResolver
        from app.schemas.common import EntityType

        resolver = ReferenceResolver()
        resolver.register("mira-acct-1", "m3ter-acct-1")
        resolver.register("mira-plan-1", "m3ter-plan-1")

        data = {"accountId": "mira-acct-1", "planId": "mira-plan-1", "startDate": "2024-01-01"}
        resolved = resolver.resolve_references(EntityType.account_plan, data)
        assert resolved["accountId"] == "m3ter-acct-1"
        assert resolved["planId"] == "m3ter-plan-1"


# ─────────────────────────────────────────────────────────────
# Part 4: Push Ordering Tests
# ─────────────────────────────────────────────────────────────


class TestPushOrdering:
    """Test entity type sort order and push engine behavior."""

    def test_push_order_correct(self):
        from app.m3ter.entities import PUSH_ORDER
        from app.schemas.common import EntityType

        expected = [
            EntityType.product,
            EntityType.meter,
            EntityType.aggregation,
            EntityType.plan_template,
            EntityType.plan,
            EntityType.pricing,
            EntityType.account,
            EntityType.account_plan,
        ]
        assert PUSH_ORDER == expected

    def test_compound_aggregation_not_in_push_order(self):
        from app.m3ter.entities import PUSH_ORDER
        from app.schemas.common import EntityType

        assert EntityType.compound_aggregation not in PUSH_ORDER

    def test_measurement_not_in_push_order(self):
        from app.m3ter.entities import PUSH_ORDER
        from app.schemas.common import EntityType

        assert EntityType.measurement not in PUSH_ORDER

    def test_sort_key_orders_correctly(self):
        from app.m3ter.entities import _sort_key

        objects = [
            {"entity_type": "pricing"},
            {"entity_type": "product"},
            {"entity_type": "meter"},
            {"entity_type": "account"},
            {"entity_type": "aggregation"},
        ]
        sorted_types = sorted([o["entity_type"] for o in objects], key=_sort_key)
        assert sorted_types == ["product", "meter", "aggregation", "pricing", "account"]

    @pytest.mark.asyncio
    async def test_skip_already_pushed(self):
        """Already-pushed objects should be skipped."""
        from app.m3ter.entities import push_entities_ordered

        mock_client = AsyncMock()
        mock_supabase = MagicMock()

        objects = [
            _object_row(
                entity_type="product",
                status="pushed",
                m3ter_id="m3ter-prod-1",
            ),
        ]

        result = await push_entities_ordered(mock_client, mock_supabase, objects)
        assert result.skipped == 1
        assert result.succeeded == 0
        assert result.failed == 0

    @pytest.mark.asyncio
    async def test_stop_on_failure(self):
        """After one failure, remaining entities should be skipped."""
        from app.m3ter.entities import push_entities_ordered

        mock_client = AsyncMock()
        mock_client.create_product = AsyncMock(side_effect=Exception("API Error"))
        mock_supabase = MagicMock()
        # Mock the update chain
        mock_builder = MagicMock()
        mock_builder.eq.return_value = mock_builder
        mock_builder.execute.return_value = MagicMock(data=[])
        mock_supabase.table.return_value.update.return_value = mock_builder

        ucid = str(uuid4())
        objects = [
            _object_row(use_case_id=ucid, entity_type="product", status="approved"),
            _object_row(use_case_id=ucid, entity_type="meter", status="approved"),
        ]

        result = await push_entities_ordered(mock_client, mock_supabase, objects)
        assert result.failed == 1
        assert result.skipped == 1
        assert result.succeeded == 0

    @pytest.mark.asyncio
    async def test_successful_push_flow(self):
        """Successful push should update DB and register in resolver."""
        from app.m3ter.entities import push_entities_ordered

        mock_client = AsyncMock()
        mock_client.create_product = AsyncMock(return_value={"id": "m3ter-prod-1", "name": "Test"})

        mock_supabase = MagicMock()
        mock_builder = MagicMock()
        mock_builder.eq.return_value = mock_builder
        mock_builder.execute.return_value = MagicMock(data=[])
        mock_supabase.table.return_value.update.return_value = mock_builder

        objects = [
            _object_row(entity_type="product", status="approved"),
        ]

        progress_calls = []
        result = await push_entities_ordered(
            mock_client, mock_supabase, objects, on_progress=progress_calls.append
        )
        assert result.succeeded == 1
        assert result.failed == 0
        assert len(progress_calls) == 1
        assert progress_calls[0].success is True
        assert progress_calls[0].m3ter_id == "m3ter-prod-1"


# ─────────────────────────────────────────────────────────────
# Part 5: Push Service Tests
# ─────────────────────────────────────────────────────────────


class TestPushService:
    """Test push service: org resolution, eligibility, ownership."""

    def test_get_push_status(self, authed_client, mock_supabase):
        ucid = str(uuid4())
        conn_id = str(uuid4())
        mock_supabase._table_data["use_cases"] = [
            _use_case_row(
                id=ucid,
                projects={
                    "user_id": str(MOCK_USER_ID),
                    "org_connection_id": conn_id,
                },
            )
        ]
        mock_supabase._table_data["generated_objects"] = [
            _object_row(use_case_id=ucid, entity_type="product", status="approved"),
            _object_row(use_case_id=ucid, entity_type="meter", status="pushed", m3ter_id="m1"),
            _object_row(use_case_id=ucid, entity_type="meter", status="draft"),
        ]

        resp = authed_client.get(f"/api/use-cases/{ucid}/push/status")
        assert resp.status_code == 200
        body = resp.json()
        assert body["org_connected"] is True
        assert body["eligible_count"] == 1  # Only approved
        assert body["pushed_count"] == 1
        assert body["total_count"] == 3

    def test_get_push_status_no_org_connection(self, authed_client, mock_supabase):
        ucid = str(uuid4())
        mock_supabase._table_data["use_cases"] = [
            _use_case_row(
                id=ucid,
                projects={
                    "user_id": str(MOCK_USER_ID),
                    "org_connection_id": None,
                },
            )
        ]
        mock_supabase._table_data["generated_objects"] = []

        resp = authed_client.get(f"/api/use-cases/{ucid}/push/status")
        assert resp.status_code == 200
        body = resp.json()
        assert body["org_connected"] is False

    def test_get_push_status_not_found(self, authed_client, mock_supabase):
        mock_supabase._table_data["use_cases"] = []
        resp = authed_client.get(f"/api/use-cases/{uuid4()}/push/status")
        assert resp.status_code == 404

    def test_push_single_object_not_found(self, authed_client, mock_supabase):
        mock_supabase._table_data["generated_objects"] = []
        resp = authed_client.post(f"/api/objects/{uuid4()}/push")
        assert resp.status_code == 404

    def test_push_single_object_wrong_status(self, authed_client, mock_supabase):
        oid = str(uuid4())
        ucid = str(uuid4())
        conn_id = str(uuid4())
        row = _object_row(id=oid, use_case_id=ucid, status="draft")
        row["use_cases"] = {
            "project_id": str(uuid4()),
            "projects": {
                "user_id": str(MOCK_USER_ID),
                "org_connection_id": conn_id,
            },
        }
        mock_supabase._table_data["generated_objects"] = [row]

        resp = authed_client.post(f"/api/objects/{oid}/push")
        assert resp.status_code == 400
        assert "approved" in resp.json()["detail"]

    def test_bulk_push_not_found(self, authed_client, mock_supabase):
        mock_supabase._table_data["use_cases"] = []
        resp = authed_client.post(f"/api/use-cases/{uuid4()}/push")
        assert resp.status_code == 404


class TestOrgConnectionResolution:
    """Test _resolve_org_connection logic."""

    @pytest.mark.asyncio
    async def test_no_org_connection_raises(self):
        from app.services.push_service import _resolve_org_connection

        mock_supabase = MagicMock()
        ucid = uuid4()
        row = _use_case_row(
            id=str(ucid),
            projects={"user_id": str(MOCK_USER_ID), "org_connection_id": None},
        )

        from tests.conftest import MockPostgrestBuilder

        mock_supabase.table.return_value = MockPostgrestBuilder([row])

        with pytest.raises(Exception) as exc_info:
            await _resolve_org_connection(mock_supabase, MOCK_USER_ID, ucid)

        assert "No m3ter organization connection" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_org_connection_found(self):
        from app.services.push_service import _resolve_org_connection

        mock_supabase = MagicMock()
        ucid = uuid4()
        conn_id = str(uuid4())

        uc_row = _use_case_row(
            id=str(ucid),
            projects={
                "user_id": str(MOCK_USER_ID),
                "org_connection_id": conn_id,
            },
        )
        conn_row = _org_connection_row(id=conn_id)

        from tests.conftest import MockPostgrestBuilder

        original_table_data = {
            "use_cases": [uc_row],
            "org_connections": [conn_row],
        }

        def mock_table(name):
            return MockPostgrestBuilder(original_table_data.get(name, []))

        mock_supabase.table = mock_table

        with patch("app.services.push_service.decrypt_value") as mock_decrypt:
            mock_decrypt.side_effect = lambda x: f"decrypted_{x}"
            org_id, api_url, client_id, client_secret = await _resolve_org_connection(
                mock_supabase, MOCK_USER_ID, ucid
            )

        assert org_id == "test-org-id"
        assert api_url == "https://api.m3ter.com"
        assert client_id == "decrypted_encrypted_client_id"
        assert client_secret == "decrypted_encrypted_client_secret"

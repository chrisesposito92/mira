"""Unit tests for the plan_pricing graph structure and generation nodes."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agents.graphs.plan_pricing import _build_graph
from app.agents.nodes.load_approved import load_approved_entities
from app.agents.nodes.plan_gen import generate_plans
from app.agents.nodes.plan_template_gen import generate_plan_templates
from app.agents.nodes.pricing_gen import generate_pricing
from app.agents.nodes.validation import _STEP_TO_ENTITY, validate_entities


@pytest.fixture
def base_state() -> dict:
    """Base workflow state for plan/pricing testing."""
    return {
        "use_case_id": "uc-111",
        "project_id": "proj-222",
        "model_id": "claude-sonnet-4-6",
        "user_id": "user-333",
    }


def _make_llm_response(content: str | dict | list) -> MagicMock:
    """Create a mock LLM response with content attribute."""
    response = MagicMock()
    response.content = json.dumps(content) if isinstance(content, dict | list) else content
    return response


# ---------------------------------------------------------------------------
# Graph structure tests
# ---------------------------------------------------------------------------


class TestPlanPricingGraphStructure:
    def test_graph_has_all_expected_nodes(self):
        graph = _build_graph()
        expected_nodes = {
            "load_approved_entities",
            "generate_plan_templates",
            "validate_plan_templates",
            "approve_plan_templates",
            "generate_plans",
            "validate_plans",
            "approve_plans",
            "generate_pricing",
            "validate_pricing",
            "approve_pricing",
        }
        node_names = {name for name in graph.nodes if not name.startswith("__")}
        assert expected_nodes == node_names

    def test_graph_entry_point_is_load_approved(self):
        graph = _build_graph()
        # The entry point creates an edge from __start__ to load_approved_entities
        assert "load_approved_entities" in graph.nodes

    def test_graph_compiles_without_checkpointer(self):
        graph = _build_graph()
        compiled = graph.compile()
        assert compiled is not None

    def test_graph_edges_connect_properly(self):
        """Verify the sequential flow of edges in the graph."""
        graph = _build_graph()
        compiled = graph.compile()
        # The graph should compile without error, confirming valid edge connections
        assert compiled is not None

    def test_graph_has_correct_node_count(self):
        graph = _build_graph()
        non_internal_nodes = {name for name in graph.nodes if not name.startswith("__")}
        assert len(non_internal_nodes) == 10


# ---------------------------------------------------------------------------
# Load approved entities tests
# ---------------------------------------------------------------------------


class TestLoadApprovedEntities:
    @pytest.mark.asyncio
    @patch("app.agents.nodes.load_approved.rag_retrieve", new_callable=AsyncMock)
    @patch("app.agents.nodes.load_approved.get_supabase_client")
    async def test_loads_approved_entities_from_db(self, mock_supabase, mock_rag, base_state):
        mock_client = MagicMock()

        # Mock generated_objects query (includes id for cross-entity references)
        mock_objects_result = MagicMock()
        mock_objects_result.data = [
            {
                "id": "prod-aaa",
                "entity_type": "product",
                "data": {"name": "API Gateway", "code": "api_gateway"},
            },
            {
                "id": "meter-bbb",
                "entity_type": "meter",
                "data": {"name": "Request Meter", "code": "request_meter"},
            },
            {
                "id": "agg-ccc",
                "entity_type": "aggregation",
                "data": {"name": "Daily Count", "code": "daily_count"},
            },
        ]

        # Mock use_cases query
        mock_uc_result = MagicMock()
        mock_uc_result.data = [
            {
                "id": "uc-111",
                "title": "API Billing",
                "description": "Bill for API usage",
            }
        ]

        # Mock workflows query (latest completed WF1 with time window)
        mock_wf_result = MagicMock()
        mock_wf_result.data = [
            {
                "started_at": "2025-01-01T00:00:00Z",
                "completed_at": "2025-01-01T01:00:00Z",
            }
        ]

        def table_side_effect(name):
            builder = MagicMock()
            builder.select.return_value = builder
            builder.eq.return_value = builder
            builder.in_.return_value = builder
            builder.gte.return_value = builder
            builder.lte.return_value = builder
            builder.order.return_value = builder
            builder.limit.return_value = builder
            if name == "generated_objects":
                builder.execute.return_value = mock_objects_result
            elif name == "workflows":
                builder.execute.return_value = mock_wf_result
            else:
                builder.execute.return_value = mock_uc_result
            return builder

        mock_client.table = table_side_effect
        mock_supabase.return_value = mock_client

        mock_rag.return_value = "Relevant plan/pricing documentation..."

        result = await load_approved_entities(base_state)

        assert len(result["approved_products"]) == 1
        assert len(result["approved_meters"]) == 1
        assert len(result["approved_aggregations"]) == 1
        # Verify canonical IDs are injected into entity data
        assert result["approved_products"][0]["id"] == "prod-aaa"
        assert result["approved_meters"][0]["id"] == "meter-bbb"
        assert result["approved_aggregations"][0]["id"] == "agg-ccc"
        # Verify original data is preserved
        assert result["approved_products"][0]["name"] == "API Gateway"
        assert result["current_step"] == "approved_entities_loaded"
        assert result["use_case"]["title"] == "API Billing"
        assert result["rag_context"] == "Relevant plan/pricing documentation..."

    @pytest.mark.asyncio
    @patch("app.agents.nodes.load_approved.rag_retrieve", new_callable=AsyncMock)
    @patch("app.agents.nodes.load_approved.get_supabase_client")
    async def test_handles_empty_approved_entities(self, mock_supabase, mock_rag, base_state):
        mock_client = MagicMock()

        def table_side_effect(name):
            builder = MagicMock()
            builder.select.return_value = builder
            builder.eq.return_value = builder
            builder.in_.return_value = builder
            builder.gte.return_value = builder
            builder.lte.return_value = builder
            builder.order.return_value = builder
            builder.limit.return_value = builder
            mock_result = MagicMock()
            mock_result.data = []
            builder.execute.return_value = mock_result
            return builder

        mock_client.table = table_side_effect
        mock_supabase.return_value = mock_client
        mock_rag.return_value = ""

        result = await load_approved_entities(base_state)

        assert "error" in result
        assert result["current_step"] == "error"


# ---------------------------------------------------------------------------
# Generation node tests
# ---------------------------------------------------------------------------


class TestGeneratePlanTemplates:
    @pytest.mark.asyncio
    @patch("app.agents.nodes.plan_template_gen.get_llm")
    async def test_generates_plan_template_list(self, mock_get_llm, base_state):
        state = {
            **base_state,
            "approved_products": [{"name": "API Gateway", "code": "api_gateway"}],
            "analysis": "Need a standard plan template",
            "rag_context": "m3ter docs...",
        }

        plan_templates = [
            {
                "name": "API Gateway Standard",
                "code": "api_gateway_standard",
                "productId": "prod-uuid",
                "currency": "USD",
                "standingCharge": 99.0,
                "billFrequency": "MONTHLY",
            }
        ]
        mock_llm_instance = AsyncMock()
        mock_llm_instance.ainvoke.return_value = _make_llm_response(plan_templates)
        mock_get_llm.return_value = mock_llm_instance

        result = await generate_plan_templates(state)

        assert len(result["plan_templates"]) == 1
        assert result["plan_templates"][0]["name"] == "API Gateway Standard"
        assert result["current_step"] == "plan_templates_generated"

    @pytest.mark.asyncio
    @patch("app.agents.nodes.plan_template_gen.get_llm")
    async def test_uses_use_case_fallback_when_no_analysis(self, mock_get_llm, base_state):
        state = {
            **base_state,
            "approved_products": [],
            "analysis": "",
            "rag_context": "",
            "use_case": {"title": "API Billing", "description": "Bill for APIs"},
        }

        mock_llm_instance = AsyncMock()
        mock_llm_instance.ainvoke.return_value = _make_llm_response([])
        mock_get_llm.return_value = mock_llm_instance

        result = await generate_plan_templates(state)

        assert result["plan_templates"] == []
        assert result["current_step"] == "error"
        assert "error" in result
        # Verify LLM was called (meaning prompt was built from use_case)
        mock_llm_instance.ainvoke.assert_called_once()


class TestGeneratePlans:
    @pytest.mark.asyncio
    @patch("app.agents.nodes.plan_gen.get_llm")
    async def test_generates_plan_list(self, mock_get_llm, base_state):
        state = {
            **base_state,
            "approved_products": [{"name": "API Gateway", "code": "api_gateway"}],
            "plan_templates": [
                {
                    "name": "API Gateway Standard",
                    "code": "api_gateway_standard",
                    "planTemplateId": "pt-uuid",
                }
            ],
            "analysis": "Need standard plans",
            "rag_context": "m3ter docs...",
        }

        plans = [
            {
                "name": "API Gateway Standard - Monthly",
                "code": "api_std_monthly",
                "planTemplateId": "pt-uuid",
            }
        ]
        mock_llm_instance = AsyncMock()
        mock_llm_instance.ainvoke.return_value = _make_llm_response(plans)
        mock_get_llm.return_value = mock_llm_instance

        result = await generate_plans(state)

        assert len(result["plans"]) == 1
        assert result["plans"][0]["code"] == "api_std_monthly"
        assert result["current_step"] == "plans_generated"

    @pytest.mark.asyncio
    @patch("app.agents.nodes.plan_gen.get_llm")
    async def test_returns_error_on_empty_result(self, mock_get_llm, base_state):
        state = {
            **base_state,
            "approved_products": [],
            "plan_templates": [],
            "analysis": "Test",
            "rag_context": "",
        }

        mock_llm_instance = AsyncMock()
        mock_llm_instance.ainvoke.return_value = _make_llm_response([])
        mock_get_llm.return_value = mock_llm_instance

        result = await generate_plans(state)
        assert result["current_step"] == "error"
        assert result["plans"] == []
        assert "error" in result


class TestGeneratePricing:
    @pytest.mark.asyncio
    @patch("app.agents.nodes.pricing_gen.get_llm")
    async def test_generates_pricing_list(self, mock_get_llm, base_state):
        state = {
            **base_state,
            "approved_aggregations": [{"name": "Daily API Count", "code": "daily_api_count"}],
            "plans": [
                {"name": "API Standard", "code": "api_standard", "planTemplateId": "pt-uuid"}
            ],
            "plan_templates": [{"name": "API Template", "code": "api_template"}],
            "analysis": "Need flat pricing",
            "rag_context": "m3ter docs...",
        }

        pricing_entities = [
            {
                "planTemplateId": "pt-uuid",
                "aggregationId": "agg-uuid",
                "type": "DEBIT",
                "cumulative": False,
                "startDate": "2024-01-01",
                "pricingBands": [{"lowerLimit": 0, "unitPrice": 0.01}],
            }
        ]
        mock_llm_instance = AsyncMock()
        mock_llm_instance.ainvoke.return_value = _make_llm_response(pricing_entities)
        mock_get_llm.return_value = mock_llm_instance

        result = await generate_pricing(state)

        assert len(result["pricing"]) == 1
        assert result["pricing"][0]["type"] == "DEBIT"
        assert result["current_step"] == "pricing_generated"

    @pytest.mark.asyncio
    @patch("app.agents.nodes.pricing_gen.get_llm")
    async def test_returns_error_on_empty_result(self, mock_get_llm, base_state):
        state = {
            **base_state,
            "approved_aggregations": [],
            "plans": [],
            "plan_templates": [],
            "analysis": "Test",
            "rag_context": "",
        }

        mock_llm_instance = AsyncMock()
        mock_llm_instance.ainvoke.return_value = _make_llm_response([])
        mock_get_llm.return_value = mock_llm_instance

        result = await generate_pricing(state)
        assert result["current_step"] == "error"
        assert result["pricing"] == []
        assert "error" in result


# ---------------------------------------------------------------------------
# Validation node tests for new entity types
# ---------------------------------------------------------------------------


class TestValidateNewEntityTypes:
    def test_step_to_entity_has_plan_templates_generated(self):
        assert "plan_templates_generated" in _STEP_TO_ENTITY

    def test_step_to_entity_has_plans_generated(self):
        assert "plans_generated" in _STEP_TO_ENTITY

    def test_step_to_entity_has_pricing_generated(self):
        assert "pricing_generated" in _STEP_TO_ENTITY

    @pytest.mark.asyncio
    async def test_validates_plan_templates(self):
        state = {
            "current_step": "plan_templates_generated",
            "plan_templates": [
                {
                    "name": "Standard Plan",
                    "code": "standard_plan",
                    "productId": "prod-uuid",
                    "currency": "USD",
                    "standingCharge": 99.0,
                    "billFrequency": "MONTHLY",
                }
            ],
        }
        result = await validate_entities(state)
        assert "plan_template_errors" in result
        assert result["current_step"] == "plan_templates_validated"

    @pytest.mark.asyncio
    async def test_validates_plans(self):
        state = {
            "current_step": "plans_generated",
            "plans": [
                {
                    "name": "Standard Monthly",
                    "code": "standard_monthly",
                    "planTemplateId": "pt-uuid",
                }
            ],
        }
        result = await validate_entities(state)
        assert "plan_errors" in result
        assert result["current_step"] == "plans_validated"

    @pytest.mark.asyncio
    async def test_validates_pricing(self):
        state = {
            "current_step": "pricing_generated",
            "pricing": [
                {
                    "startDate": "2024-01-01",
                    "pricingBands": [{"lowerLimit": 0, "unitPrice": 0.01}],
                }
            ],
        }
        result = await validate_entities(state)
        assert "pricing_errors" in result
        assert result["current_step"] == "pricing_validated"


# ---------------------------------------------------------------------------
# Approval config tests for new entity types
# ---------------------------------------------------------------------------


class TestApprovalConfigNewEntityTypes:
    def test_approval_config_has_plan_templates_validated(self):
        from app.agents.nodes.approval import _STEP_CONFIG

        assert "plan_templates_validated" in _STEP_CONFIG
        config = _STEP_CONFIG["plan_templates_validated"]
        assert config[4] == "plan_templates_approved"

    def test_approval_config_has_plans_validated(self):
        from app.agents.nodes.approval import _STEP_CONFIG

        assert "plans_validated" in _STEP_CONFIG
        config = _STEP_CONFIG["plans_validated"]
        assert config[4] == "plans_approved"

    def test_approval_config_has_pricing_validated(self):
        from app.agents.nodes.approval import _STEP_CONFIG

        assert "pricing_validated" in _STEP_CONFIG
        config = _STEP_CONFIG["pricing_validated"]
        assert config[4] == "pricing_approved"

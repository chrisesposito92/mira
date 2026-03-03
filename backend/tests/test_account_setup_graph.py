"""Unit tests for the account_setup graph structure and generation nodes."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agents.graphs.account_setup import (
    _build_graph,
    route_after_approve_accounts,
    route_after_load,
)
from app.agents.nodes.account_gen import generate_accounts
from app.agents.nodes.account_plan_gen import generate_account_plans
from app.agents.nodes.load_approved_accounts import load_approved_for_accounts
from app.agents.nodes.validation import _STEP_TO_ENTITY, validate_entities


@pytest.fixture
def base_state() -> dict:
    """Base workflow state for account setup testing."""
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


class TestAccountSetupGraphStructure:
    def test_graph_has_all_expected_nodes(self):
        graph = _build_graph()
        expected_nodes = {
            "load_approved_for_accounts",
            "generate_accounts",
            "validate_accounts",
            "approve_accounts",
            "generate_account_plans",
            "validate_account_plans",
            "approve_account_plans",
        }
        node_names = {name for name in graph.nodes if not name.startswith("__")}
        assert expected_nodes == node_names

    def test_graph_entry_point_is_load_approved(self):
        graph = _build_graph()
        assert "load_approved_for_accounts" in graph.nodes

    def test_graph_compiles_without_checkpointer(self):
        graph = _build_graph()
        compiled = graph.compile()
        assert compiled is not None

    def test_graph_has_correct_node_count(self):
        graph = _build_graph()
        non_internal_nodes = {name for name in graph.nodes if not name.startswith("__")}
        assert len(non_internal_nodes) == 7

    def test_route_after_load_returns_end_on_error(self):
        """Load node should route to END when current_step is 'error'."""
        from langgraph.graph import END

        assert route_after_load({"current_step": "error"}) == END
        loaded = "approved_entities_loaded_for_accounts"
        assert route_after_load({"current_step": loaded}) == "generate_accounts"

    def test_route_after_approve_accounts_returns_end_when_empty(self):
        """Approve node should route to END when all accounts were rejected."""
        from langgraph.graph import END

        assert route_after_approve_accounts({"accounts": []}) == END
        assert route_after_approve_accounts({}) == END
        state = {"accounts": [{"name": "Acme"}]}
        assert route_after_approve_accounts(state) == "generate_account_plans"


# ---------------------------------------------------------------------------
# Load approved entities tests
# ---------------------------------------------------------------------------


class TestLoadApprovedForAccounts:
    @pytest.mark.asyncio
    @patch("app.agents.nodes.load_approved_accounts.rag_retrieve", new_callable=AsyncMock)
    @patch("app.agents.nodes.load_approved_accounts.get_supabase_client")
    async def test_loads_approved_entities_from_db(
        self, mock_supabase, mock_rag, base_state, mock_config
    ):
        mock_client = MagicMock()

        # Mock WF1 entities
        mock_wf1_objects = MagicMock()
        mock_wf1_objects.data = [
            {
                "id": "prod-aaa",
                "entity_type": "product",
                "data": {"name": "API Gateway", "code": "api_gateway"},
            },
        ]

        # Mock WF2 entities
        mock_wf2_objects = MagicMock()
        mock_wf2_objects.data = [
            {
                "id": "plan-bbb",
                "entity_type": "plan",
                "data": {"name": "Standard Plan", "code": "standard_plan"},
            },
        ]

        # Mock use_cases query
        mock_uc_result = MagicMock()
        mock_uc_result.data = [
            {"id": "uc-111", "title": "API Billing", "description": "Bill for API usage"}
        ]

        # Mock workflows queries (WF1 and WF2)
        mock_wf_result = MagicMock()
        mock_wf_result.data = [
            {
                "started_at": "2025-01-01T00:00:00Z",
                "completed_at": "2025-01-01T01:00:00Z",
            }
        ]

        call_count = {"generated_objects": 0}

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
                call_count["generated_objects"] += 1
                if call_count["generated_objects"] == 1:
                    builder.execute.return_value = mock_wf1_objects
                else:
                    builder.execute.return_value = mock_wf2_objects
            elif name == "workflows":
                builder.execute.return_value = mock_wf_result
            else:
                builder.execute.return_value = mock_uc_result
            return builder

        mock_client.table = table_side_effect
        mock_supabase.return_value = mock_client
        mock_rag.return_value = "Relevant account docs..."

        result = await load_approved_for_accounts(base_state, mock_config)

        assert len(result["approved_products"]) == 1
        assert result["approved_products"][0]["id"] == "prod-aaa"
        assert len(result["approved_plans"]) == 1
        assert result["approved_plans"][0]["id"] == "plan-bbb"
        assert result["current_step"] == "approved_entities_loaded_for_accounts"
        assert result["rag_context"] == "Relevant account docs..."

    @pytest.mark.asyncio
    @patch("app.agents.nodes.load_approved_accounts.rag_retrieve", new_callable=AsyncMock)
    @patch("app.agents.nodes.load_approved_accounts.get_supabase_client")
    async def test_errors_when_no_approved_plans(
        self, mock_supabase, mock_rag, base_state, mock_config
    ):
        """WF3 should fail if no approved plans exist (needed for AccountPlan generation)."""
        mock_client = MagicMock()

        # Return products but no plans
        mock_wf1_objects = MagicMock()
        mock_wf1_objects.data = [
            {
                "id": "prod-aaa",
                "entity_type": "product",
                "data": {"name": "API Gateway", "code": "api_gateway"},
            },
        ]

        # Empty WF2 result — no plans
        mock_wf2_objects = MagicMock()
        mock_wf2_objects.data = []

        mock_wf_result = MagicMock()
        mock_wf_result.data = [
            {
                "started_at": "2025-01-01T00:00:00Z",
                "completed_at": "2025-01-01T01:00:00Z",
            }
        ]

        call_count = {"generated_objects": 0}

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
                call_count["generated_objects"] += 1
                if call_count["generated_objects"] == 1:
                    builder.execute.return_value = mock_wf1_objects
                else:
                    builder.execute.return_value = mock_wf2_objects
            elif name == "workflows":
                builder.execute.return_value = mock_wf_result
            return builder

        mock_client.table = table_side_effect
        mock_supabase.return_value = mock_client
        mock_rag.return_value = ""

        result = await load_approved_for_accounts(base_state, mock_config)

        assert "error" in result
        assert result["current_step"] == "error"
        assert "plans" in result["error"].lower()

    @pytest.mark.asyncio
    @patch("app.agents.nodes.load_approved_accounts.rag_retrieve", new_callable=AsyncMock)
    @patch("app.agents.nodes.load_approved_accounts.get_supabase_client")
    async def test_handles_empty_approved_entities(
        self, mock_supabase, mock_rag, base_state, mock_config
    ):
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

        result = await load_approved_for_accounts(base_state, mock_config)

        assert "error" in result
        assert result["current_step"] == "error"


# ---------------------------------------------------------------------------
# Generation node tests
# ---------------------------------------------------------------------------


class TestGenerateAccounts:
    @pytest.mark.asyncio
    @patch("app.agents.nodes.account_gen.get_llm")
    async def test_generates_account_list(self, mock_get_llm, base_state, mock_config):
        state = {
            **base_state,
            "approved_products": [{"name": "API Gateway", "code": "api_gateway"}],
            "approved_plans": [{"name": "Standard", "code": "standard"}],
            "analysis": "Need customer accounts",
            "rag_context": "m3ter docs...",
        }

        accounts = [
            {
                "name": "Acme Corp",
                "code": "acme_corp",
                "email": "billing@acme.com",
            }
        ]
        mock_llm_instance = AsyncMock()
        mock_llm_instance.ainvoke.return_value = _make_llm_response(accounts)
        mock_get_llm.return_value = mock_llm_instance

        result = await generate_accounts(state, mock_config)

        assert len(result["accounts"]) == 1
        assert result["accounts"][0]["name"] == "Acme Corp"
        assert result["current_step"] == "accounts_generated"

    @pytest.mark.asyncio
    @patch("app.agents.nodes.account_gen.get_llm")
    async def test_uses_use_case_fallback_when_no_analysis(
        self, mock_get_llm, base_state, mock_config
    ):
        state = {
            **base_state,
            "approved_products": [],
            "approved_plans": [],
            "analysis": "",
            "rag_context": "",
            "use_case": {"title": "API Billing", "description": "Bill for APIs"},
        }

        mock_llm_instance = AsyncMock()
        mock_llm_instance.ainvoke.return_value = _make_llm_response([])
        mock_get_llm.return_value = mock_llm_instance

        result = await generate_accounts(state, mock_config)

        assert result["accounts"] == []
        assert result["current_step"] == "error"
        assert "error" in result
        mock_llm_instance.ainvoke.assert_called_once()


class TestGenerateAccountPlans:
    @pytest.mark.asyncio
    @patch("app.agents.nodes.account_plan_gen.get_llm")
    async def test_generates_account_plan_list(self, mock_get_llm, base_state, mock_config):
        state = {
            **base_state,
            "accounts": [{"name": "Acme Corp", "code": "acme_corp", "id": "acc-123"}],
            "approved_plans": [{"name": "Standard", "code": "standard", "id": "plan-456"}],
        }

        account_plans = [
            {
                "accountId": "acc-123",
                "planId": "plan-456",
                "startDate": "2024-01-01",
            }
        ]
        mock_llm_instance = AsyncMock()
        mock_llm_instance.ainvoke.return_value = _make_llm_response(account_plans)
        mock_get_llm.return_value = mock_llm_instance

        result = await generate_account_plans(state, mock_config)

        assert len(result["account_plans"]) == 1
        assert result["account_plans"][0]["accountId"] == "acc-123"
        assert result["current_step"] == "account_plans_generated"

    @pytest.mark.asyncio
    @patch("app.agents.nodes.account_plan_gen.get_llm")
    async def test_returns_error_on_empty_result(self, mock_get_llm, base_state, mock_config):
        state = {
            **base_state,
            "accounts": [],
            "approved_plans": [],
        }

        mock_llm_instance = AsyncMock()
        mock_llm_instance.ainvoke.return_value = _make_llm_response([])
        mock_get_llm.return_value = mock_llm_instance

        result = await generate_account_plans(state, mock_config)
        assert result["current_step"] == "error"
        assert result["account_plans"] == []
        assert "error" in result


# ---------------------------------------------------------------------------
# Validation + Approval config tests for new entity types
# ---------------------------------------------------------------------------


class TestValidateNewEntityTypes:
    def test_step_to_entity_has_accounts_generated(self):
        assert "accounts_generated" in _STEP_TO_ENTITY

    def test_step_to_entity_has_account_plans_generated(self):
        assert "account_plans_generated" in _STEP_TO_ENTITY

    @pytest.mark.asyncio
    async def test_validates_accounts(self):
        state = {
            "current_step": "accounts_generated",
            "accounts": [
                {
                    "name": "Acme Corp",
                    "code": "acme_corp",
                    "email": "billing@acme.com",
                }
            ],
        }
        result = await validate_entities(state)
        assert "account_errors" in result
        assert result["current_step"] == "accounts_validated"

    @pytest.mark.asyncio
    async def test_validates_account_plans(self):
        state = {
            "current_step": "account_plans_generated",
            "account_plans": [
                {
                    "accountId": "acc-123",
                    "planId": "plan-456",
                    "startDate": "2024-01-01",
                }
            ],
        }
        result = await validate_entities(state)
        assert "account_plan_errors" in result
        assert result["current_step"] == "account_plans_validated"


class TestApprovalConfigNewEntityTypes:
    def test_approval_config_has_accounts_validated(self):
        from app.agents.nodes.approval import _STEP_CONFIG

        assert "accounts_validated" in _STEP_CONFIG
        config = _STEP_CONFIG["accounts_validated"]
        assert config[4] == "accounts_approved"

    def test_approval_config_has_account_plans_validated(self):
        from app.agents.nodes.approval import _STEP_CONFIG

        assert "account_plans_validated" in _STEP_CONFIG
        config = _STEP_CONFIG["account_plans_validated"]
        assert config[4] == "account_plans_approved"

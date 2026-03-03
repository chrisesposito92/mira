"""Unit tests for the usage_submission graph structure and generation nodes."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agents.graphs.usage_submission import _build_graph, route_after_load
from app.agents.nodes.load_approved_usage import load_approved_for_usage
from app.agents.nodes.measurement_gen import generate_measurements
from app.agents.nodes.validation import _STEP_TO_ENTITY, validate_entities


@pytest.fixture
def base_state() -> dict:
    """Base workflow state for usage submission testing."""
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


class TestUsageSubmissionGraphStructure:
    def test_graph_has_all_expected_nodes(self):
        graph = _build_graph()
        expected_nodes = {
            "load_approved_for_usage",
            "generate_measurements",
            "validate_measurements",
            "approve_measurements",
        }
        node_names = {name for name in graph.nodes if not name.startswith("__")}
        assert expected_nodes == node_names

    def test_graph_entry_point_is_load_approved(self):
        graph = _build_graph()
        assert "load_approved_for_usage" in graph.nodes

    def test_graph_compiles_without_checkpointer(self):
        graph = _build_graph()
        compiled = graph.compile()
        assert compiled is not None

    def test_graph_has_correct_node_count(self):
        graph = _build_graph()
        non_internal_nodes = {name for name in graph.nodes if not name.startswith("__")}
        assert len(non_internal_nodes) == 4

    def test_route_after_load_returns_end_on_error(self):
        """Load node should route to END when current_step is 'error'."""
        from langgraph.graph import END

        assert route_after_load({"current_step": "error"}) == END
        loaded = "approved_entities_loaded_for_usage"
        assert route_after_load({"current_step": loaded}) == "generate_measurements"


# ---------------------------------------------------------------------------
# Load approved entities tests
# ---------------------------------------------------------------------------


class TestLoadApprovedForUsage:
    @pytest.mark.asyncio
    @patch("app.agents.nodes.load_approved_usage.get_supabase_client")
    async def test_loads_approved_entities_from_db(self, mock_supabase, base_state):
        mock_client = MagicMock()

        # Mock meters result
        mock_meters_result = MagicMock()
        mock_meters_result.data = [
            {
                "id": "meter-aaa",
                "entity_type": "meter",
                "data": {"name": "API Requests", "code": "api_requests"},
            },
        ]

        # Mock accounts result
        mock_accounts_result = MagicMock()
        mock_accounts_result.data = [
            {
                "id": "acc-bbb",
                "entity_type": "account",
                "data": {"name": "Acme Corp", "code": "acme_corp"},
            },
        ]

        # Mock workflows queries
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
                    builder.execute.return_value = mock_meters_result
                else:
                    builder.execute.return_value = mock_accounts_result
            elif name == "workflows":
                builder.execute.return_value = mock_wf_result
            return builder

        mock_client.table = table_side_effect
        mock_supabase.return_value = mock_client

        result = await load_approved_for_usage(base_state)

        assert len(result["approved_meters"]) == 1
        assert result["approved_meters"][0]["id"] == "meter-aaa"
        assert len(result["approved_accounts"]) == 1
        assert result["approved_accounts"][0]["id"] == "acc-bbb"
        assert result["current_step"] == "approved_entities_loaded_for_usage"

    @pytest.mark.asyncio
    @patch("app.agents.nodes.load_approved_usage.get_supabase_client")
    async def test_errors_when_only_meters_present(self, mock_supabase, base_state):
        """WF4 should fail if accounts are missing even when meters exist."""
        mock_client = MagicMock()

        mock_meters_result = MagicMock()
        mock_meters_result.data = [
            {
                "id": "meter-aaa",
                "entity_type": "meter",
                "data": {"name": "API Requests", "code": "api_requests"},
            },
        ]

        mock_empty_result = MagicMock()
        mock_empty_result.data = []

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
                    builder.execute.return_value = mock_meters_result
                else:
                    builder.execute.return_value = mock_empty_result
            elif name == "workflows":
                builder.execute.return_value = mock_wf_result
            return builder

        mock_client.table = table_side_effect
        mock_supabase.return_value = mock_client

        result = await load_approved_for_usage(base_state)

        assert "error" in result
        assert result["current_step"] == "error"
        assert "accounts" in result["error"].lower()

    @pytest.mark.asyncio
    @patch("app.agents.nodes.load_approved_usage.get_supabase_client")
    async def test_handles_empty_approved_entities(self, mock_supabase, base_state):
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

        result = await load_approved_for_usage(base_state)

        assert "error" in result
        assert result["current_step"] == "error"


# ---------------------------------------------------------------------------
# Generation node tests
# ---------------------------------------------------------------------------


class TestGenerateMeasurements:
    @pytest.mark.asyncio
    @patch("app.agents.nodes.measurement_gen.get_llm")
    async def test_generates_measurement_list(self, mock_get_llm, base_state):
        state = {
            **base_state,
            "approved_meters": [
                {
                    "name": "API Requests",
                    "code": "api_requests",
                    "dataFields": [{"code": "requests", "category": "MEASURE"}],
                }
            ],
            "approved_accounts": [{"name": "Acme Corp", "code": "acme_corp"}],
        }

        measurements = [
            {
                "uid": "meas-001",
                "meter": "api_requests",
                "account": "acme_corp",
                "ts": "2024-01-15T10:30:00Z",
                "data": {"requests": 150},
            }
        ]
        mock_llm_instance = AsyncMock()
        mock_llm_instance.ainvoke.return_value = _make_llm_response(measurements)
        mock_get_llm.return_value = mock_llm_instance

        result = await generate_measurements(state)

        assert len(result["measurements"]) == 1
        assert result["measurements"][0]["uid"] == "meas-001"
        assert result["current_step"] == "measurements_generated"

    @pytest.mark.asyncio
    @patch("app.agents.nodes.measurement_gen.get_llm")
    async def test_returns_error_on_empty_result(self, mock_get_llm, base_state):
        state = {
            **base_state,
            "approved_meters": [],
            "approved_accounts": [],
        }

        mock_llm_instance = AsyncMock()
        mock_llm_instance.ainvoke.return_value = _make_llm_response([])
        mock_get_llm.return_value = mock_llm_instance

        result = await generate_measurements(state)
        assert result["current_step"] == "error"
        assert result["measurements"] == []
        assert "error" in result


# ---------------------------------------------------------------------------
# Validation + Approval config tests for new entity types
# ---------------------------------------------------------------------------


class TestValidateNewEntityTypes:
    def test_step_to_entity_has_measurements_generated(self):
        assert "measurements_generated" in _STEP_TO_ENTITY

    @pytest.mark.asyncio
    async def test_validates_measurements(self):
        state = {
            "current_step": "measurements_generated",
            "measurements": [
                {
                    "uid": "meas-001",
                    "meter": "api_requests",
                    "account": "acme_corp",
                    "ts": "2024-01-15T10:30:00Z",
                    "data": {"requests": 150},
                }
            ],
        }
        result = await validate_entities(state)
        assert "measurement_errors" in result
        assert result["current_step"] == "measurements_validated"


class TestApprovalConfigNewEntityTypes:
    def test_approval_config_has_measurements_validated(self):
        from app.agents.nodes.approval import _STEP_CONFIG

        assert "measurements_validated" in _STEP_CONFIG
        config = _STEP_CONFIG["measurements_validated"]
        assert config[4] == "measurements_approved"

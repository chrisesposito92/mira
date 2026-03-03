"""Tests for LangGraph agent nodes with mocked LLM responses."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agents.nodes.analysis import analyze_use_case
from app.agents.nodes.clarification import generate_clarifications
from app.agents.nodes.generation import (
    generate_aggregations,
    generate_meters,
    generate_products,
)
from app.agents.nodes.validation import validate_entities


@pytest.fixture
def mock_llm() -> AsyncMock:
    """Create a mock LLM that returns configurable JSON responses."""
    llm = AsyncMock()
    return llm


@pytest.fixture
def base_state() -> dict:
    """Base workflow state for testing."""
    return {
        "use_case_id": "uc-111",
        "project_id": "proj-222",
        "model_id": "claude-sonnet-4-6",
        "user_id": "user-333",
    }


def _make_llm_response(content: str | dict) -> MagicMock:
    """Create a mock LLM response with content attribute."""
    response = MagicMock()
    response.content = json.dumps(content) if isinstance(content, dict | list) else content
    return response


class TestAnalyzeUseCase:
    @pytest.mark.asyncio
    @patch("app.agents.nodes.analysis.rag_retrieve", new_callable=AsyncMock)
    @patch("app.agents.nodes.analysis.get_llm")
    @patch("app.agents.nodes.analysis.get_supabase_client")
    async def test_successful_analysis(
        self, mock_supabase, mock_get_llm, mock_rag, base_state, mock_config
    ):
        # Mock Supabase query
        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.data = [
            {
                "id": "uc-111",
                "title": "API Usage Billing",
                "description": "Bill customers based on API calls",
                "target_billing_model": "per-request",
                "billing_frequency": "monthly",
                "notes": None,
            }
        ]
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            mock_result
        )
        mock_supabase.return_value = mock_client

        # Mock RAG
        mock_rag.return_value = "Relevant m3ter documentation context..."

        # Mock LLM
        llm_response = _make_llm_response(
            {
                "analysis": "This use case requires an API product with request metering",
                "needs_clarification": False,
                "products_needed": ["API Gateway"],
                "meters_needed": ["API Request Meter"],
                "aggregations_needed": ["Daily API Count"],
                "reasoning": "Simple per-request billing model",
            }
        )
        mock_llm_instance = AsyncMock()
        mock_llm_instance.ainvoke.return_value = llm_response
        mock_get_llm.return_value = mock_llm_instance

        result = await analyze_use_case(base_state, mock_config)

        assert "analysis" in result
        assert result["needs_clarification"] is False
        assert result["current_step"] == "analysis_complete"
        assert result["use_case"] is not None
        assert "rag_context" in result
        mock_rag.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.agents.nodes.analysis.rag_retrieve", new_callable=AsyncMock)
    @patch("app.agents.nodes.analysis.get_llm")
    @patch("app.agents.nodes.analysis.get_supabase_client")
    async def test_use_case_not_found(
        self, mock_supabase, mock_get_llm, mock_rag, base_state, mock_config
    ):
        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.data = []
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            mock_result
        )
        mock_supabase.return_value = mock_client

        result = await analyze_use_case(base_state, mock_config)
        assert result.get("error") is not None
        assert result["current_step"] == "error"


class TestGenerateClarifications:
    @pytest.mark.asyncio
    @patch("app.agents.nodes.clarification.interrupt")
    @patch("app.agents.nodes.clarification.get_llm")
    async def test_generates_questions_and_interrupts(
        self, mock_get_llm, mock_interrupt, base_state
    ):
        state = {**base_state, "analysis": "Analysis text here"}

        # Mock LLM
        questions = [
            {
                "question": "What granularity for API metering?",
                "options": [
                    {"label": "Per request", "description": "Count each API call"},
                    {"label": "Per minute", "description": "Aggregate by minute"},
                ],
                "recommendation": "Per request",
            }
        ]
        mock_llm_instance = AsyncMock()
        mock_llm_instance.ainvoke.return_value = _make_llm_response(questions)
        mock_get_llm.return_value = mock_llm_instance

        # Mock interrupt to return user answers
        mock_interrupt.return_value = [{"question_index": 0, "selected_option": 0}]

        result = await generate_clarifications(state)

        assert "clarification_questions" in result
        assert len(result["clarification_questions"]) == 1
        assert "clarification_answers" in result
        assert result["needs_clarification"] is False
        mock_interrupt.assert_called_once()


class TestGenerateProducts:
    @pytest.mark.asyncio
    @patch("app.agents.nodes.generation.get_llm")
    async def test_generates_product_list(self, mock_get_llm, base_state, mock_config):
        state = {
            **base_state,
            "analysis": "Need an API product",
            "rag_context": "m3ter docs...",
        }

        products = [
            {"name": "API Gateway", "code": "api_gateway"},
            {"name": "Data Storage", "code": "data_storage"},
        ]
        mock_llm_instance = AsyncMock()
        mock_llm_instance.ainvoke.return_value = _make_llm_response(products)
        mock_get_llm.return_value = mock_llm_instance

        result = await generate_products(state, mock_config)

        assert len(result["products"]) == 2
        assert result["products"][0]["name"] == "API Gateway"
        assert result["current_step"] == "products_generated"


class TestGenerateMeters:
    @pytest.mark.asyncio
    @patch("app.agents.nodes.generation.get_llm")
    async def test_generates_meter_list(self, mock_get_llm, base_state, mock_config):
        state = {
            **base_state,
            "analysis": "Need API request metering",
            "rag_context": "m3ter docs...",
            "products": [{"name": "API Gateway", "code": "api_gateway"}],
        }

        meters = [
            {
                "name": "API Request Meter",
                "code": "api_request_meter",
                "dataFields": [
                    {"code": "request_count", "category": "MEASURE", "unit": "requests"},
                ],
            }
        ]
        mock_llm_instance = AsyncMock()
        mock_llm_instance.ainvoke.return_value = _make_llm_response(meters)
        mock_get_llm.return_value = mock_llm_instance

        result = await generate_meters(state, mock_config)

        assert len(result["meters"]) == 1
        assert result["meters"][0]["code"] == "api_request_meter"
        assert result["current_step"] == "meters_generated"


class TestGenerateAggregations:
    @pytest.mark.asyncio
    @patch("app.agents.nodes.generation.get_llm")
    async def test_generates_aggregation_list(self, mock_get_llm, base_state, mock_config):
        state = {
            **base_state,
            "analysis": "Need daily request aggregation",
            "rag_context": "m3ter docs...",
            "products": [{"name": "API Gateway", "code": "api_gateway"}],
            "meters": [
                {
                    "name": "API Request Meter",
                    "code": "api_request_meter",
                    "dataFields": [
                        {"code": "request_count", "category": "MEASURE"},
                    ],
                }
            ],
        }

        aggregations = [
            {
                "name": "Daily API Count",
                "code": "daily_api_count",
                "meterCode": "api_request_meter",
                "aggregationType": "SUM",
                "targetField": "request_count",
            }
        ]
        mock_llm_instance = AsyncMock()
        mock_llm_instance.ainvoke.return_value = _make_llm_response(aggregations)
        mock_get_llm.return_value = mock_llm_instance

        result = await generate_aggregations(state, mock_config)

        assert len(result["aggregations"]) == 1
        assert result["aggregations"][0]["aggregationType"] == "SUM"
        assert result["current_step"] == "aggregations_generated"


class TestValidateEntities:
    @pytest.mark.asyncio
    async def test_validates_products_with_no_errors(self):
        state = {
            "current_step": "products_generated",
            "products": [{"name": "API Gateway", "code": "api_gateway"}],
        }
        result = await validate_entities(state)
        assert result["product_errors"] == []
        assert result["current_step"] == "products_validated"

    @pytest.mark.asyncio
    async def test_validates_products_with_errors(self):
        state = {
            "current_step": "products_generated",
            "products": [{"name": "", "code": "API-BAD"}],
        }
        result = await validate_entities(state)
        assert len(result["product_errors"]) > 0
        assert result["product_errors"][0]["entity_index"] == 0

    @pytest.mark.asyncio
    async def test_validates_meters(self):
        state = {
            "current_step": "meters_generated",
            "meters": [
                {
                    "name": "Test Meter",
                    "code": "test_meter",
                    "dataFields": [{"code": "count", "category": "MEASURE"}],
                }
            ],
        }
        result = await validate_entities(state)
        assert result["meter_errors"] == []
        assert result["current_step"] == "meters_validated"

    @pytest.mark.asyncio
    async def test_validates_aggregations(self):
        state = {
            "current_step": "aggregations_generated",
            "aggregations": [
                {
                    "name": "Daily Count",
                    "code": "daily_count",
                    "aggregationType": "SUM",
                    "targetField": "count",
                }
            ],
        }
        result = await validate_entities(state)
        assert result["aggregation_errors"] == []
        assert result["current_step"] == "aggregations_validated"

    @pytest.mark.asyncio
    async def test_unknown_step_returns_empty(self):
        state = {"current_step": "unknown_step"}
        result = await validate_entities(state)
        assert result == {}

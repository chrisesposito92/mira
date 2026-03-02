"""Tests for use case generator: REST extract-text endpoint, graph structure, and node logic."""

import io
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from tests.conftest import MOCK_USER_ID

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _project_row(**overrides):
    defaults = {
        "id": str(uuid4()),
        "user_id": str(MOCK_USER_ID),
        "name": "Test Project",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }
    defaults.update(overrides)
    return defaults


# ---------------------------------------------------------------------------
# REST: extract-text endpoint
# ---------------------------------------------------------------------------


class TestExtractText:
    def test_extract_text_from_txt(self, authed_client, mock_supabase):
        pid = str(uuid4())
        mock_supabase._table_data["projects"] = [_project_row(id=pid)]
        resp = authed_client.post(
            f"/api/projects/{pid}/generate-use-cases/extract-text",
            files={"file": ("notes.txt", io.BytesIO(b"Hello world"), "text/plain")},
        )
        assert resp.status_code == 200
        assert resp.json()["text"] == "Hello world"

    def test_reject_unsupported_file_type(self, authed_client, mock_supabase):
        pid = str(uuid4())
        mock_supabase._table_data["projects"] = [_project_row(id=pid)]
        resp = authed_client.post(
            f"/api/projects/{pid}/generate-use-cases/extract-text",
            files={"file": ("virus.exe", io.BytesIO(b"data"), "application/octet-stream")},
        )
        assert resp.status_code == 400
        assert "Unsupported file type" in resp.json()["detail"]

    def test_reject_empty_file(self, authed_client, mock_supabase):
        pid = str(uuid4())
        mock_supabase._table_data["projects"] = [_project_row(id=pid)]
        resp = authed_client.post(
            f"/api/projects/{pid}/generate-use-cases/extract-text",
            files={"file": ("empty.txt", io.BytesIO(b""), "text/plain")},
        )
        assert resp.status_code == 400
        assert "No text content" in resp.json()["detail"]

    def test_reject_whitespace_only_file(self, authed_client, mock_supabase):
        pid = str(uuid4())
        mock_supabase._table_data["projects"] = [_project_row(id=pid)]
        resp = authed_client.post(
            f"/api/projects/{pid}/generate-use-cases/extract-text",
            files={"file": ("spaces.txt", io.BytesIO(b"   \n\t  "), "text/plain")},
        )
        assert resp.status_code == 400
        assert "No text content" in resp.json()["detail"]

    def test_unauthorized_wrong_owner(self, authed_client, mock_supabase):
        pid = str(uuid4())
        mock_supabase._table_data["projects"] = [
            _project_row(id=pid, user_id=str(uuid4()))  # different owner
        ]
        resp = authed_client.post(
            f"/api/projects/{pid}/generate-use-cases/extract-text",
            files={"file": ("notes.txt", io.BytesIO(b"hello"), "text/plain")},
        )
        assert resp.status_code == 404
        assert "Project not found" in resp.json()["detail"]

    def test_project_not_found(self, authed_client, mock_supabase):
        mock_supabase._table_data["projects"] = []
        resp = authed_client.post(
            f"/api/projects/{uuid4()}/generate-use-cases/extract-text",
            files={"file": ("notes.txt", io.BytesIO(b"hello"), "text/plain")},
        )
        assert resp.status_code == 404

    def test_reject_file_too_large(self, authed_client, mock_supabase):
        pid = str(uuid4())
        mock_supabase._table_data["projects"] = [_project_row(id=pid)]
        large = b"x" * (10 * 1024 * 1024 + 1)
        resp = authed_client.post(
            f"/api/projects/{pid}/generate-use-cases/extract-text",
            files={"file": ("big.txt", io.BytesIO(large), "text/plain")},
        )
        assert resp.status_code == 400
        assert "10 MB" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# Graph structure
# ---------------------------------------------------------------------------


class TestUseCaseGenGraph:
    def test_graph_has_expected_nodes(self):
        from app.agents.graphs.use_case_gen import _build_graph

        graph = _build_graph()
        node_names = {name for name in graph.nodes if not name.startswith("__")}
        assert node_names == {"research_customer", "ask_clarification", "compile_use_cases"}

    def test_graph_compiles(self):
        from langgraph.checkpoint.memory import MemorySaver

        from app.agents.graphs.use_case_gen import _build_graph

        graph = _build_graph()
        compiled = graph.compile(checkpointer=MemorySaver())
        assert compiled is not None

    def test_should_clarify_true(self):
        from app.agents.graphs.use_case_gen import _should_clarify

        assert _should_clarify({"needs_clarification": True}) == "ask_clarification"

    def test_should_clarify_false(self):
        from app.agents.graphs.use_case_gen import _should_clarify

        assert _should_clarify({"needs_clarification": False}) == "compile_use_cases"

    def test_should_clarify_missing_key(self):
        from app.agents.graphs.use_case_gen import _should_clarify

        assert _should_clarify({}) == "compile_use_cases"


# ---------------------------------------------------------------------------
# Node unit tests
# ---------------------------------------------------------------------------


class TestCompileUseCasesNode:
    @pytest.mark.asyncio
    async def test_compile_returns_use_cases(self):
        """compile_use_cases with mocked LLM produces UseCaseCreate-compatible dicts."""
        from app.agents.nodes.use_case_compile import compile_use_cases

        mock_response = MagicMock()
        mock_response.content = json.dumps(
            [
                {
                    "title": "API Metering",
                    "description": "Meter API calls per customer",
                    "billing_frequency": "monthly",
                    "currency": "USD",
                    "target_billing_model": "usage_based",
                    "notes": "Per-request pricing",
                }
            ]
        )

        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)

        state = {
            "model_id": "gpt-5.2",
            "customer_name": "Acme Corp",
            "research_results": "Acme is an API company.",
            "num_use_cases": 1,
            "notes": "",
            "attachment_text": "",
            "clarification_answers": [],
        }

        with patch("app.agents.nodes.use_case_compile.get_llm", return_value=mock_llm):
            result = await compile_use_cases(state)

        generated = result["generated_use_cases"]
        assert len(generated) == 1
        assert generated[0]["title"] == "API Metering"
        assert generated[0]["description"] == "Meter API calls per customer"
        assert generated[0]["currency"] == "USD"
        assert result["current_step"] == "compile_complete"

    @pytest.mark.asyncio
    async def test_compile_fallback_on_invalid_json(self):
        """compile_use_cases creates a fallback use case when LLM returns invalid JSON."""
        from app.agents.nodes.use_case_compile import compile_use_cases

        mock_response = MagicMock()
        mock_response.content = "This is not valid JSON at all"

        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)

        state = {
            "model_id": "gpt-5.2",
            "customer_name": "Acme Corp",
            "research_results": "Some research.",
            "num_use_cases": 1,
        }

        with patch("app.agents.nodes.use_case_compile.get_llm", return_value=mock_llm):
            result = await compile_use_cases(state)

        generated = result["generated_use_cases"]
        assert len(generated) == 1
        assert "Acme Corp" in generated[0]["title"]


class TestResearchCustomerNode:
    @pytest.mark.asyncio
    async def test_research_with_results(self):
        """research_customer with mocked Tavily + LLM returns structured research."""
        from app.agents.nodes.use_case_research import research_customer

        mock_response = MagicMock()
        mock_response.content = json.dumps(
            {
                "research_summary": "Acme Corp provides API services for developers.",
                "needs_clarification": False,
            }
        )

        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)

        state = {
            "customer_name": "Acme Corp",
            "model_id": "gpt-5.2",
            "notes": "They do API metering",
            "attachment_text": "",
        }

        with (
            patch(
                "app.agents.nodes.use_case_research._run_tavily_searches",
                AsyncMock(return_value="Acme Corp is a tech company..."),
            ),
            patch("app.agents.nodes.use_case_research.get_llm", return_value=mock_llm),
        ):
            result = await research_customer(state)

        assert "Acme Corp" in result["research_results"]
        assert result["needs_clarification"] is False
        assert result["current_step"] == "research_complete"

    @pytest.mark.asyncio
    async def test_research_fallback_on_no_results(self):
        """research_customer returns fallback when Tavily returns nothing."""
        from app.agents.nodes.use_case_research import research_customer

        state = {
            "customer_name": "Unknown Corp",
            "model_id": "gpt-5.2",
            "notes": "",
            "attachment_text": "",
        }

        with patch(
            "app.agents.nodes.use_case_research._run_tavily_searches",
            AsyncMock(return_value=""),
        ):
            result = await research_customer(state)

        assert "no results" in result["research_results"].lower()
        assert result["needs_clarification"] is False

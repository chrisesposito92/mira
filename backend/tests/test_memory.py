"""Tests for the core memory module (app.agents.memory)."""

import pytest
from langgraph.store.memory import InMemoryStore

from app.agents.memory import (
    build_entity_summary,
    build_memory_context,
    build_workflow_summary_text,
    format_memory_section,
    get_store_from_config,
    get_workflow_num_for_step,
    load_correction_patterns,
    load_project_context,
    load_workflow_history,
    save_analysis_context,
    save_user_corrections,
    save_workflow_summary,
)

# ---------------------------------------------------------------------------
# get_store_from_config
# ---------------------------------------------------------------------------


class TestGetStoreFromConfig:
    def test_returns_store_when_present(self):
        store = InMemoryStore()

        class Runtime:
            pass

        runtime = Runtime()
        runtime.store = store
        config = {"configurable": {"__pregel_runtime": runtime}}
        assert get_store_from_config(config) is store

    def test_returns_none_on_missing_runtime(self):
        config = {"configurable": {}}
        assert get_store_from_config(config) is None

    def test_returns_none_on_missing_configurable(self):
        config = {}
        assert get_store_from_config(config) is None

    def test_returns_none_on_none_config(self):
        # Defensive — should not crash
        assert get_store_from_config({}) is None


# ---------------------------------------------------------------------------
# UC1: save / load project context
# ---------------------------------------------------------------------------


class TestProjectContext:
    @pytest.mark.asyncio
    async def test_save_and_load_analysis(self):
        store = InMemoryStore()
        await save_analysis_context(
            store,
            project_id="proj-1",
            use_case_id="uc-1",
            analysis="API billing requires per-request metering",
            use_case={"title": "API Usage", "description": "Bill per API call"},
        )

        result = await load_project_context(store, "proj-1")
        assert "API Usage" in result
        assert "API billing requires per-request metering" in result

    @pytest.mark.asyncio
    async def test_load_empty_project(self):
        store = InMemoryStore()
        result = await load_project_context(store, "proj-nonexistent")
        assert result == ""

    @pytest.mark.asyncio
    async def test_multiple_analyses_loaded(self):
        store = InMemoryStore()
        for i in range(3):
            await save_analysis_context(
                store,
                project_id="proj-1",
                use_case_id=f"uc-{i}",
                analysis=f"Analysis {i}",
                use_case={"title": f"Use Case {i}"},
            )

        result = await load_project_context(store, "proj-1")
        for i in range(3):
            assert f"Use Case {i}" in result


class TestCorrectionPatterns:
    @pytest.mark.asyncio
    async def test_save_and_load_corrections(self):
        store = InMemoryStore()
        corrections = [
            {"summary": "Changed code from camelCase to snake_case"},
            {"summary": "Added custom field 'tier'"},
        ]
        await save_user_corrections(
            store,
            project_id="proj-1",
            use_case_id="uc-1",
            entity_type="product",
            corrections=corrections,
        )

        result = await load_correction_patterns(store, "proj-1")
        assert "product" in result
        assert "snake_case" in result

    @pytest.mark.asyncio
    async def test_empty_corrections_skipped(self):
        store = InMemoryStore()
        await save_user_corrections(
            store,
            project_id="proj-1",
            use_case_id="uc-1",
            entity_type="product",
            corrections=[],
        )
        result = await load_correction_patterns(store, "proj-1")
        assert result == ""

    @pytest.mark.asyncio
    async def test_corrections_capped_at_50(self):
        store = InMemoryStore()
        corrections = [{"summary": f"Correction {i}"} for i in range(60)]
        await save_user_corrections(
            store,
            project_id="proj-1",
            use_case_id="uc-1",
            entity_type="meter",
            corrections=corrections,
        )
        # Verify stored count is capped
        item = await store.aget(("project", "proj-1", "analysis"), "corrections_uc-1_meter")
        assert len(item.value["corrections"]) == 50

    @pytest.mark.asyncio
    async def test_corrections_merge_with_existing(self):
        store = InMemoryStore()
        first_batch = [{"summary": f"First {i}"} for i in range(5)]
        await save_user_corrections(
            store,
            project_id="proj-1",
            use_case_id="uc-1",
            entity_type="product",
            corrections=first_batch,
        )
        second_batch = [{"summary": f"Second {i}"} for i in range(3)]
        await save_user_corrections(
            store,
            project_id="proj-1",
            use_case_id="uc-1",
            entity_type="product",
            corrections=second_batch,
        )
        item = await store.aget(("project", "proj-1", "analysis"), "corrections_uc-1_product")
        assert len(item.value["corrections"]) == 8


# ---------------------------------------------------------------------------
# UC3: Workflow history
# ---------------------------------------------------------------------------


class TestWorkflowHistory:
    @pytest.mark.asyncio
    async def test_save_and_load_summary(self):
        store = InMemoryStore()
        await save_workflow_summary(
            store,
            project_id="proj-1",
            use_case_id="uc-1",
            workflow_num=1,
            entity_summary="Products (2): API Gateway, Data Pipeline",
        )

        result = await load_workflow_history(store, "proj-1", up_to_wf=2)
        assert "Workflow 1" in result
        assert "API Gateway" in result

    @pytest.mark.asyncio
    async def test_load_filters_by_workflow_num(self):
        store = InMemoryStore()
        await save_workflow_summary(
            store,
            project_id="proj-1",
            use_case_id="uc-1",
            workflow_num=1,
            entity_summary="WF1 entities",
        )
        await save_workflow_summary(
            store,
            project_id="proj-1",
            use_case_id="uc-1",
            workflow_num=2,
            entity_summary="WF2 entities",
        )
        await save_workflow_summary(
            store,
            project_id="proj-1",
            use_case_id="uc-1",
            workflow_num=3,
            entity_summary="WF3 entities",
        )

        # up_to_wf=2 should only load WF1
        result = await load_workflow_history(store, "proj-1", up_to_wf=2)
        assert "WF1 entities" in result
        assert "WF2 entities" not in result
        assert "WF3 entities" not in result

        # up_to_wf=4 should load WF1, WF2, WF3
        result = await load_workflow_history(store, "proj-1", up_to_wf=4)
        assert "WF1 entities" in result
        assert "WF2 entities" in result
        assert "WF3 entities" in result

    @pytest.mark.asyncio
    async def test_empty_workflow_history(self):
        store = InMemoryStore()
        result = await load_workflow_history(store, "proj-1", up_to_wf=2)
        assert result == ""

    @pytest.mark.asyncio
    async def test_overwrite_on_rerun(self):
        store = InMemoryStore()
        await save_workflow_summary(
            store,
            project_id="proj-1",
            use_case_id="uc-1",
            workflow_num=1,
            entity_summary="First run",
        )
        await save_workflow_summary(
            store,
            project_id="proj-1",
            use_case_id="uc-1",
            workflow_num=1,
            entity_summary="Second run",
        )
        result = await load_workflow_history(store, "proj-1", up_to_wf=2)
        assert "Second run" in result
        assert "First run" not in result


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class TestHelpers:
    def test_get_workflow_num_for_step(self):
        assert get_workflow_num_for_step("aggregations_approved") == 1
        assert get_workflow_num_for_step("pricing_approved") == 2
        assert get_workflow_num_for_step("account_plans_approved") == 3
        assert get_workflow_num_for_step("measurements_approved") == 4
        assert get_workflow_num_for_step("unknown_step") is None

    def test_build_entity_summary(self):
        entities = [{"name": "API Gateway"}, {"code": "data_pipeline"}]
        result = build_entity_summary("products", entities, "Products")
        assert "Products (2)" in result
        assert "API Gateway" in result
        assert "data_pipeline" in result

    def test_build_entity_summary_empty(self):
        result = build_entity_summary("products", [], "Products")
        assert result == ""

    def test_build_workflow_summary_text_wf1(self):
        state = {
            "products": [{"name": "API Gateway"}],
            "meters": [{"name": "API Calls Meter"}],
            "aggregations": [{"name": "Total API Calls"}],
            "analysis": "Per-request billing",
        }
        result = build_workflow_summary_text(state, workflow_num=1)
        assert "Products" in result
        assert "Meters" in result
        assert "Aggregations" in result
        assert "Per-request billing" in result

    def test_build_workflow_summary_text_empty_state(self):
        result = build_workflow_summary_text({}, workflow_num=1)
        assert result == ""

    def test_format_memory_section(self):
        result = format_memory_section("Project Memory", "Some context here")
        assert "## Project Memory" in result
        assert "Some context here" in result

    def test_format_memory_section_empty(self):
        result = format_memory_section("Project Memory", "")
        assert result == ""

    def test_build_memory_context_all_populated(self):
        mem = build_memory_context(
            project_memory="project info",
            correction_patterns="corrections",
            user_preferences="preferences",
            workflow_history="history",
        )
        assert "## Project Memory" in mem["project_memory"]
        assert "## Correction Patterns" in mem["correction_patterns"]
        assert "## User Preferences" in mem["user_preferences"]
        assert "## Prior Workflow Context" in mem["workflow_history"]

    def test_build_memory_context_all_empty(self):
        mem = build_memory_context()
        assert mem["project_memory"] == ""
        assert mem["correction_patterns"] == ""
        assert mem["user_preferences"] == ""
        assert mem["workflow_history"] == ""

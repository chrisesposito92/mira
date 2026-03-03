"""Tests for user decision memory (app.agents.memory_decisions)."""

import pytest
from langgraph.store.memory import InMemoryStore

from app.agents.memory_decisions import (
    compute_entity_diff,
    format_preferences_for_prompt,
    retrieve_user_preferences,
    store_rejection_signal,
    store_user_preferences,
)

# ---------------------------------------------------------------------------
# compute_entity_diff
# ---------------------------------------------------------------------------


class TestComputeEntityDiff:
    def test_no_changes(self):
        entity = {"name": "Test", "code": "test_code"}
        diffs = compute_entity_diff(entity, entity, "product")
        assert diffs == []

    def test_code_change_snake_case(self):
        original = {"code": "testCode"}
        edited = {"code": "test_code"}
        diffs = compute_entity_diff(original, edited, "product")
        assert len(diffs) == 1
        assert diffs[0]["pattern"] == "prefers_snake_case"
        assert diffs[0]["field"] == "code"

    def test_code_change_kebab_case(self):
        original = {"code": "test_code"}
        edited = {"code": "test-code"}
        diffs = compute_entity_diff(original, edited, "product")
        assert len(diffs) == 1
        assert diffs[0]["pattern"] == "prefers_kebab_case"

    def test_code_change_camel_case(self):
        original = {"code": "test_code"}
        edited = {"code": "testCode"}
        diffs = compute_entity_diff(original, edited, "product")
        assert len(diffs) == 1
        assert diffs[0]["pattern"] == "prefers_camelCase"

    def test_currency_change(self):
        original = {"currency": "USD"}
        edited = {"currency": "EUR"}
        diffs = compute_entity_diff(original, edited, "plan_template")
        currency_diffs = [d for d in diffs if d["field"] == "currency"]
        assert len(currency_diffs) == 1
        assert currency_diffs[0]["pattern"] == "prefers_currency_EUR"

    def test_bill_frequency_change(self):
        original = {"billFrequency": "MONTHLY"}
        edited = {"billFrequency": "ANNUALLY"}
        diffs = compute_entity_diff(original, edited, "plan_template")
        freq_diffs = [d for d in diffs if d["field"] == "billFrequency"]
        assert len(freq_diffs) == 1
        assert freq_diffs[0]["pattern"] == "prefers_billing_annually"

    def test_custom_fields_added(self):
        original = {"customFields": {"tier": "standard"}}
        edited = {"customFields": {"tier": "standard", "region": "us-east"}}
        diffs = compute_entity_diff(original, edited, "product")
        cf_diffs = [d for d in diffs if d["field"] == "customFields"]
        assert len(cf_diffs) == 1
        assert "custom_fields_added:region" in cf_diffs[0]["pattern"]

    def test_custom_fields_removed(self):
        original = {"customFields": {"tier": "standard", "region": "us-east"}}
        edited = {"customFields": {"tier": "standard"}}
        diffs = compute_entity_diff(original, edited, "product")
        cf_diffs = [d for d in diffs if d["field"] == "customFields"]
        assert len(cf_diffs) == 1
        assert "custom_fields_removed:region" in cf_diffs[0]["pattern"]

    def test_name_change(self):
        original = {"name": "Old Name"}
        edited = {"name": "New Name"}
        diffs = compute_entity_diff(original, edited, "product")
        assert len(diffs) == 1
        assert diffs[0]["pattern"] == "field_modified:name"

    def test_only_tracked_fields(self):
        # 'untracked_field' should not appear in diffs
        original = {"name": "Test", "untracked_field": "old"}
        edited = {"name": "Test", "untracked_field": "new"}
        diffs = compute_entity_diff(original, edited, "product")
        assert diffs == []

    def test_entity_specific_fields_tracked(self):
        original = {"aggregationType": "SUM"}
        edited = {"aggregationType": "COUNT"}
        diffs = compute_entity_diff(original, edited, "aggregation")
        assert len(diffs) == 1
        assert diffs[0]["field"] == "aggregationType"


# ---------------------------------------------------------------------------
# store_user_preferences + retrieve
# ---------------------------------------------------------------------------


class TestStoreAndRetrievePreferences:
    @pytest.mark.asyncio
    async def test_store_and_retrieve(self):
        store = InMemoryStore()
        diffs = [
            {"pattern": "prefers_snake_case", "summary": "Changed code to snake_case"},
        ]
        await store_user_preferences(store, "user-1", "product", diffs)

        prefs = await retrieve_user_preferences(store, "user-1", "product")
        assert len(prefs) == 1
        assert prefs[0]["pattern"] == "prefers_snake_case"
        assert prefs[0]["weight"] == 0.5
        assert prefs[0]["count"] == 1

    @pytest.mark.asyncio
    async def test_weight_increases_with_observations(self):
        store = InMemoryStore()
        diff = [{"pattern": "prefers_snake_case", "summary": "Observation"}]

        # 3 observations: weight should be 0.5 + 0.1 + 0.1 = 0.7
        await store_user_preferences(store, "user-1", "product", diff)
        await store_user_preferences(store, "user-1", "product", diff)
        await store_user_preferences(store, "user-1", "product", diff)

        prefs = await retrieve_user_preferences(store, "user-1", "product")
        assert len(prefs) == 1
        assert prefs[0]["weight"] == 0.7
        assert prefs[0]["count"] == 3

    @pytest.mark.asyncio
    async def test_weight_capped_at_1(self):
        store = InMemoryStore()
        diff = [{"pattern": "prefers_snake_case", "summary": "Observation"}]

        for _ in range(20):
            await store_user_preferences(store, "user-1", "product", diff)

        prefs = await retrieve_user_preferences(store, "user-1", "product")
        assert prefs[0]["weight"] == 1.0

    @pytest.mark.asyncio
    async def test_evidence_capped_at_5(self):
        store = InMemoryStore()

        for i in range(10):
            diff = [{"pattern": "prefers_snake_case", "summary": f"Observation {i}"}]
            await store_user_preferences(store, "user-1", "product", diff)

        prefs = await retrieve_user_preferences(store, "user-1", "product")
        assert len(prefs[0]["evidence"]) == 5
        # Should be the last 5
        assert prefs[0]["evidence"][0] == "Observation 5"

    @pytest.mark.asyncio
    async def test_empty_diffs_skipped(self):
        store = InMemoryStore()
        await store_user_preferences(store, "user-1", "product", [])
        prefs = await retrieve_user_preferences(store, "user-1", "product")
        assert prefs == []

    @pytest.mark.asyncio
    async def test_preferences_sorted_by_weight(self):
        store = InMemoryStore()
        # Create two patterns with different observation counts
        for _ in range(5):
            await store_user_preferences(
                store,
                "user-1",
                "product",
                [{"pattern": "prefers_snake_case", "summary": "snake"}],
            )
        await store_user_preferences(
            store,
            "user-1",
            "product",
            [{"pattern": "field_modified:name", "summary": "name change"}],
        )

        prefs = await retrieve_user_preferences(store, "user-1", "product")
        assert len(prefs) == 2
        assert prefs[0]["pattern"] == "prefers_snake_case"  # higher weight
        assert prefs[0]["weight"] > prefs[1]["weight"]

    @pytest.mark.asyncio
    async def test_cross_entity_isolation(self):
        store = InMemoryStore()
        diff = [{"pattern": "prefers_snake_case", "summary": "snake"}]
        await store_user_preferences(store, "user-1", "product", diff)
        await store_user_preferences(store, "user-1", "meter", diff)

        product_prefs = await retrieve_user_preferences(store, "user-1", "product")
        meter_prefs = await retrieve_user_preferences(store, "user-1", "meter")
        assert len(product_prefs) == 1
        assert len(meter_prefs) == 1


# ---------------------------------------------------------------------------
# store_rejection_signal
# ---------------------------------------------------------------------------


class TestStoreRejectionSignal:
    @pytest.mark.asyncio
    async def test_rejection_recorded(self):
        store = InMemoryStore()
        entity = {"code": "test_code", "name": "Test", "currency": "USD"}
        await store_rejection_signal(store, "user-1", "product", entity)

        ns = ("user", "user-1", "preferences", "product")
        item = await store.aget(ns, "rejection_product")
        assert item is not None
        assert item.value["count"] == 1
        assert item.value["weight"] == 0.5
        assert item.value["pattern"] == "rejection_product"

    @pytest.mark.asyncio
    async def test_rejection_count_increments(self):
        store = InMemoryStore()
        entity = {"code": "test_code", "name": "Test"}
        await store_rejection_signal(store, "user-1", "product", entity)
        await store_rejection_signal(store, "user-1", "product", entity)

        ns = ("user", "user-1", "preferences", "product")
        item = await store.aget(ns, "rejection_product")
        assert item.value["count"] == 2
        assert item.value["weight"] == 0.6

    @pytest.mark.asyncio
    async def test_rejection_patterns_capped(self):
        store = InMemoryStore()
        for i in range(15):
            entity = {"code": f"code_{i}", "name": f"Entity {i}"}
            await store_rejection_signal(store, "user-1", "product", entity)

        ns = ("user", "user-1", "preferences", "product")
        item = await store.aget(ns, "rejection_product")
        assert len(item.value["patterns"]) == 10  # capped


# ---------------------------------------------------------------------------
# format_preferences_for_prompt
# ---------------------------------------------------------------------------


class TestFormatPreferencesForPrompt:
    def test_empty_preferences(self):
        assert format_preferences_for_prompt([]) == ""

    def test_snake_case_preference(self):
        prefs = [{"pattern": "prefers_snake_case", "count": 5, "weight": 0.9}]
        result = format_preferences_for_prompt(prefs)
        assert "snake_case" in result
        assert "5 times" in result

    def test_currency_preference(self):
        prefs = [{"pattern": "prefers_currency_EUR", "count": 3, "weight": 0.7}]
        result = format_preferences_for_prompt(prefs)
        assert "EUR" in result

    def test_billing_preference(self):
        prefs = [{"pattern": "prefers_billing_monthly", "count": 2, "weight": 0.6}]
        result = format_preferences_for_prompt(prefs)
        assert "monthly" in result

    def test_custom_fields_added(self):
        prefs = [{"pattern": "custom_fields_added:tier,region", "count": 2, "weight": 0.6}]
        result = format_preferences_for_prompt(prefs)
        assert "tier,region" in result

    def test_field_modified(self):
        prefs = [{"pattern": "field_modified:name", "count": 3, "weight": 0.7}]
        result = format_preferences_for_prompt(prefs)
        assert "name" in result

    def test_capped_at_10(self):
        prefs = [
            {"pattern": f"field_modified:field_{i}", "count": 1, "weight": 0.5} for i in range(15)
        ]
        result = format_preferences_for_prompt(prefs)
        # Count lines starting with "- "
        lines = [line for line in result.split("\n") if line.startswith("- ")]
        assert len(lines) == 10

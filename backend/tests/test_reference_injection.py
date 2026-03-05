"""Tests for inject_parent_references in app.agents.utils."""

import uuid

import pytest

from app.agents.utils import inject_parent_references


def _make_parent(code: str) -> dict:
    """Create a parent entity dict with a random UUID and the given code."""
    return {"id": str(uuid.uuid4()), "code": code, "name": f"Parent {code}"}


def _make_entity(code: str, **extra: object) -> dict:
    """Create a child entity dict with a random UUID and the given code."""
    return {"id": str(uuid.uuid4()), "code": code, "name": f"Entity {code}", **extra}


# ---------------------------------------------------------------------------
# 1. TestValidateExistingUUID
# ---------------------------------------------------------------------------


class TestValidateExistingUUID:
    """Strategy 1: if the ref field already holds a valid parent UUID, keep it."""

    def test_keeps_valid_parent_uuid(self) -> None:
        parent = _make_parent("storage_meter")
        entity = _make_entity("storage_agg", meterId=parent["id"])

        result = inject_parent_references(
            entities=[entity],
            ref_field="meterId",
            parents=[parent],
        )

        assert result[0]["meterId"] == parent["id"]

    def test_clears_invalid_uuid(self) -> None:
        parent = _make_parent("storage_meter")
        entity = _make_entity("storage_agg", meterId="bogus-not-a-real-uuid")

        result = inject_parent_references(
            entities=[entity],
            ref_field="meterId",
            parents=[parent],
        )

        # Single parent -> auto-assign replaces the bogus value
        assert result[0]["meterId"] == parent["id"]


# ---------------------------------------------------------------------------
# 2. TestResolveByCodeHint
# ---------------------------------------------------------------------------


class TestResolveByCodeHint:
    """Strategy 2: resolve via a code hint field that matches a parent's code."""

    def test_resolves_meter_code_to_meter_id(self) -> None:
        parent = _make_parent("api_calls_meter")
        entity = _make_entity("api_calls_agg", meterCode="api_calls_meter")

        result = inject_parent_references(
            entities=[entity],
            ref_field="meterId",
            parents=[parent],
            code_hint_field="meterCode",
        )

        assert result[0]["meterId"] == parent["id"]
        assert "meterCode" not in result[0]

    def test_resolves_among_multiple_parents(self) -> None:
        parent_a = _make_parent("meter_alpha")
        parent_b = _make_parent("meter_beta")
        entity = _make_entity("beta_agg", meterCode="meter_beta")

        result = inject_parent_references(
            entities=[entity],
            ref_field="meterId",
            parents=[parent_a, parent_b],
            code_hint_field="meterCode",
        )

        assert result[0]["meterId"] == parent_b["id"]
        assert "meterCode" not in result[0]

    def test_unmatched_code_hint_does_not_crash(self) -> None:
        parent = _make_parent("real_meter")
        entity = _make_entity("some_agg", meterCode="nonexistent_meter")

        result = inject_parent_references(
            entities=[entity],
            ref_field="meterId",
            parents=[parent],
            code_hint_field="meterCode",
        )

        # Hint didn't match, but single parent -> auto-assign
        assert result[0]["meterId"] == parent["id"]
        assert "meterCode" not in result[0]


# ---------------------------------------------------------------------------
# 3. TestAutoAssignSingleParent
# ---------------------------------------------------------------------------


class TestAutoAssignSingleParent:
    """Strategy 3: auto-assign when there is exactly one parent."""

    def test_assigns_when_one_parent_and_no_ref(self) -> None:
        parent = _make_parent("the_product")
        entity = _make_entity("the_meter")  # no productId at all

        result = inject_parent_references(
            entities=[entity],
            ref_field="productId",
            parents=[parent],
        )

        assert result[0]["productId"] == parent["id"]

    def test_no_assign_when_multiple_parents_and_no_hint(self) -> None:
        parent_a = _make_parent("product_a")
        parent_b = _make_parent("product_b")
        entity = _make_entity("orphan_meter")  # no productId, no hint

        result = inject_parent_references(
            entities=[entity],
            ref_field="productId",
            parents=[parent_a, parent_b],
        )

        # Multiple parents and no hint -> cannot resolve, leave unset
        assert "productId" not in result[0]


# ---------------------------------------------------------------------------
# 4. TestEdgeCases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Edge cases: empty inputs, multiple entities."""

    def test_empty_entities_returns_empty(self) -> None:
        parent = _make_parent("some_parent")
        result = inject_parent_references(
            entities=[],
            ref_field="meterId",
            parents=[parent],
        )
        assert result == []

    def test_empty_parents_leaves_entities_unchanged(self) -> None:
        entity = _make_entity("lonely_agg", meterId="whatever")
        original_meter_id = entity["meterId"]

        result = inject_parent_references(
            entities=[entity],
            ref_field="meterId",
            parents=[],
        )

        assert result[0]["meterId"] == original_meter_id

    def test_multiple_entities_each_get_ref(self) -> None:
        product = _make_parent("cloud_product")
        meter_a = _make_entity("meter_a")
        meter_b = _make_entity("meter_b")

        result = inject_parent_references(
            entities=[meter_a, meter_b],
            ref_field="productId",
            parents=[product],
        )

        assert result[0]["productId"] == product["id"]
        assert result[1]["productId"] == product["id"]

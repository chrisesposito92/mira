# Post-LLM Reference Injection — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** After LLM generates entities, programmatically inject MIRA UUIDs for parent references so the push engine's reference resolver can map them to m3ter UUIDs at push time.

**Architecture:** A single utility function `inject_parent_references()` in `agents/utils.py` takes generated entities and parent entity lists, then injects MIRA UUIDs into reference fields using three strategies: validate existing UUID, resolve by code hint, or auto-assign single parent. Each generation node calls it after `parse_entity_list()`.

**Tech Stack:** Python, pytest, existing `agents/utils.py` module

---

### Task 1: Write tests for `inject_parent_references`

**Files:**
- Create: `backend/tests/test_reference_injection.py`

**Step 1: Write the test file**

```python
"""Tests for post-LLM parent reference injection."""

from uuid import uuid4

from app.agents.utils import inject_parent_references


# ── Helpers ──────────────────────────────────────────────────

def _product(code="my_product"):
    return {"id": str(uuid4()), "name": "My Product", "code": code}


def _meter(product_id=None, product_code=None):
    m = {"name": "My Meter", "code": "my_meter", "dataFields": [], "derivedFields": []}
    if product_id:
        m["productId"] = product_id
    if product_code:
        m["productCode"] = product_code
    return m


def _agg(meter_id=None, meter_code=None):
    a = {"name": "My Agg", "code": "my_agg", "aggregationType": "SUM", "targetField": "x"}
    if meter_id:
        a["meterId"] = meter_id
    if meter_code:
        a["meterCode"] = meter_code
    return a


# ── Strategy 1: validate existing UUID ──────────────────────

class TestValidateExistingUUID:
    def test_keeps_valid_parent_uuid(self):
        product = _product()
        meter = _meter(product_id=product["id"])
        result = inject_parent_references(
            entities=[meter],
            ref_field="productId",
            parents=[product],
            code_hint_field=None,
        )
        assert result[0]["productId"] == product["id"]

    def test_clears_invalid_uuid(self):
        """If ref field has a UUID that doesn't match any parent, clear it."""
        product = _product()
        meter = _meter(product_id=str(uuid4()))  # bogus UUID
        result = inject_parent_references(
            entities=[meter],
            ref_field="productId",
            parents=[product],
            code_hint_field=None,
        )
        # Should auto-assign since there's 1 parent
        assert result[0]["productId"] == product["id"]


# ── Strategy 2: resolve by code hint ────────────────────────

class TestResolveByCodeHint:
    def test_resolves_meter_code_to_meter_id(self):
        meter = {"id": str(uuid4()), "name": "M", "code": "api_meter"}
        agg = _agg(meter_code="api_meter")
        result = inject_parent_references(
            entities=[agg],
            ref_field="meterId",
            parents=[meter],
            code_hint_field="meterCode",
        )
        assert result[0]["meterId"] == meter["id"]
        assert "meterCode" not in result[0]  # hint field cleaned up

    def test_resolves_among_multiple_parents(self):
        meter_a = {"id": str(uuid4()), "name": "A", "code": "meter_a"}
        meter_b = {"id": str(uuid4()), "name": "B", "code": "meter_b"}
        agg = _agg(meter_code="meter_b")
        result = inject_parent_references(
            entities=[agg],
            ref_field="meterId",
            parents=[meter_a, meter_b],
            code_hint_field="meterCode",
        )
        assert result[0]["meterId"] == meter_b["id"]

    def test_unmatched_code_hint_does_not_crash(self):
        meter = {"id": str(uuid4()), "name": "M", "code": "real_meter"}
        agg = _agg(meter_code="nonexistent_meter")
        result = inject_parent_references(
            entities=[agg],
            ref_field="meterId",
            parents=[meter],
            code_hint_field="meterCode",
        )
        # Single parent fallback
        assert result[0]["meterId"] == meter["id"]


# ── Strategy 3: auto-assign single parent ───────────────────

class TestAutoAssignSingleParent:
    def test_assigns_when_one_parent_and_no_ref(self):
        product = _product()
        meter = _meter()  # no productId
        result = inject_parent_references(
            entities=[meter],
            ref_field="productId",
            parents=[product],
            code_hint_field=None,
        )
        assert result[0]["productId"] == product["id"]

    def test_no_assign_when_multiple_parents_and_no_hint(self):
        p1 = _product("prod_a")
        p2 = _product("prod_b")
        meter = _meter()  # no productId, no hint
        result = inject_parent_references(
            entities=[meter],
            ref_field="productId",
            parents=[p1, p2],
            code_hint_field=None,
        )
        # Can't determine which parent — leave unset
        assert "productId" not in result[0]


# ── Edge cases ──────────────────────────────────────────────

class TestEdgeCases:
    def test_empty_entities_returns_empty(self):
        result = inject_parent_references(
            entities=[],
            ref_field="productId",
            parents=[_product()],
            code_hint_field=None,
        )
        assert result == []

    def test_empty_parents_leaves_entities_unchanged(self):
        meter = _meter()
        result = inject_parent_references(
            entities=[meter],
            ref_field="productId",
            parents=[],
            code_hint_field=None,
        )
        assert "productId" not in result[0]

    def test_multiple_entities_each_get_ref(self):
        product = _product()
        m1 = _meter()
        m2 = _meter()
        result = inject_parent_references(
            entities=[m1, m2],
            ref_field="productId",
            parents=[product],
            code_hint_field=None,
        )
        assert result[0]["productId"] == product["id"]
        assert result[1]["productId"] == product["id"]
```

**Step 2: Run tests to verify they fail**

Run: `cd /Users/chrisesposito/Documents/github/mira/backend && python -m pytest tests/test_reference_injection.py -v`
Expected: FAIL — `ImportError: cannot import name 'inject_parent_references'`

**Step 3: Commit**

```bash
git add backend/tests/test_reference_injection.py
git commit -m "test: add tests for inject_parent_references utility"
```

---

### Task 2: Implement `inject_parent_references` in `agents/utils.py`

**Files:**
- Modify: `backend/app/agents/utils.py` (add function at end)

**Step 1: Add the function**

Append to `backend/app/agents/utils.py`:

```python
def inject_parent_references(
    entities: list[dict],
    ref_field: str,
    parents: list[dict],
    code_hint_field: str | None = None,
) -> list[dict]:
    """Inject parent MIRA UUIDs into generated entities' reference fields.

    Three-strategy resolution:
    1. Validate — if ref_field already contains a valid parent UUID, keep it.
    2. Code hint — if code_hint_field is set and matches a parent's code, resolve it.
    3. Auto-assign — if there's exactly 1 parent and no ref, assign it.

    Cleans up code_hint_field from entity data after resolution.
    """
    if not entities or not parents:
        return entities

    parent_ids = {p["id"] for p in parents if "id" in p}
    parent_by_code = {p["code"]: p["id"] for p in parents if "code" in p and "id" in p}

    for entity in entities:
        current_ref = entity.get(ref_field)

        # Strategy 1: already a valid parent UUID — keep it
        if current_ref and current_ref in parent_ids:
            _cleanup_hint(entity, code_hint_field)
            continue

        # Strategy 2: resolve by code hint
        if code_hint_field:
            hint_value = entity.get(code_hint_field)
            if hint_value and hint_value in parent_by_code:
                entity[ref_field] = parent_by_code[hint_value]
                _cleanup_hint(entity, code_hint_field)
                continue

        # Strategy 3: auto-assign if single parent
        if len(parents) == 1:
            entity[ref_field] = parents[0]["id"]
            _cleanup_hint(entity, code_hint_field)
            continue

        # Multiple parents, no hint, no valid ref — log warning and skip
        logger.warning(
            "Cannot resolve %s for entity %s: %d parents, no code hint",
            ref_field,
            entity.get("code", entity.get("name", "?")),
            len(parents),
        )
        _cleanup_hint(entity, code_hint_field)

    return entities


def _cleanup_hint(entity: dict, code_hint_field: str | None) -> None:
    """Remove a code hint field from entity data (it's not an API field)."""
    if code_hint_field and code_hint_field in entity:
        del entity[code_hint_field]
```

**Step 2: Run tests to verify they pass**

Run: `cd /Users/chrisesposito/Documents/github/mira/backend && python -m pytest tests/test_reference_injection.py -v`
Expected: All 9 tests PASS

**Step 3: Commit**

```bash
git add backend/app/agents/utils.py
git commit -m "feat: add inject_parent_references utility for post-LLM reference injection"
```

---

### Task 3: Wire up WF1 generation nodes

**Files:**
- Modify: `backend/app/agents/nodes/generation.py`

**Step 1: Add injection calls to `generate_meters`**

After line `meters = parse_entity_list(content)` (~line 129), add:

```python
    # Inject productId from approved products
    products = state.get("products", [])
    if meters and products:
        from app.agents.utils import inject_parent_references
        inject_parent_references(meters, "productId", products, code_hint_field="productCode")
```

**Step 2: Add injection calls to `generate_aggregations`**

After line `aggregations = parse_entity_list(content)` (~line 185), add:

```python
    # Inject meterId from approved meters
    if aggregations and meters:
        from app.agents.utils import inject_parent_references
        inject_parent_references(aggregations, "meterId", meters, code_hint_field="meterCode")
```

**Step 3: Add injection calls to `generate_compound_aggregations`**

After line `compound_aggregations = parse_entity_list(content)` (~line 244), add:

```python
    # Inject productId from approved products
    if compound_aggregations:
        from app.agents.utils import inject_parent_references
        inject_parent_references(compound_aggregations, "productId", products, code_hint_field="productCode")
```

**Step 4: Run existing backend tests to verify no regressions**

Run: `cd /Users/chrisesposito/Documents/github/mira/backend && python -m pytest tests/test_nodes.py tests/test_graph.py -v -m "not integration"`
Expected: All existing tests PASS

**Step 5: Commit**

```bash
git add backend/app/agents/nodes/generation.py
git commit -m "feat: inject parent references in WF1 generation nodes (meters, aggregations, compound aggs)"
```

---

### Task 4: Wire up WF2 generation nodes

**Files:**
- Modify: `backend/app/agents/nodes/plan_template_gen.py`
- Modify: `backend/app/agents/nodes/plan_gen.py`
- Modify: `backend/app/agents/nodes/pricing_gen.py`

**Step 1: Add injection to `generate_plan_templates`**

In `plan_template_gen.py`, after `plan_templates = parse_entity_list(content)` (~line 47), add:

```python
    # Inject productId from approved products
    if plan_templates and approved_products:
        from app.agents.utils import inject_parent_references
        inject_parent_references(plan_templates, "productId", approved_products, code_hint_field="productCode")
```

**Step 2: Add injection to `generate_plans`**

In `plan_gen.py`, after `plans = parse_entity_list(content)` (~line 49), add:

```python
    # Inject planTemplateId from approved plan templates
    if plans and plan_templates:
        from app.agents.utils import inject_parent_references
        inject_parent_references(plans, "planTemplateId", plan_templates, code_hint_field="planTemplateCode")
```

**Step 3: Add injection to `generate_pricing`**

In `pricing_gen.py`, after `pricing = parse_entity_list(content)` (~line 53), add:

```python
    # Inject aggregationId from approved aggregations (regular + compound)
    all_aggregations = list(approved_aggregations) + list(approved_compound_aggregations)
    if pricing and all_aggregations:
        from app.agents.utils import inject_parent_references
        inject_parent_references(pricing, "aggregationId", all_aggregations, code_hint_field="aggregationCode")
        # Also handle compoundAggregationId if present
        inject_parent_references(pricing, "compoundAggregationId", approved_compound_aggregations, code_hint_field="compoundAggregationCode")

    # Inject planTemplateId from plan templates
    if pricing and plan_templates:
        from app.agents.utils import inject_parent_references
        inject_parent_references(pricing, "planTemplateId", plan_templates, code_hint_field="planTemplateCode")

    # Inject planId from plans (some pricing uses planId instead)
    if pricing and plans:
        from app.agents.utils import inject_parent_references
        inject_parent_references(pricing, "planId", plans, code_hint_field="planCode")
```

**Step 4: Run WF2 tests**

Run: `cd /Users/chrisesposito/Documents/github/mira/backend && python -m pytest tests/test_plan_pricing_graph.py -v -m "not integration"`
Expected: All existing tests PASS

**Step 5: Commit**

```bash
git add backend/app/agents/nodes/plan_template_gen.py backend/app/agents/nodes/plan_gen.py backend/app/agents/nodes/pricing_gen.py
git commit -m "feat: inject parent references in WF2 generation nodes (plan templates, plans, pricing)"
```

---

### Task 5: Wire up WF3 generation nodes

**Files:**
- Modify: `backend/app/agents/nodes/account_plan_gen.py`

Note: `generate_accounts` needs no injection — accounts are top-level entities with no parent references.

**Step 1: Add injection to `generate_account_plans`**

In `account_plan_gen.py`, after `account_plans = parse_entity_list(content)` (~line 44), add:

```python
    # Inject accountId and planId from approved parents
    if account_plans and accounts:
        from app.agents.utils import inject_parent_references
        inject_parent_references(account_plans, "accountId", accounts, code_hint_field="accountCode")
    if account_plans and approved_plans:
        inject_parent_references(account_plans, "planId", approved_plans, code_hint_field="planCode")
```

**Step 2: Run WF3 tests**

Run: `cd /Users/chrisesposito/Documents/github/mira/backend && python -m pytest tests/test_account_setup_graph.py -v -m "not integration"`
Expected: All existing tests PASS

**Step 3: Commit**

```bash
git add backend/app/agents/nodes/account_plan_gen.py
git commit -m "feat: inject parent references in WF3 generation node (account plans)"
```

---

### Task 6: Run full test suite and commit remaining changes

**Files:**
- Already modified: `backend/app/m3ter/client.py`, `backend/app/m3ter/entities.py`, `backend/app/m3ter/mapper.py`, `backend/app/agents/tools/m3ter_schema.py`, `backend/app/agents/prompts/product_meter.py`

These files were modified earlier in the conversation (error logging, derivedFields fix, pricing push support, prompt improvements). They need to be tested and committed.

**Step 1: Run full backend test suite**

Run: `cd /Users/chrisesposito/Documents/github/mira/backend && python -m pytest tests/ -v -m "not integration and not eval_live"`
Expected: All tests PASS

**Step 2: Commit supporting changes**

```bash
git add backend/app/m3ter/client.py backend/app/m3ter/entities.py backend/app/m3ter/mapper.py
git commit -m "fix: improve m3ter push — log error bodies, default derivedFields, support planTemplate pricing"

git add backend/app/agents/tools/m3ter_schema.py backend/app/agents/prompts/product_meter.py
git commit -m "fix: update meter/aggregation schemas and prompts with required fields and UUID references"
```

**Step 3: Update AGENTS.md with reference injection pattern**

Add a bullet under "Key Patterns" about the reference injection:

> **Reference injection**: After LLM generates entities, `inject_parent_references()` in `agents/utils.py` programmatically injects parent MIRA UUIDs into reference fields (productId, meterId, planTemplateId, etc.) using 3 strategies: validate existing UUID, resolve by code hint, auto-assign single parent. At push time, `ReferenceResolver` maps MIRA UUIDs → m3ter UUIDs.

---

### Summary of all changes

| File | Change |
|------|--------|
| `agents/utils.py` | New `inject_parent_references()` + `_cleanup_hint()` |
| `agents/nodes/generation.py` | Inject refs in meters, aggregations, compound aggs |
| `agents/nodes/plan_template_gen.py` | Inject productId |
| `agents/nodes/plan_gen.py` | Inject planTemplateId |
| `agents/nodes/pricing_gen.py` | Inject aggregationId, planTemplateId, planId |
| `agents/nodes/account_plan_gen.py` | Inject accountId, planId |
| `agents/prompts/product_meter.py` | Updated meter + aggregation prompts (already done) |
| `agents/tools/m3ter_schema.py` | Added name to DataField, derivedFields required (already done) |
| `m3ter/client.py` | Error body logging, `create_pricing_on_template` (already done) |
| `m3ter/entities.py` | Support planTemplateId in pricing push (already done) |
| `m3ter/mapper.py` | Default derivedFields to [] for meters (already done) |
| `tests/test_reference_injection.py` | 9 unit tests for inject_parent_references |

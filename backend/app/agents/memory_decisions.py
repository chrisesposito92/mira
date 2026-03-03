"""User decision memory — tracks patterns from edit/reject decisions.

Observes how users modify or reject generated entities, extracts preference
patterns (code format, currency, billing frequency, custom fields, etc.),
and stores them per-user per-entity-type so future generations can be
personalized.

Namespace schema:
  ("user", {user_id}, "preferences", {entity_type})

All store operations are wrapped in try/except — memory is additive, never
required.  Functions return gracefully on failure so workflows continue.
"""

import logging
import re

from langgraph.store.base import BaseStore

logger = logging.getLogger(__name__)

# Fields tracked beyond the universal set, keyed by entity type
_ENTITY_SPECIFIC_FIELDS: dict[str, list[str]] = {
    "plan_template": ["currency", "billFrequency", "standingCharge", "minimumSpend"],
    "pricing": ["pricingBands", "cumulative", "type"],
    "account": ["email", "currency", "daysBeforeBillDue"],
    "meter": ["dataFields", "derivedFields"],
    "aggregation": ["aggregationType", "targetField", "meterCode"],
}

_UNIVERSAL_FIELDS = {"name", "code", "customFields"}


# ---------------------------------------------------------------------------
# Diff computation
# ---------------------------------------------------------------------------


def _classify_code_format(code: str) -> str | None:
    """Classify code format preference from a code string."""
    if "_" in code:
        return "prefers_snake_case"
    if "-" in code:
        return "prefers_kebab_case"
    if re.search(r"[a-z][A-Z]", code):
        return "prefers_camelCase"
    return None


def _classify_pattern(field: str, old_val: object, new_val: object) -> str:
    """Classify a field change into a named pattern."""
    if field == "code" and isinstance(new_val, str):
        fmt = _classify_code_format(new_val)
        if fmt:
            return fmt

    if field == "currency" and isinstance(new_val, str):
        return f"prefers_currency_{new_val.upper()}"

    if field == "billFrequency" and isinstance(new_val, str):
        return f"prefers_billing_{new_val.lower()}"

    if field == "customFields":
        old_keys = set((old_val or {}).keys()) if isinstance(old_val, dict) else set()
        new_keys = set((new_val or {}).keys()) if isinstance(new_val, dict) else set()
        added = new_keys - old_keys
        removed = old_keys - new_keys
        if added and removed:
            return (
                f"custom_fields_added:{','.join(sorted(added))}|removed:{','.join(sorted(removed))}"
            )
        if added:
            return f"custom_fields_added:{','.join(sorted(added))}"
        if removed:
            return f"custom_fields_removed:{','.join(sorted(removed))}"

    return f"field_modified:{field}"


def compute_entity_diff(original: dict, edited: dict, entity_type: str) -> list[dict]:
    """Compare two entity dicts and return classified diff entries.

    Returns a list of diffs, each with field, old, new, pattern, and summary.
    """
    tracked = set(_UNIVERSAL_FIELDS)
    tracked.update(_ENTITY_SPECIFIC_FIELDS.get(entity_type, []))

    diffs: list[dict] = []
    for field in tracked:
        old_val = original.get(field)
        new_val = edited.get(field)
        if old_val == new_val:
            continue
        pattern = _classify_pattern(field, old_val, new_val)
        diffs.append(
            {
                "field": field,
                "old": old_val,
                "new": new_val,
                "pattern": pattern,
                "summary": f"Changed {field}: {old_val} → {new_val}",
            }
        )
    return diffs


# ---------------------------------------------------------------------------
# Store writes
# ---------------------------------------------------------------------------


def _preference_namespace(user_id: str, entity_type: str) -> tuple[str, ...]:
    return ("user", user_id, "preferences", entity_type)


async def store_user_preferences(
    store: BaseStore,
    user_id: str,
    entity_type: str,
    diffs: list[dict],
) -> None:
    """Persist preference signals extracted from user edits.

    For each diff, upserts a preference item keyed by its pattern name.
    Weight starts at 0.5 and increases by 0.1 per observation (capped at 1.0).
    Evidence is capped at the last 5 samples.
    """
    if not diffs:
        return
    ns = _preference_namespace(user_id, entity_type)
    for diff in diffs:
        try:
            pattern = diff["pattern"]
            existing = await store.aget(ns, pattern)
            if existing:
                val = existing.value
                weight = min(val.get("weight", 0.5) + 0.1, 1.0)
                count = val.get("count", 0) + 1
                evidence = val.get("evidence", [])
            else:
                weight = 0.5
                count = 1
                evidence = []
            evidence = (evidence + [diff["summary"]])[-5:]
            await store.aput(
                ns,
                pattern,
                {
                    "pattern": pattern,
                    "weight": round(weight, 2),
                    "count": count,
                    "evidence": evidence,
                },
            )
        except Exception:
            logger.warning(
                "Failed to store preference %s for user %s",
                diff.get("pattern", "?"),
                user_id,
                exc_info=True,
            )


async def store_rejection_signal(
    store: BaseStore,
    user_id: str,
    entity_type: str,
    entity: dict,
) -> None:
    """Record that a user rejected an entity, tracking rejection count and patterns."""
    ns = _preference_namespace(user_id, entity_type)
    key = f"rejection_{entity_type}"
    try:
        existing = await store.aget(ns, key)
        if existing:
            val = existing.value
            count = val.get("count", 0) + 1
            weight = min(val.get("weight", 0.5) + 0.1, 1.0)
            patterns = val.get("patterns", [])
        else:
            count = 1
            weight = 0.5
            patterns = []

        # Extract observable patterns from the rejected entity
        code = entity.get("code")
        if isinstance(code, str):
            fmt = _classify_code_format(code)
            if fmt:
                patterns.append(f"rejected_code_format:{fmt}")

        field_snapshot = sorted(k for k in entity if entity[k] is not None)
        patterns.append(f"rejected_fields:{','.join(field_snapshot[:10])}")
        patterns = patterns[-10:]

        await store.aput(
            ns,
            key,
            {
                "pattern": f"rejection_{entity_type}",
                "weight": round(weight, 2),
                "count": count,
                "entity_type": entity_type,
                "patterns": patterns,
            },
        )
    except Exception:
        logger.warning("Failed to store rejection for %s/%s", user_id, entity_type, exc_info=True)


# ---------------------------------------------------------------------------
# Store reads
# ---------------------------------------------------------------------------


async def retrieve_user_preferences(
    store: BaseStore,
    user_id: str,
    entity_type: str,
) -> list[dict]:
    """Load user preferences for an entity type, filtered by minimum weight.

    Returns preferences sorted by weight descending.  Empty list on failure.
    """
    ns = _preference_namespace(user_id, entity_type)
    try:
        items = await store.asearch(ns, limit=50)
        prefs = []
        for item in items:
            val = item.value
            if val.get("weight", 0) >= 0.5:
                prefs.append(val)
        prefs.sort(key=lambda p: p.get("weight", 0), reverse=True)
        return prefs
    except Exception:
        logger.warning(
            "Failed to retrieve preferences for %s/%s", user_id, entity_type, exc_info=True
        )
        return []


# ---------------------------------------------------------------------------
# Prompt formatting
# ---------------------------------------------------------------------------

_PATTERN_LABELS: dict[str, str] = {
    "prefers_snake_case": "snake_case for entity codes",
    "prefers_kebab_case": "kebab-case for entity codes",
    "prefers_camelCase": "camelCase for entity codes",
}


def _describe_pattern(pattern: str, count: int) -> str:
    """Turn a pattern key into a human-readable preference description."""
    label = _PATTERN_LABELS.get(pattern)
    if label:
        return f"You prefer {label} (observed {count} times)"

    if pattern.startswith("prefers_currency_"):
        currency = pattern.removeprefix("prefers_currency_")
        return f"You prefer {currency} as the currency (observed {count} times)"

    if pattern.startswith("prefers_billing_"):
        freq = pattern.removeprefix("prefers_billing_")
        return f"You prefer {freq} billing frequency (observed {count} times)"

    if pattern.startswith("custom_fields_added:"):
        rest = pattern.removeprefix("custom_fields_added:")
        if "|removed:" in rest:
            added_keys, removed_keys = rest.split("|removed:", 1)
            return (
                f"You tend to add custom fields: {added_keys} "
                f"and remove: {removed_keys} (observed {count} times)"
            )
        return f"You tend to add custom fields: {rest} (observed {count} times)"

    if pattern.startswith("custom_fields_removed:"):
        keys = pattern.removeprefix("custom_fields_removed:")
        return f"You tend to remove custom fields: {keys} (observed {count} times)"

    if pattern.startswith("field_modified:"):
        field = pattern.removeprefix("field_modified:")
        return f"You frequently adjust the '{field}' field (observed {count} times)"

    if pattern.startswith("rejection_"):
        return f"Rejection pattern recorded (observed {count} times)"

    return f"Preference: {pattern} (observed {count} times)"


def format_preferences_for_prompt(preferences: list[dict]) -> str:
    """Format a preferences list into a prompt-injectable string.

    Returns empty string if there are no preferences.  Caps output at 10 items.
    """
    if not preferences:
        return ""
    lines: list[str] = []
    for pref in preferences[:10]:
        pattern = pref.get("pattern", "")
        count = pref.get("count", 1)
        lines.append(f"- {_describe_pattern(pattern, count)}")
    return "Based on your previous preferences:\n" + "\n".join(lines)

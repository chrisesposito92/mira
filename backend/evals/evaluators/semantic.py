"""LLM-as-Judge evaluator — semantic quality assessment (weight: 20%)."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from langchain.chat_models import init_chat_model

from evals.datasets.base import EvalResult

if TYPE_CHECKING:
    from evals.datasets.base import WorkflowReference

# Workflow type → entity state keys
WORKFLOW_ENTITY_KEYS: dict[str, list[str]] = {
    "product_meter_aggregation": ["products", "meters", "aggregations", "compound_aggregations"],
    "plan_pricing": ["plan_templates", "plans", "pricing"],
    "account_setup": ["accounts", "account_plans"],
}

JUDGE_PROMPT = """You are an expert m3ter billing configuration reviewer. Evaluate the following
generated billing configuration against the use case description and reference specification.

## Use Case
{use_case_description}

## Workflow Type
{workflow_type}

## Generated Configuration
{generated_config}

## Reference Specification
{reference_spec}

Score each dimension from 1-5 (1=poor, 5=excellent):

1. **relevance**: How well does the configuration address the use case requirements?
2. **naming**: Are entity names clear, descriptive, and follow conventions?
3. **data_model**: Is the data model (meters, data fields, aggregations) well-structured?
4. **aggregation_logic**: Are aggregation types and target fields logically correct?
5. **pricing_structure**: Are pricing bands, tiers, and amounts reasonable?
6. **completeness**: Does the configuration cover all aspects of the use case?

Respond with ONLY a JSON object (no markdown, no explanation):
{{"relevance": <int>, "naming": <int>, "data_model": <int>,
"aggregation_logic": <int>, "pricing_structure": <int>, "completeness": <int>}}"""

DIMENSIONS = [
    "relevance",
    "naming",
    "data_model",
    "aggregation_logic",
    "pricing_structure",
    "completeness",
]


def _format_entities(state: dict, workflow_type: str) -> str:
    """Format generated entities for the judge prompt."""
    entity_keys = WORKFLOW_ENTITY_KEYS.get(workflow_type, [])
    sections: list[str] = []
    for key in entity_keys:
        entities = state.get(key, [])
        if entities:
            sections.append(f"### {key} ({len(entities)})")
            sections.append(json.dumps(entities, indent=2, default=str))
    return "\n\n".join(sections) if sections else "No entities generated."


def _format_reference(reference: WorkflowReference) -> str:
    """Format reference specification for the judge prompt."""
    lines: list[str] = []
    lines.append(f"Expected counts: {json.dumps(reference.expected_counts)}")
    for key, entities in reference.entities.items():
        if entities:
            lines.append(f"\n### {key} ({len(entities)} expected)")
            for ref_entity in entities:
                lines.append(f"- {ref_entity.name}")
                if ref_entity.key_fields:
                    for field, value in ref_entity.key_fields.items():
                        lines.append(f"  {field}: {value}")
    return "\n".join(lines)


def _parse_scores(response_text: str) -> dict[str, int]:
    """Parse LLM judge response into dimension scores."""
    # Try to extract JSON from the response
    text = response_text.strip()

    # Handle markdown code blocks
    if "```" in text:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            text = text[start:end]

    scores: dict[str, Any] = json.loads(text)

    # Validate and clamp scores
    result: dict[str, int] = {}
    for dim in DIMENSIONS:
        val = scores.get(dim, 3)
        result[dim] = max(1, min(5, int(val)))

    return result


async def evaluate(
    state: dict,
    reference: WorkflowReference,
    workflow_type: str,
    judge_model: str = "claude-opus-4-6",
) -> EvalResult:
    """Evaluate configuration quality using an LLM judge.

    Scores 6 dimensions (1-5), overall = average / 5.0.
    """
    # Build use case description from available state fields
    use_case = state.get("use_case", {})
    if isinstance(use_case, dict) and use_case:
        use_case_desc = (
            f"Title: {use_case.get('title', 'N/A')}\n"
            f"Description: {use_case.get('description', 'N/A')}\n"
            f"Billing model: {use_case.get('target_billing_model', 'N/A')}"
        )
    else:
        use_case_desc = state.get("analysis", "No description provided.")
    generated_config = _format_entities(state, workflow_type)
    reference_spec = _format_reference(reference)

    prompt = JUDGE_PROMPT.format(
        use_case_description=use_case_desc,
        workflow_type=workflow_type,
        generated_config=generated_config,
        reference_spec=reference_spec,
    )

    llm = init_chat_model(judge_model)
    response = await llm.ainvoke(prompt)
    response_text = response.content if hasattr(response, "content") else str(response)

    try:
        dimension_scores = _parse_scores(response_text)
    except (json.JSONDecodeError, ValueError):
        # If parsing fails, return a middle-of-the-road score with error details
        return EvalResult(
            name="semantic",
            score=0.5,
            details=[{"error": "Failed to parse judge response", "raw": response_text[:500]}],
            notes="LLM judge response could not be parsed; defaulting to 0.5",
        )

    avg_score = sum(dimension_scores.values()) / len(dimension_scores)
    normalized_score = avg_score / 5.0

    details: list[dict] = [
        {"dimension": dim, "score": dimension_scores[dim], "max": 5} for dim in DIMENSIONS
    ]

    notes = (
        f"LLM judge ({judge_model}): avg {avg_score:.1f}/5.0 "
        f"({normalized_score:.1%} normalized). "
        + ", ".join(f"{d}={dimension_scores[d]}" for d in DIMENSIONS)
    )

    return EvalResult(name="semantic", score=normalized_score, details=details, notes=notes)

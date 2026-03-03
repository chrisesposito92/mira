"""Core dataclasses for evaluation datasets."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ReferenceEntity:
    """A single reference entity for comparison against generated output.

    Attributes:
        entity_type: The state key this entity belongs to (e.g. "products", "meters").
        name: Expected entity name (used for fuzzy name matching).
        key_fields: Critical semantic fields that evaluators check for accuracy.
            Keys are field names, values are expected values.
    """

    entity_type: str
    name: str
    key_fields: dict = field(default_factory=dict)


@dataclass(frozen=True)
class WorkflowReference:
    """Reference data for a single workflow evaluation.

    Attributes:
        entities: Mapping of state key → list of ReferenceEntity.
            Keys match WorkflowState fields (e.g. "products", "meters", "aggregations").
        expected_counts: Mapping of state key → expected count (for completeness evaluator).
    """

    entities: dict[str, list[ReferenceEntity]] = field(default_factory=dict)
    expected_counts: dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class EvalExample:
    """A complete evaluation example derived from an m3ter worked example.

    Attributes:
        name: Short identifier (e.g. "cloud_storage").
        display_name: Human-readable name (e.g. "Cloud Storage and File Cleanup").
        use_case: Dict compatible with UseCaseCreate fields
            (title, description, target_billing_model, billing_frequency, currency).
        wf1_reference: Reference for WF1 (Product/Meter/Aggregation).
        wf2_reference: Reference for WF2 (PlanTemplate/Plan/Pricing).
        wf3_reference: Reference for WF3 (Account/AccountPlan).
    """

    name: str
    display_name: str
    use_case: dict
    wf1_reference: WorkflowReference
    wf2_reference: WorkflowReference
    wf3_reference: WorkflowReference


@dataclass
class EvalResult:
    """Result from a single evaluator.

    Attributes:
        name: Evaluator name (e.g. "accuracy", "completeness").
        score: Normalized score in [0.0, 1.0].
        details: Evaluator-specific detail records.
        notes: Human-readable summary of the evaluation.
    """

    name: str
    score: float
    details: list[dict] = field(default_factory=list)
    notes: str = ""

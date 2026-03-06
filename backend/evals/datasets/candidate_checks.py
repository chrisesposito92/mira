"""Example 3: Segmented Aggregation on Single Meter Usage (Candidate Checks).

Based on m3ter worked example 3.

WF1: 1 product, 1 meter (Location WHERE, Type WHAT, Checks MEASURE),
     1 segmented aggregation (SUM Checks segmented by Location x Type)
WF2: 1 plan template (monthly, USD), 1 plan, 6 pricing configs (one per segment)
WF3: 1 account, 1 account plan
"""

from evals.datasets.base import EvalExample, ReferenceEntity, WorkflowReference

# ---------------------------------------------------------------------------
# WF1 — Product, Meter, Segmented Aggregation
# ---------------------------------------------------------------------------

_wf1_reference = WorkflowReference(
    entities={
        "products": [
            ReferenceEntity(
                entity_type="products",
                name="Premium Candidate Checks",
                key_fields={
                    "code": "premium_candidate_checks",
                },
            ),
        ],
        "meters": [
            ReferenceEntity(
                entity_type="meters",
                name="Candidate Check Meter 1",
                key_fields={
                    "code": "candidate_check_meter_1",
                    "dataFields_count": 3,
                    "dataFields_categories": ["WHERE", "WHAT", "MEASURE"],
                },
            ),
        ],
        "aggregations": [
            ReferenceEntity(
                entity_type="aggregations",
                name="Candidate Checks Aggregation 1",
                key_fields={
                    "aggregation": "SUM",
                    "targetField": "checks",
                    "segmentedFields": ["location", "type"],
                },
            ),
        ],
    },
    expected_counts={
        "products": 1,
        "meters": 1,
        "aggregations": 1,
        "compound_aggregations": 0,
    },
)

# ---------------------------------------------------------------------------
# WF2 — PlanTemplate, Plan, 6 Segment Pricing
# ---------------------------------------------------------------------------

_wf2_reference = WorkflowReference(
    entities={
        "plan_templates": [
            ReferenceEntity(
                entity_type="plan_templates",
                name="Candidate Checks Plan Template 1",
                key_fields={
                    "currency": "USD",
                    "standingCharge": 0.0,
                    "billFrequency": "MONTHLY",
                    "billFrequencyInterval": 1,
                },
            ),
        ],
        "plans": [
            ReferenceEntity(
                entity_type="plans",
                name="Candidate Checks Plan 1",
                key_fields={},
            ),
        ],
        "pricing": [
            # China/Standard — $0.20 per check
            ReferenceEntity(
                entity_type="pricing",
                name="China Standard Pricing",
                key_fields={
                    "pricingBands_count": 1,
                    "band_0_lowerLimit": 0,
                    "band_0_unitPrice": 0.20,
                },
            ),
            # China/Extended — $0.40 per check
            ReferenceEntity(
                entity_type="pricing",
                name="China Extended Pricing",
                key_fields={
                    "pricingBands_count": 1,
                    "band_0_lowerLimit": 0,
                    "band_0_unitPrice": 0.40,
                },
            ),
            # USA/Extended — $0.50 per check
            ReferenceEntity(
                entity_type="pricing",
                name="USA Extended Pricing",
                key_fields={
                    "pricingBands_count": 1,
                    "band_0_lowerLimit": 0,
                    "band_0_unitPrice": 0.50,
                },
            ),
            # USA/Complete — $0.70 per check
            ReferenceEntity(
                entity_type="pricing",
                name="USA Complete Pricing",
                key_fields={
                    "pricingBands_count": 1,
                    "band_0_lowerLimit": 0,
                    "band_0_unitPrice": 0.70,
                },
            ),
            # UK/Standard — $0.50 per check
            ReferenceEntity(
                entity_type="pricing",
                name="UK Standard Pricing",
                key_fields={
                    "pricingBands_count": 1,
                    "band_0_lowerLimit": 0,
                    "band_0_unitPrice": 0.50,
                },
            ),
            # UK/Complete — $0.80 per check
            ReferenceEntity(
                entity_type="pricing",
                name="UK Complete Pricing",
                key_fields={
                    "pricingBands_count": 1,
                    "band_0_lowerLimit": 0,
                    "band_0_unitPrice": 0.80,
                },
            ),
        ],
    },
    expected_counts={
        "plan_templates": 1,
        "plans": 1,
        "pricing": 6,
    },
)

# ---------------------------------------------------------------------------
# WF3 — Account, AccountPlan
# ---------------------------------------------------------------------------

_wf3_reference = WorkflowReference(
    entities={
        "accounts": [
            ReferenceEntity(
                entity_type="accounts",
                name="Candidate Checks Customer 1",
                key_fields={
                    "code": "candidate_checks_customer_1",
                    "currency": "USD",
                },
            ),
        ],
        "account_plans": [
            ReferenceEntity(
                entity_type="account_plans",
                name="Candidate Checks Customer 1 Account Plan",
                key_fields={},
            ),
        ],
    },
    expected_counts={
        "accounts": 1,
        "account_plans": 1,
    },
)

# ---------------------------------------------------------------------------
# Full example
# ---------------------------------------------------------------------------

CANDIDATE_CHECKS = EvalExample(
    name="candidate_checks",
    display_name="Segmented Aggregation on Single Meter Usage",
    use_case={
        "title": "Premium Candidate Checks",
        "description": (
            "Premium Candidate Checks is a background checking service with location- and "
            "type-based segmented pricing. Customers are billed monthly in USD with no standing "
            "charge. A single meter captures three fields: Location (WHERE — the country), "
            "Type (WHAT — the check type such as Standard, Extended, or Complete), and "
            "Checks (MEASURE — the number of checks). A segmented aggregation SUMs the "
            "checks field, segmented by Location and Type, yielding 6 segment combinations. "
            "Each segment has its own per-unit pricing: China/Standard $0.20, China/Extended "
            "$0.40, USA/Extended $0.50, USA/Complete $0.70, UK/Standard $0.50, UK/Complete $0.80."
        ),
        "target_billing_model": "usage_based",
        "billing_frequency": "monthly",
        "currency": "USD",
    },
    wf1_reference=_wf1_reference,
    wf2_reference=_wf2_reference,
    wf3_reference=_wf3_reference,
)

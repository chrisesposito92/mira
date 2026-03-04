"""Example 1: Cloud Storage and File Cleanup (Revive Graph Standard).

Based on m3ter worked example 1.

WF1: 1 product, 1 meter (3 MEASURE data fields + 1 derived field), 3 aggregations (SUM/SUM/MAX)
WF2: 1 plan template (monthly, USD, $20 standing charge), 1 plan, 3 pricing configs
     (tiered storage, flat per-unit files, stairstep processing)
WF3: 1 account, 1 account plan
"""

from evals.datasets.base import EvalExample, ReferenceEntity, WorkflowReference

# ---------------------------------------------------------------------------
# WF1 — Product, Meter, Aggregations
# ---------------------------------------------------------------------------

_wf1_reference = WorkflowReference(
    entities={
        "products": [
            ReferenceEntity(
                entity_type="products",
                name="Revive Graph Standard",
                key_fields={
                    "code": "revive_graph_standard",
                },
            ),
        ],
        "meters": [
            ReferenceEntity(
                entity_type="meters",
                name="Store N Clean Meter",
                key_fields={
                    "code": "store_n_clean_meter",
                    "dataFields_count": 3,
                    "dataFields_categories": ["MEASURE", "MEASURE", "MEASURE"],
                    "derivedFields_count": 1,
                },
            ),
        ],
        "aggregations": [
            ReferenceEntity(
                entity_type="aggregations",
                name="Gigabyte Store Aggregation",
                key_fields={
                    "aggregationType": "SUM",
                    "targetField": "gigabyte_store",
                },
            ),
            ReferenceEntity(
                entity_type="aggregations",
                name="Graphic File Submits Aggregation",
                key_fields={
                    "aggregationType": "SUM",
                    "targetField": "graphic_file_submits",
                },
            ),
            ReferenceEntity(
                entity_type="aggregations",
                name="Processing Average Aggregation",
                key_fields={
                    "aggregationType": "MAX",
                    "targetField": "processing_average",
                },
            ),
        ],
    },
    expected_counts={
        "products": 1,
        "meters": 1,
        "aggregations": 3,
        "compound_aggregations": 0,
    },
)

# ---------------------------------------------------------------------------
# WF2 — PlanTemplate, Plan, Pricing
# ---------------------------------------------------------------------------

_wf2_reference = WorkflowReference(
    entities={
        "plan_templates": [
            ReferenceEntity(
                entity_type="plan_templates",
                name="Revive Graph Standard Template",
                key_fields={
                    "currency": "USD",
                    "standingCharge": 20.0,
                    "billFrequency": "MONTHLY",
                    "billFrequencyInterval": 1,
                },
            ),
        ],
        "plans": [
            ReferenceEntity(
                entity_type="plans",
                name="Revive Graph Standard Plan",
                key_fields={},
            ),
        ],
        "pricing": [
            # Tiered storage pricing: 0-500 GB @ $0.15/GB, 500+ GB @ $0.10/GB
            ReferenceEntity(
                entity_type="pricing",
                name="Gigabyte Storage Pricing",
                key_fields={
                    "pricingBands_count": 2,
                    "cumulative": True,
                    "band_0_lowerLimit": 0,
                    "band_0_unitPrice": 0.15,
                    "band_1_lowerLimit": 500,
                    "band_1_unitPrice": 0.10,
                },
            ),
            # Flat per-unit file pricing: $0.50/file
            ReferenceEntity(
                entity_type="pricing",
                name="Graphic File Submits Pricing",
                key_fields={
                    "pricingBands_count": 1,
                    "band_0_lowerLimit": 0,
                    "band_0_unitPrice": 0.50,
                },
            ),
            # Stairstep processing pricing: <=4s $12, <=6s $25, >6s $50
            ReferenceEntity(
                entity_type="pricing",
                name="Processing Average Pricing",
                key_fields={
                    "pricingBands_count": 3,
                    "band_0_lowerLimit": 0,
                    "band_0_fixedPrice": 12.0,
                    "band_1_lowerLimit": 4,
                    "band_1_fixedPrice": 25.0,
                    "band_2_lowerLimit": 6,
                    "band_2_fixedPrice": 50.0,
                },
            ),
        ],
    },
    expected_counts={
        "plan_templates": 1,
        "plans": 1,
        "pricing": 3,
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
                name="Revive Graph Customer 1",
                key_fields={
                    "code": "revive_graph_customer_1",
                    "currency": "USD",
                },
            ),
        ],
        "account_plans": [
            ReferenceEntity(
                entity_type="account_plans",
                name="Revive Graph Customer 1 Account Plan",
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

CLOUD_STORAGE = EvalExample(
    name="cloud_storage",
    display_name="Cloud Storage and File Cleanup",
    use_case={
        "title": "Cloud Storage and File Cleanup",
        "description": (
            "Revive Graph Standard is a cloud storage and graphic file processing service. "
            "Customers are billed monthly in USD with a $20 standing charge. "
            "Usage is metered across three dimensions: gigabytes of storage used (tiered pricing "
            "at $0.15/GB for the first 500 GB, $0.10/GB after), number of graphic files submitted "
            "($0.50 per file flat rate), and average processing time per file (stairstep pricing: "
            "up to 4 seconds costs $12, up to 6 seconds costs $25, above 6 seconds costs $50). "
            "A derived field calculates the processing average from total process time divided "
            "by file count."
        ),
        "target_billing_model": "usage_based",
        "billing_frequency": "monthly",
        "currency": "USD",
    },
    wf1_reference=_wf1_reference,
    wf2_reference=_wf2_reference,
    wf3_reference=_wf3_reference,
)

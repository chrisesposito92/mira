"""Example 2: Compound Aggregation for Sign-Up Bonus (App Hosting).

Based on m3ter worked example 2.

WF1: 1 product, 2 meters (apps count, requests count), 2 aggregations (MAX apps, SUM requests),
     1 compound aggregation (requests minus free allowance: sum_requests - max_apps * 100)
WF2: 1 plan template (monthly, USD, no standing charge), 1 plan,
     1 pricing ($0.50/request on compound agg)
WF3: 1 account, 1 account plan
"""

from evals.datasets.base import EvalExample, ReferenceEntity, WorkflowReference

# ---------------------------------------------------------------------------
# WF1 — Product, Meters, Aggregations, Compound Aggregation
# ---------------------------------------------------------------------------

_wf1_reference = WorkflowReference(
    entities={
        "products": [
            ReferenceEntity(
                entity_type="products",
                name="App Hosting Standard",
                key_fields={
                    "code": "app_hosting_standard",
                },
            ),
        ],
        "meters": [
            ReferenceEntity(
                entity_type="meters",
                name="App Hosting Meter 1",
                key_fields={
                    "code": "app_hosting_meter_1",
                    "dataFields_count": 1,
                    "dataFields_categories": ["MEASURE"],
                },
            ),
            ReferenceEntity(
                entity_type="meters",
                name="App Hosting Meter 2",
                key_fields={
                    "code": "app_hosting_meter_2",
                    "dataFields_count": 1,
                    "dataFields_categories": ["MEASURE"],
                },
            ),
        ],
        "aggregations": [
            ReferenceEntity(
                entity_type="aggregations",
                name="Max Apps Hosted",
                key_fields={
                    "aggregationType": "MAX",
                    "targetField": "number_apps",
                },
            ),
            ReferenceEntity(
                entity_type="aggregations",
                name="Number App Requests",
                key_fields={
                    "aggregationType": "SUM",
                    "targetField": "number_requests",
                },
            ),
        ],
        "compound_aggregations": [
            ReferenceEntity(
                entity_type="compound_aggregations",
                name="App Requests Minus Free",
                key_fields={
                    "quantityPerUnit": 1.0,
                    "rounding": "UP",
                    "unit": "requests",
                },
            ),
        ],
    },
    expected_counts={
        "products": 1,
        "meters": 2,
        "aggregations": 2,
        "compound_aggregations": 1,
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
                name="App Hosting Plan Template 1",
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
                name="App Hosting Plan 1",
                key_fields={},
            ),
        ],
        "pricing": [
            # $0.50 per request on the compound aggregation
            ReferenceEntity(
                entity_type="pricing",
                name="App Requests Pricing",
                key_fields={
                    "pricingBands_count": 1,
                    "band_0_lowerLimit": 0,
                    "band_0_unitPrice": 0.50,
                },
            ),
        ],
    },
    expected_counts={
        "plan_templates": 1,
        "plans": 1,
        "pricing": 1,
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
                name="App Hosting Customer 1",
                key_fields={
                    "code": "app_hosting_customer_1",
                    "currency": "USD",
                },
            ),
        ],
        "account_plans": [
            ReferenceEntity(
                entity_type="account_plans",
                name="App Hosting Customer 1 Account Plan",
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

APP_HOSTING = EvalExample(
    name="app_hosting",
    display_name="Compound Aggregation for Sign-Up Bonus",
    use_case={
        "title": "App Hosting with Sign-Up Bonus",
        "description": (
            "App Hosting Standard provides application hosting with a sign-up bonus. "
            "Customers are billed monthly in USD with no standing charge. "
            "Two meters track usage: one counts the number of hosted applications, "
            "and the other counts total API requests. A simple MAX aggregation captures "
            "the peak number of apps hosted in the billing period. A SUM aggregation totals "
            "all requests. A compound aggregation calculates billable requests by subtracting "
            "a free allowance of 100 requests per hosted app from total requests "
            "(sum_requests - max_apps * 100). The billable requests are priced at $0.50 per "
            "request."
        ),
        "target_billing_model": "usage_based",
        "billing_frequency": "monthly",
        "currency": "USD",
    },
    wf1_reference=_wf1_reference,
    wf2_reference=_wf2_reference,
    wf3_reference=_wf3_reference,
)

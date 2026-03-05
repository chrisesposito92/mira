"""Hardcoded m3ter entity schemas for LLM prompt injection and validation."""

from app.schemas.common import EntityType

# Product schema - simple entity
PRODUCT_SCHEMA = {
    "name": {
        "type": "str",
        "required": True,
        "description": "Human-readable product name",
        "max_length": 200,
    },
    "code": {
        "type": "str",
        "required": True,
        "description": "Unique product code (lowercase, alphanumeric + underscore)",
        "pattern": "^[a-z][a-z0-9_]*$",
    },
    "customFields": {
        "type": "dict",
        "required": False,
        "description": "Optional custom key-value pairs",
    },
}

# Meter schema - complex entity with data fields
METER_SCHEMA = {
    "name": {
        "type": "str",
        "required": True,
        "description": "Human-readable meter name",
        "max_length": 200,
    },
    "code": {
        "type": "str",
        "required": True,
        "description": "Unique meter code (lowercase, alphanumeric + underscore)",
        "pattern": "^[a-z][a-z0-9_]*$",
    },
    "productId": {
        "type": "str",
        "required": False,
        "description": "UUID of the parent product (set after product approval)",
    },
    "dataFields": {
        "type": "list[dict]",
        "required": True,
        "min_items": 1,
        "description": "At least one data field for measurement ingestion",
        "item_schema": {
            "name": {
                "type": "str",
                "required": True,
                "description": "Descriptive name of the field",
            },
            "code": {
                "type": "str",
                "required": True,
                "description": "Field code (lowercase)",
            },
            "category": {
                "type": "str",
                "required": True,
                "enum": [
                    "WHO",
                    "WHAT",
                    "WHERE",
                    "MEASURE",
                    "METADATA",
                    "OTHER",
                    "INCOME",
                    "COST",
                ],
                "description": "Field category",
            },
            "unit": {
                "type": "str",
                "required": False,
                "description": "Unit of measurement (e.g., 'GB', 'requests', 'seconds')",
            },
        },
    },
    "derivedFields": {
        "type": "list[dict]",
        "required": True,
        "description": "Computed fields from data fields. Use empty array [] if none needed",
        "item_schema": {
            "name": {
                "type": "str",
                "required": True,
                "description": "Descriptive name of the derived field",
            },
            "code": {"type": "str", "required": True},
            "category": {
                "type": "str",
                "required": True,
                "enum": [
                    "WHO",
                    "WHAT",
                    "WHERE",
                    "MEASURE",
                    "METADATA",
                    "OTHER",
                    "INCOME",
                    "COST",
                ],
                "description": "Field category",
            },
            "calculation": {
                "type": "str",
                "required": True,
                "description": "Formula using data field codes",
            },
            "unit": {"type": "str", "required": False},
        },
    },
}

# Aggregation schema
AGGREGATION_SCHEMA = {
    "name": {
        "type": "str",
        "required": True,
        "description": "Human-readable aggregation name",
        "max_length": 200,
    },
    "code": {
        "type": "str",
        "required": True,
        "description": "Unique aggregation code (lowercase, alphanumeric + underscore)",
        "pattern": "^[a-z][a-z0-9_]*$",
    },
    "meterId": {
        "type": "str",
        "required": False,
        "description": "UUID of the parent meter (set after meter approval)",
    },
    "aggregationType": {
        "type": "str",
        "required": True,
        "enum": ["SUM", "MIN", "MAX", "COUNT", "LATEST", "MEAN", "CUSTOM"],
        "description": "How measurements are aggregated",
    },
    "targetField": {
        "type": "str",
        "required": True,
        "description": "Data field code to aggregate on",
    },
    "rounding": {
        "type": "dict",
        "required": False,
        "description": "Optional rounding configuration",
        "item_schema": {
            "precision": {"type": "int", "required": True},
            "roundingType": {
                "type": "str",
                "required": True,
                "enum": ["UP", "DOWN", "NEAREST"],
            },
        },
    },
    "segmentedFields": {
        "type": "list[str]",
        "required": False,
        "description": "Data field codes to segment aggregation by",
    },
}

# PlanTemplate schema
PLAN_TEMPLATE_SCHEMA = {
    "name": {
        "type": "str",
        "required": True,
        "description": "Human-readable plan template name",
        "max_length": 200,
    },
    "code": {
        "type": "str",
        "required": True,
        "description": "Unique plan template code (lowercase, alphanumeric + underscore)",
        "pattern": "^[a-z][a-z0-9_]*$",
    },
    "productId": {
        "type": "str",
        "required": True,
        "description": "UUID of the parent product",
    },
    "currency": {
        "type": "str",
        "required": True,
        "description": "3-character ISO currency code (e.g., USD, EUR)",
    },
    "standingCharge": {
        "type": "float",
        "required": True,
        "description": "Standing charge amount (>= 0)",
    },
    "billFrequency": {
        "type": "str",
        "required": True,
        "enum": ["DAILY", "WEEKLY", "MONTHLY", "ANNUALLY", "AD_HOC", "MIXED"],
        "description": "How frequently bills are generated",
    },
    "billFrequencyInterval": {
        "type": "int",
        "required": False,
        "description": "Interval for bill frequency (1-365)",
    },
    "minimumSpend": {
        "type": "float",
        "required": False,
        "description": "Minimum spend amount (>= 0)",
    },
    "customFields": {
        "type": "dict",
        "required": False,
        "description": "Optional custom key-value pairs",
    },
}

# Plan schema
PLAN_SCHEMA = {
    "name": {
        "type": "str",
        "required": True,
        "description": "Human-readable plan name",
        "max_length": 200,
    },
    "code": {
        "type": "str",
        "required": True,
        "description": "Unique plan code (lowercase, alphanumeric + underscore)",
        "pattern": "^[a-z][a-z0-9_]*$",
    },
    "planTemplateId": {
        "type": "str",
        "required": True,
        "description": "UUID of the parent plan template",
    },
    "standingCharge": {
        "type": "float",
        "required": False,
        "description": "Override standing charge from template (>= 0)",
    },
    "minimumSpend": {
        "type": "float",
        "required": False,
        "description": "Override minimum spend from template (>= 0)",
    },
    "bespoke": {
        "type": "bool",
        "required": False,
        "description": "Whether this is a bespoke (custom) plan",
    },
    "customFields": {
        "type": "dict",
        "required": False,
        "description": "Optional custom key-value pairs",
    },
}

# Pricing schema
PRICING_SCHEMA = {
    "planId": {
        "type": "str",
        "required": False,
        "description": "UUID of the plan",
    },
    "planTemplateId": {
        "type": "str",
        "required": False,
        "description": "UUID of the plan template",
    },
    "aggregationId": {
        "type": "str",
        "required": False,
        "description": "UUID of the aggregation to price",
    },
    "compoundAggregationId": {
        "type": "str",
        "required": False,
        "description": "UUID of the compound aggregation to price (use instead of aggregationId)",
    },
    "type": {
        "type": "str",
        "required": False,
        "enum": ["DEBIT", "PRODUCT_CREDIT", "GLOBAL_CREDIT"],
        "description": "Pricing type",
    },
    "code": {
        "type": "str",
        "required": False,
        "description": "Pricing code",
    },
    "cumulative": {
        "type": "bool",
        "required": False,
        "description": "Whether pricing bands are cumulative (tiered) or non-cumulative (volume)",
    },
    "startDate": {
        "type": "str",
        "required": True,
        "description": "Start date for pricing (ISO format)",
    },
    "endDate": {
        "type": "str",
        "required": False,
        "description": "End date for pricing",
    },
    "pricingBands": {
        "type": "list[dict]",
        "required": True,
        "min_items": 1,
        "description": "Pricing tiers",
        "item_schema": {
            "lowerLimit": {
                "type": "float",
                "required": True,
                "description": "Lower limit for this band",
            },
            "fixedPrice": {
                "type": "float",
                "required": False,
                "description": "Fixed price for this band",
            },
            "unitPrice": {
                "type": "float",
                "required": False,
                "description": "Per-unit price for this band",
            },
        },
    },
    "overagePricingBands": {
        "type": "list[dict]",
        "required": False,
        "description": "Overage pricing tiers (same structure as pricingBands)",
        "item_schema": {
            "lowerLimit": {
                "type": "float",
                "required": True,
                "description": "Lower limit for this overage band",
            },
            "fixedPrice": {
                "type": "float",
                "required": False,
                "description": "Fixed price for this overage band",
            },
            "unitPrice": {
                "type": "float",
                "required": False,
                "description": "Per-unit price for this overage band",
            },
        },
    },
    "description": {
        "type": "str",
        "required": False,
        "description": "Pricing description",
        "max_length": 200,
    },
    "tiersSpanPlan": {
        "type": "bool",
        "required": False,
        "description": "Whether tiers span across the entire plan",
    },
    "minimumSpend": {
        "type": "float",
        "required": False,
        "description": "Minimum spend amount (>= 0)",
    },
    "customFields": {
        "type": "dict",
        "required": False,
        "description": "Optional custom key-value pairs",
    },
}

# Account schema
ACCOUNT_SCHEMA = {
    "name": {
        "type": "str",
        "required": True,
        "description": "Human-readable account name",
        "max_length": 200,
    },
    "code": {
        "type": "str",
        "required": True,
        "description": "Unique account code (lowercase, alphanumeric + underscore)",
        "pattern": "^[a-z][a-z0-9_]*$",
    },
    "email": {
        "type": "str",
        "required": True,
        "description": "Primary contact email for the account",
    },
    "currency": {
        "type": "str",
        "required": False,
        "description": "3-character ISO currency code (e.g., USD, EUR)",
    },
    "address": {
        "type": "dict",
        "required": False,
        "description": "Account address (line1, line2, city, state, postCode, country)",
    },
    "parentAccountId": {
        "type": "str",
        "required": False,
        "description": "UUID of parent account for hierarchical billing",
    },
    "purchaseOrderNumber": {
        "type": "str",
        "required": False,
        "description": "Purchase order number for the account",
    },
    "daysBeforeBillDue": {
        "type": "int",
        "required": False,
        "description": "Days before bill is due (>= 0)",
    },
    "customFields": {
        "type": "dict",
        "required": False,
        "description": "Optional custom key-value pairs",
    },
}

# AccountPlan schema
ACCOUNT_PLAN_SCHEMA = {
    "accountId": {
        "type": "str",
        "required": True,
        "description": "UUID of the account to attach the plan to",
    },
    "planId": {
        "type": "str",
        "required": True,
        "description": "UUID of the plan to assign",
    },
    "startDate": {
        "type": "str",
        "required": True,
        "description": "Start date for the account plan (ISO format)",
    },
    "endDate": {
        "type": "str",
        "required": False,
        "description": "End date for the account plan (ISO format)",
    },
    "customFields": {
        "type": "dict",
        "required": False,
        "description": "Optional custom key-value pairs",
    },
}

# Measurement schema
MEASUREMENT_SCHEMA = {
    "uid": {
        "type": "str",
        "required": True,
        "description": "Unique identifier for idempotent submission",
    },
    "meter": {
        "type": "str",
        "required": True,
        "description": "Meter code (NOT UUID) to submit measurement against",
    },
    "account": {
        "type": "str",
        "required": True,
        "description": "Account code (NOT UUID) to submit measurement for",
    },
    "ts": {
        "type": "str",
        "required": True,
        "description": "Timestamp in ISO 8601 format (e.g., 2024-01-15T10:30:00Z)",
    },
    "end_ts": {
        "type": "str",
        "required": False,
        "description": "End timestamp for duration-based measurements (ISO 8601)",
    },
    "data": {
        "type": "dict",
        "required": True,
        "description": "Measurement data with numeric values keyed by data field codes",
    },
}

# Compound Aggregation schema — calculated from simple aggregations using formulas
COMPOUND_AGGREGATION_SCHEMA = {
    "name": {
        "type": "str",
        "required": True,
        "description": "Human-readable compound aggregation name",
        "max_length": 200,
    },
    "code": {
        "type": "str",
        "required": True,
        "description": "Unique compound aggregation code (lowercase, alphanumeric + underscore)",
        "pattern": "^[a-z][a-z0-9_]*$",
    },
    "calculation": {
        "type": "str",
        "required": True,
        "description": (
            'Formula referencing aggregation codes, e.g. "agg_code_1 - (agg_code_2 * 100)"'
        ),
    },
    "quantityPerUnit": {
        "type": "float",
        "required": True,
        "description": "Units divisor (usually 1.0)",
    },
    "rounding": {
        "type": "str",
        "required": True,
        "enum": ["UP", "DOWN", "NEAREST", "NONE"],
        "description": "Rounding mode for the calculated result",
    },
    "unit": {
        "type": "str",
        "required": True,
        "description": "User-defined unit label (e.g. 'requests', 'GB')",
    },
    "productId": {
        "type": "str",
        "required": False,
        "description": "UUID of the parent product",
    },
    "customFields": {
        "type": "dict",
        "required": False,
        "description": "Optional custom key-value pairs",
    },
}

_SCHEMAS = {
    EntityType.product: PRODUCT_SCHEMA,
    EntityType.meter: METER_SCHEMA,
    EntityType.aggregation: AGGREGATION_SCHEMA,
    EntityType.plan_template: PLAN_TEMPLATE_SCHEMA,
    EntityType.plan: PLAN_SCHEMA,
    EntityType.pricing: PRICING_SCHEMA,
    EntityType.account: ACCOUNT_SCHEMA,
    EntityType.account_plan: ACCOUNT_PLAN_SCHEMA,
    EntityType.measurement: MEASUREMENT_SCHEMA,
    EntityType.compound_aggregation: COMPOUND_AGGREGATION_SCHEMA,
}


def get_schema(entity_type: EntityType) -> dict:
    """Get the schema definition for an entity type."""
    if entity_type not in _SCHEMAS:
        raise ValueError(f"No schema defined for entity type: {entity_type}")
    return _SCHEMAS[entity_type]


def get_schema_as_prompt_text(entity_type: EntityType) -> str:
    """Format a schema as human-readable text for LLM prompts."""
    schema = get_schema(entity_type)
    lines = [f"## {entity_type.value.title()} Schema\n"]
    for field_name, field_def in schema.items():
        required = "REQUIRED" if field_def.get("required") else "optional"
        desc = field_def.get("description", "")
        field_type = field_def.get("type", "")
        enum_vals = field_def.get("enum")
        line = f"- **{field_name}** ({field_type}, {required}): {desc}"
        if enum_vals:
            line += f" Values: {', '.join(enum_vals)}"
        lines.append(line)
        # Nested item schemas
        if "item_schema" in field_def:
            for sub_name, sub_def in field_def["item_schema"].items():
                sub_req = "REQUIRED" if sub_def.get("required") else "optional"
                sub_desc = sub_def.get("description", "")
                sub_enum = sub_def.get("enum")
                sub_line = f"  - **{sub_name}** ({sub_def.get('type', '')}, {sub_req}): {sub_desc}"
                if sub_enum:
                    sub_line += f" Values: {', '.join(sub_enum)}"
                lines.append(sub_line)
    return "\n".join(lines)

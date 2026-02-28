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
        "required": False,
        "description": "Optional computed fields from data fields",
        "item_schema": {
            "code": {"type": "str", "required": True},
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

_SCHEMAS = {
    EntityType.product: PRODUCT_SCHEMA,
    EntityType.meter: METER_SCHEMA,
    EntityType.aggregation: AGGREGATION_SCHEMA,
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

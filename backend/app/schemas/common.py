"""Shared enums and common response models."""

from enum import StrEnum

from pydantic import BaseModel


class EntityType(StrEnum):
    product = "product"
    meter = "meter"
    aggregation = "aggregation"
    compound_aggregation = "compound_aggregation"
    plan_template = "plan_template"
    plan = "plan"
    pricing = "pricing"
    account = "account"
    account_plan = "account_plan"
    measurement = "measurement"


class ObjectStatus(StrEnum):
    draft = "draft"
    approved = "approved"
    rejected = "rejected"
    pushed = "pushed"
    push_failed = "push_failed"


class WorkflowType(StrEnum):
    product_meter_aggregation = "product_meter_aggregation"
    plan_pricing = "plan_pricing"
    account_setup = "account_setup"
    usage_submission = "usage_submission"


class WorkflowStatus(StrEnum):
    pending = "pending"
    running = "running"
    interrupted = "interrupted"
    completed = "completed"
    failed = "failed"


class UseCaseStatus(StrEnum):
    draft = "draft"
    in_progress = "in_progress"
    completed = "completed"


class BillingFrequency(StrEnum):
    monthly = "monthly"
    quarterly = "quarterly"
    annually = "annually"


class ConnectionStatus(StrEnum):
    untested = "untested"
    connected = "connected"
    failed = "failed"


class DocumentStatus(StrEnum):
    pending = "pending"
    processing = "processing"
    ready = "ready"
    failed = "failed"


class MessageRole(StrEnum):
    user = "user"
    assistant = "assistant"
    system = "system"
    tool = "tool"


class MessageResponse(BaseModel):
    message: str

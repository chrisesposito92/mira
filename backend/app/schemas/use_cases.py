"""Schemas for use_cases endpoints."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import BillingFrequency, UseCaseStatus


class UseCaseCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    contract_start_date: date | None = None
    billing_frequency: BillingFrequency | None = None
    currency: str = "USD"
    target_billing_model: str | None = None
    notes: str | None = None


class UseCaseUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    status: UseCaseStatus | None = None
    contract_start_date: date | None = None
    billing_frequency: BillingFrequency | None = None
    currency: str | None = None
    target_billing_model: str | None = None
    notes: str | None = None


class UseCaseResponse(BaseModel):
    id: UUID
    project_id: UUID
    title: str
    description: str | None = None
    status: UseCaseStatus
    contract_start_date: date | None = None
    billing_frequency: BillingFrequency | None = None
    currency: str
    target_billing_model: str | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

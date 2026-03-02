"""Schemas for use case generator endpoints."""

from pydantic import BaseModel

from app.schemas.common import BillingFrequency


class ExtractTextResponse(BaseModel):
    text: str


class GeneratedUseCaseItem(BaseModel):
    title: str
    description: str
    billing_frequency: BillingFrequency | None = None
    currency: str = "USD"
    target_billing_model: str | None = None
    notes: str | None = None

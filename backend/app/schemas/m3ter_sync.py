"""Pydantic models for m3ter push/sync API endpoints."""

from uuid import UUID

from pydantic import BaseModel


class PushResultResponse(BaseModel):
    """Result of pushing a single entity."""

    entity_id: str
    entity_type: str
    success: bool
    m3ter_id: str | None = None
    error: str | None = None


class BulkPushRequest(BaseModel):
    """Request body for bulk push."""

    object_ids: list[UUID] | None = None


class BulkPushResultResponse(BaseModel):
    """Result of a bulk push operation."""

    results: list[PushResultResponse]
    total: int
    succeeded: int
    failed: int
    skipped: int


class PushStatusResponse(BaseModel):
    """Push readiness info for a use case."""

    org_connected: bool
    eligible_count: int
    pushed_count: int
    total_count: int
    entity_breakdown: dict[str, dict[str, int]]

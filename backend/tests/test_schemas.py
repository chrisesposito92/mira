"""Tests for Pydantic schemas — validation, enums, required fields."""

import pytest
from pydantic import ValidationError

from app.schemas.common import (
    BillingFrequency,
    ConnectionStatus,
    DocumentStatus,
    EntityType,
    ObjectStatus,
    UseCaseStatus,
    WorkflowStatus,
    WorkflowType,
)
from app.schemas.generated_objects import BulkStatusUpdate, GeneratedObjectUpdate
from app.schemas.org_connections import OrgConnectionCreate, OrgConnectionUpdate
from app.schemas.projects import ProjectCreate, ProjectUpdate
from app.schemas.use_cases import UseCaseCreate, UseCaseUpdate

# --- Enum tests ---


class TestEnums:
    def test_entity_type_valid(self):
        assert EntityType("product") == EntityType.product
        assert EntityType("compound_aggregation") == EntityType.compound_aggregation

    def test_entity_type_invalid(self):
        with pytest.raises(ValueError):
            EntityType("nonexistent")

    def test_object_status_values(self):
        assert set(ObjectStatus) == {"draft", "approved", "rejected", "pushed", "push_failed"}

    def test_workflow_type_values(self):
        assert len(WorkflowType) == 4

    def test_workflow_status_values(self):
        assert "interrupted" in set(WorkflowStatus)

    def test_use_case_status_values(self):
        assert set(UseCaseStatus) == {"draft", "in_progress", "completed"}

    def test_billing_frequency_values(self):
        assert set(BillingFrequency) == {"monthly", "quarterly", "annually"}

    def test_connection_status_values(self):
        assert set(ConnectionStatus) == {"active", "inactive", "error"}

    def test_document_status_values(self):
        assert set(DocumentStatus) == {"pending", "processing", "ready", "failed"}


# --- OrgConnection schemas ---


class TestOrgConnectionSchemas:
    def test_create_valid(self):
        data = OrgConnectionCreate(
            org_id="org-123",
            org_name="Test Org",
            client_id="cid",
            client_secret="csec",
        )
        assert data.api_url == "https://api.m3ter.com"

    def test_create_missing_required(self):
        with pytest.raises(ValidationError):
            OrgConnectionCreate(org_name="Test Org", client_id="cid", client_secret="csec")

    def test_create_empty_org_id(self):
        with pytest.raises(ValidationError):
            OrgConnectionCreate(
                org_id="", org_name="Test Org", client_id="cid", client_secret="csec"
            )

    def test_update_all_optional(self):
        data = OrgConnectionUpdate()
        assert data.model_dump(exclude_unset=True) == {}

    def test_update_partial(self):
        data = OrgConnectionUpdate(org_name="Updated")
        dumped = data.model_dump(exclude_unset=True)
        assert dumped == {"org_name": "Updated"}


# --- Project schemas ---


class TestProjectSchemas:
    def test_create_valid_minimal(self):
        data = ProjectCreate(name="My Project")
        assert data.name == "My Project"
        assert data.org_connection_id is None

    def test_create_missing_name(self):
        with pytest.raises(ValidationError):
            ProjectCreate()

    def test_create_empty_name(self):
        with pytest.raises(ValidationError):
            ProjectCreate(name="")

    def test_update_all_optional(self):
        data = ProjectUpdate()
        assert data.model_dump(exclude_unset=True) == {}


# --- UseCase schemas ---


class TestUseCaseSchemas:
    def test_create_valid(self):
        data = UseCaseCreate(title="Metering setup")
        assert data.currency == "USD"
        assert data.billing_frequency is None

    def test_create_with_billing_frequency(self):
        data = UseCaseCreate(title="Test", billing_frequency="monthly")
        assert data.billing_frequency == BillingFrequency.monthly

    def test_create_invalid_billing_frequency(self):
        with pytest.raises(ValidationError):
            UseCaseCreate(title="Test", billing_frequency="weekly")

    def test_update_with_status(self):
        data = UseCaseUpdate(status="in_progress")
        assert data.status == UseCaseStatus.in_progress


# --- GeneratedObject schemas ---


class TestGeneratedObjectSchemas:
    def test_update_partial(self):
        data = GeneratedObjectUpdate(status="approved")
        assert data.status == ObjectStatus.approved

    def test_bulk_update(self):
        data = BulkStatusUpdate(
            ids=["00000000-0000-0000-0000-000000000001"],
            status="pushed",
        )
        assert len(data.ids) == 1
        assert data.status == ObjectStatus.pushed

    def test_bulk_update_invalid_status(self):
        with pytest.raises(ValidationError):
            BulkStatusUpdate(
                ids=["00000000-0000-0000-0000-000000000001"],
                status="invalid_status",
            )

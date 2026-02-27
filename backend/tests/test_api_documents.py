"""Tests for /api/documents endpoints."""

import io
from datetime import datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from tests.conftest import MOCK_USER_ID


def _project_row(**overrides):
    defaults = {
        "id": str(uuid4()),
        "user_id": str(MOCK_USER_ID),
        "name": "Test Project",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }
    defaults.update(overrides)
    return defaults


def _doc_row(**overrides):
    defaults = {
        "id": str(uuid4()),
        "project_id": str(uuid4()),
        "filename": "test.pdf",
        "file_type": "pdf",
        "file_size_bytes": 1024,
        "storage_path": "pending/test/test.pdf",
        "processing_status": "pending",
        "chunk_count": 0,
        "error_message": None,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }
    defaults.update(overrides)
    return defaults


class TestUploadDocument:
    def test_upload_valid_pdf(self, authed_client, mock_supabase):
        pid = str(uuid4())
        mock_supabase._table_data["projects"] = [_project_row(id=pid)]
        mock_supabase._table_data["documents"] = [_doc_row(project_id=pid)]
        file_content = b"fake pdf content"
        resp = authed_client.post(
            f"/api/projects/{pid}/documents",
            files={"file": ("test.pdf", io.BytesIO(file_content), "application/pdf")},
        )
        assert resp.status_code == 201

    def test_upload_invalid_file_type(self, authed_client, mock_supabase):
        pid = str(uuid4())
        mock_supabase._table_data["projects"] = [_project_row(id=pid)]
        resp = authed_client.post(
            f"/api/projects/{pid}/documents",
            files={"file": ("test.exe", io.BytesIO(b"data"), "application/octet-stream")},
        )
        assert resp.status_code == 400
        assert "not allowed" in resp.json()["detail"]

    def test_upload_file_too_large(self, authed_client, mock_supabase):
        pid = str(uuid4())
        mock_supabase._table_data["projects"] = [_project_row(id=pid)]
        large_content = b"x" * (10 * 1024 * 1024 + 1)  # 10 MB + 1 byte
        resp = authed_client.post(
            f"/api/projects/{pid}/documents",
            files={"file": ("big.pdf", io.BytesIO(large_content), "application/pdf")},
        )
        assert resp.status_code == 400
        assert "10 MB" in resp.json()["detail"]


class TestListDocuments:
    def test_list_success(self, authed_client, mock_supabase):
        pid = str(uuid4())
        mock_supabase._table_data["projects"] = [_project_row(id=pid)]
        mock_supabase._table_data["documents"] = [_doc_row(project_id=pid)]
        resp = authed_client.get(f"/api/projects/{pid}/documents")
        assert resp.status_code == 200
        assert len(resp.json()) == 1


class TestGetDocument:
    def test_get_success(self, authed_client, mock_supabase):
        did = str(uuid4())
        row = _doc_row(id=did)
        row["projects"] = {"user_id": str(MOCK_USER_ID)}
        mock_supabase._table_data["documents"] = [row]
        resp = authed_client.get(f"/api/documents/{did}")
        assert resp.status_code == 200

    def test_get_not_found(self, authed_client, mock_supabase):
        mock_supabase._table_data["documents"] = []
        resp = authed_client.get(f"/api/documents/{uuid4()}")
        assert resp.status_code == 404


class TestDeleteDocument:
    def test_delete_success(self, authed_client, mock_supabase):
        did = str(uuid4())
        row = _doc_row(id=did)
        row["projects"] = {"user_id": str(MOCK_USER_ID)}
        mock_supabase._table_data["documents"] = [row]
        with (
            patch(
                "app.services.document_service.get_db_pool",
                AsyncMock(return_value=AsyncMock()),
            ),
            patch(
                "app.services.document_service.delete_by_source_id",
                AsyncMock(return_value=0),
            ),
            patch(
                "app.services.document_service.Path.unlink",
            ),
        ):
            resp = authed_client.delete(f"/api/documents/{did}")
        assert resp.status_code == 204

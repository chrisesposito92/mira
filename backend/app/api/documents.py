"""API routes for documents."""

from uuid import UUID

from fastapi import APIRouter, Depends, UploadFile, status
from supabase import Client

from app.dependencies import get_current_user, get_supabase
from app.schemas.documents import DocumentResponse
from app.services import document_service as svc

router = APIRouter(tags=["documents"])


@router.post(
    "/api/projects/{project_id}/documents",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    project_id: UUID,
    file: UploadFile,
    user_id: UUID = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
):
    return await svc.upload_document(supabase, user_id, project_id, file)


@router.get("/api/projects/{project_id}/documents", response_model=list[DocumentResponse])
async def list_documents(
    project_id: UUID,
    user_id: UUID = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
):
    return svc.list_documents(supabase, user_id, project_id)


@router.get("/api/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    user_id: UUID = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
):
    return svc.get_document(supabase, user_id, document_id)


@router.delete("/api/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    user_id: UUID = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
):
    svc.delete_document(supabase, user_id, document_id)

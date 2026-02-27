"""Central API router collecting all sub-routers."""

from fastapi import APIRouter

from app.api.documents import router as documents_router
from app.api.generated_objects import router as generated_objects_router
from app.api.org_connections import router as org_connections_router
from app.api.projects import router as projects_router
from app.api.use_cases import router as use_cases_router
from app.api.workflows import router as workflows_router

api_router = APIRouter()
api_router.include_router(org_connections_router)
api_router.include_router(projects_router)
api_router.include_router(use_cases_router)
api_router.include_router(documents_router)
api_router.include_router(generated_objects_router)
api_router.include_router(workflows_router)

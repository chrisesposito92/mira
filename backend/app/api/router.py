"""Central API router collecting all sub-routers."""

from fastapi import APIRouter

from app.api.chat_messages import router as chat_messages_router
from app.api.component_library import router as component_library_router
from app.api.diagrams import router as diagrams_router
from app.api.documents import router as documents_router
from app.api.generated_objects import router as generated_objects_router
from app.api.logos import router as logos_router
from app.api.m3ter_sync import router as m3ter_sync_router
from app.api.org_connections import router as org_connections_router
from app.api.projects import router as projects_router
from app.api.use_case_generator import router as use_case_generator_router
from app.api.use_cases import router as use_cases_router
from app.api.workflows import router as workflows_router
from app.api.ws import router as ws_router

api_router = APIRouter()
api_router.include_router(org_connections_router)
api_router.include_router(projects_router)
api_router.include_router(use_cases_router)
api_router.include_router(documents_router)
api_router.include_router(generated_objects_router)
api_router.include_router(m3ter_sync_router)
api_router.include_router(workflows_router)
api_router.include_router(chat_messages_router)
api_router.include_router(use_case_generator_router)
api_router.include_router(ws_router)
api_router.include_router(component_library_router)
api_router.include_router(diagrams_router)
api_router.include_router(logos_router)

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db import close_db_pool, get_db_pool


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await get_db_pool()
    yield
    # Shutdown
    await close_db_pool()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        description="AI-powered m3ter configuration assistant",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health():
        return {"status": "healthy", "service": "mira-backend"}

    return app


app = create_app()

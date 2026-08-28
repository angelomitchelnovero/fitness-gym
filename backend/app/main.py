"""FastAPI application entry point."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.core.config import settings


def create_app() -> FastAPI:
    """Application factory."""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        openapi_url=f"{settings.API_PREFIX}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS
    origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/", tags=["meta"])
    def root() -> dict[str, str]:
        return {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "env": settings.APP_ENV,
        }

    @app.get("/health", tags=["meta"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(api_router, prefix=settings.API_PREFIX)

    return app


app = create_app()

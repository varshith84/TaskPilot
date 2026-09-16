"""
TaskPilot FastAPI application factory.

This module creates and configures the FastAPI app instance.
Import `app` from here or use it via uvicorn entrypoint.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import health, documents, chat
from app.core.config import settings
from app.core.logging import setup_logging
from app.models.schemas import ErrorResponse

# ---------------------------------------------------------------------------
# Bootstrap logging immediately on import so all subsequent log calls work.
# ---------------------------------------------------------------------------
setup_logging(
    level=logging.DEBUG if settings.is_development else logging.INFO,
    env=settings.APP_ENV,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan context manager (replaces deprecated on_event handlers)
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:  # noqa: ARG001
    """Handle startup and shutdown logic using the modern lifespan API."""
    # --- Startup ---
    logger.info("=" * 60)
    logger.info("  %s API  v%s", settings.APP_NAME, settings.APP_VERSION)
    logger.info("  Environment : %s", settings.APP_ENV)
    logger.info("  Docs        : http://localhost:8000/docs")
    logger.info("  CORS origins: %s", settings.allowed_origins)
    logger.info("=" * 60)

    try:
        settings.ensure_data_directories()
        logger.info(
            "Data directories verified: uploads=%s  vector_store=%s",
            settings.UPLOAD_DIR,
            settings.VECTOR_STORE_PATH,
        )
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to create data directories: %s", exc)

    yield  # Application runs here.

    # --- Shutdown ---
    logger.info("%s API shutting down.", settings.APP_NAME)


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI(
        title=f"{settings.APP_NAME} API",
        description=(
            "TaskPilot — Multi-Tool AI Agent API.\n\n"
            "Provides document management, AI chat, and RAG retrieval "
            "powered by LangGraph and LangChain."
        ),
        version=settings.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # ------------------------------------------------------------------
    # CORS middleware
    # ------------------------------------------------------------------
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ------------------------------------------------------------------
    # Global exception handler — catch unhandled errors gracefully.
    # ------------------------------------------------------------------
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                detail="An unexpected internal error occurred.",
                code="INTERNAL_SERVER_ERROR",
            ).model_dump(mode="json"),
        )

    # ------------------------------------------------------------------
    # Register API routers under the /api prefix.
    # ------------------------------------------------------------------
    API_PREFIX = "/api"

    app.include_router(health.router, prefix=API_PREFIX)
    # Documents and chat routers are registered now (empty) so their
    # tags appear in the OpenAPI schema; endpoints will be added later.
    app.include_router(documents.router, prefix=API_PREFIX)
    app.include_router(chat.router, prefix=API_PREFIX)

    return app


# ---------------------------------------------------------------------------
# Module-level app instance used by uvicorn.
# ---------------------------------------------------------------------------
app = create_app()

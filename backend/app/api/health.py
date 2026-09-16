"""
Health check API router.

GET /api/health — returns structured liveness information.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.core.config import settings
from app.core.logging import get_logger
from app.models.schemas import HealthResponse

logger = get_logger(__name__)

router = APIRouter(prefix="/health", tags=["Health"])


@router.get(
    "",
    response_model=HealthResponse,
    summary="Application health check",
    description=(
        "Returns the current liveness status of the TaskPilot API. "
        "Useful for load-balancer probes and monitoring dashboards."
    ),
)
async def health_check() -> HealthResponse:
    """Return the current health status of the API."""
    logger.debug("Health check requested.")
    return HealthResponse(
        status="healthy",
        service=f"{settings.APP_NAME} API",
        version=settings.APP_VERSION,
        environment=settings.APP_ENV,
    )

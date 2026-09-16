"""
Pydantic schemas for the TaskPilot API.

Only schemas that are genuinely required in Phase 1 are defined here.
Future schemas for chat messages, documents, and agent responses will be
added in later phases when the corresponding functionality is implemented.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Literal, Optional, List

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Health endpoint
# ---------------------------------------------------------------------------


class HealthResponse(BaseModel):
    """Response model for GET /api/health."""

    status: Literal["healthy", "degraded", "unhealthy"] = "healthy"
    service: str = Field(description="Human-readable service name")
    version: str = Field(description="Application version string")
    environment: str = Field(description="Current deployment environment")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of the health check",
    )

    model_config = {"json_schema_extra": {"example": {
        "status": "healthy",
        "service": "TaskPilot API",
        "version": "0.1.0",
        "environment": "development",
        "timestamp": "2024-01-01T00:00:00Z",
    }}}


# ---------------------------------------------------------------------------
# Generic error response
# ---------------------------------------------------------------------------


class ErrorResponse(BaseModel):
    """Standard error envelope returned for 4xx / 5xx responses."""

    detail: str = Field(description="Human-readable error message")
    code: Optional[str] = Field(default=None, description="Machine-readable error code")
    meta: Optional[Dict[str, Any]] = Field(default=None, description="Optional additional context")

    model_config = {"json_schema_extra": {"example": {
        "detail": "Resource not found.",
        "code": "NOT_FOUND",
        "meta": None,
    }}}

# ---------------------------------------------------------------------------
# Chat endpoints
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    """Request model for POST /api/chat."""
    message: str = Field(..., min_length=1, max_length=20000, description="The user's message.")
    session_id: Optional[str] = Field(default=None, description="Optional session ID for conversation memory.")
    document_ids: Optional[List[str]] = Field(default=None, description="Optional list of document IDs to scope the chat.")

    model_config = {"json_schema_extra": {"example": {
        "message": "What does my uploaded paper say?",
        "session_id": "optional-uuid",
        "document_ids": ["uuid-1234"]
    }}}

class ToolTraceItem(BaseModel):
    """Observable tool execution metadata."""
    tool: str
    status: Literal["completed", "error"]
    description: str

class DocumentSource(BaseModel):
    """A source piece of evidence retrieved from an uploaded document."""
    type: Literal["document"] = "document"
    document_id: str
    filename: str
    page: Optional[int] = None
    chunk_id: Optional[str] = None
    snippet: str

class WebSource(BaseModel):
    """A source piece of evidence retrieved from the web."""
    type: Literal["web"] = "web"
    title: Optional[str] = None
    url: str
    snippet: str

class ChatResponse(BaseModel):
    """Response model for POST /api/chat."""
    session_id: str
    answer: str
    tools_used: List[str] = Field(default_factory=list)
    tool_trace: List[ToolTraceItem] = Field(default_factory=list)
    sources: List[Any] = Field(default_factory=list, description="List of DocumentSource or WebSource")

ChatRequest.model_rebuild()
ChatResponse.model_rebuild()

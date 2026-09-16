"""
Chat API router.
"""

from __future__ import annotations

import logging
from fastapi import APIRouter, HTTPException, status

from app.models.schemas import ChatRequest, ChatResponse, ErrorResponse
from app.services.agent_service import run_agent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])

@router.post("", response_model=ChatResponse, responses={
    400: {"model": ErrorResponse},
    500: {"model": ErrorResponse},
    503: {"model": ErrorResponse}
})
def chat(request: ChatRequest):
    """
    Interact with the TaskPilot AI agent.
    """
    message = request.message.strip()
    if not message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message cannot be empty."
        )
        
    try:
        result = run_agent(
            message=message,
            session_id=request.session_id,
            document_ids=request.document_ids
        )
        return ChatResponse(**result)
        
    except ValueError as ve:
        # This covers our specific "GEMINI_API_KEY is not configured"
        # as well as Document ID validation errors from the service layer.
        error_msg = str(ve)
        if "GEMINI_API_KEY" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"code": "llm_not_configured", "message": "TaskPilot AI is not configured. Set GEMINI_API_KEY."}
            )
        
        # It's a standard ValueError
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
            
    except RuntimeError as re:
        message = str(re)
        provider_failure = message.startswith("The AI provider")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY if provider_failure else status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=message
        )
        
    except Exception as e:
        logger.exception("Unexpected error in chat endpoint.")
        # Attempt to categorize provider errors from strings if needed, 
        # but defaulting to 502 Bad Gateway if it's external, or 500 otherwise.
        if "429" in str(e) or "503" in str(e) or "provider" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Error communicating with the AI provider."
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected internal error occurred."
        )

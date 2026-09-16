"""
Centralized LLM Factory.
"""
from typing import Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import settings

_chat_model: Optional[ChatGoogleGenerativeAI] = None

def get_chat_model() -> ChatGoogleGenerativeAI:
    """
    Returns a cached instance of the chat model.
    Throws ValueError if the API key is not configured.
    """
    global _chat_model
    if _chat_model is None:
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not configured.")
            
        _chat_model = ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL,
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.0
        )
    return _chat_model

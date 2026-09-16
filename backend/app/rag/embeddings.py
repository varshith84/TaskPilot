"""
Embedding model abstraction for vector operations.
Provides a singleton instance of the embedding model to avoid repeated expensive loading.
"""

from __future__ import annotations

from typing import Optional
from langchain_huggingface import HuggingFaceEmbeddings

# Singleton instance
_embedding_model: Optional[HuggingFaceEmbeddings] = None

def get_embedding_model() -> HuggingFaceEmbeddings:
    """
    Get or create the embedding model.
    Uses sentence-transformers/all-MiniLM-L6-v2 running locally.
    """
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
    return _embedding_model

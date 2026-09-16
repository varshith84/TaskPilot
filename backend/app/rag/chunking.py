"""
Text chunking utilities for RAG ingestion.
"""

from __future__ import annotations

import uuid
from typing import List

from langchain_core.documents import Document

from app.core.config import settings

def chunk_documents(documents: list[Document]) -> list[Document]:
    """
    Split documents into smaller chunks suitable for embedding.
    Ensures every chunk has a unique chunk_id and preserves necessary metadata.
    """
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.RAG_CHUNK_SIZE,
        chunk_overlap=settings.RAG_CHUNK_OVERLAP,
        separators=["\n\n", "\n", " ", ""]
    )
    
    chunks = splitter.split_documents(documents)
    
    # Add unique chunk IDs and ensure base metadata is intact
    for chunk in chunks:
        if "chunk_id" not in chunk.metadata:
            chunk.metadata["chunk_id"] = str(uuid.uuid4())
            
    return chunks

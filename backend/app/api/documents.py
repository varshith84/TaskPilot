"""
Documents API router for uploading, listing, deleting and searching knowledge base documents.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from pydantic import BaseModel

from app.core.config import settings
from app.services import document_service

router = APIRouter(prefix="/documents", tags=["Documents"])


# --- Schemas ---

class SearchRequest(BaseModel):
    query: str
    document_ids: Optional[List[str]] = None
    top_k: Optional[int] = None

class SearchResultItem(BaseModel):
    document_id: str
    filename: str
    chunk_id: str
    page: Optional[int] = None
    content: str
    distance: float

class SearchResponse(BaseModel):
    query: str
    results: List[SearchResultItem]


# --- Endpoints ---

@router.post("/upload", status_code=status.HTTP_201_CREATED)
def upload_document(file: UploadFile = File(...)):
    """
    Upload a document for parsing, chunking, embedding and storage in the vector database.
    Supported formats: .pdf, .txt, .md, .docx.
    """
    try:
        # Check size hint if possible, but FastAPI handles real limit via max_request_size or manually
        doc_info = document_service.ingest_document(file)
        return doc_info
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Ingestion failed: {e}")


@router.get("")
def list_documents():
    """
    List all uploaded documents (newest first).
    """
    try:
        docs = document_service.list_documents()
        return {"documents": docs}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(document_id: str):
    """
    Delete a document, its physical file, and all associated vector store chunks.
    """
    try:
        deleted = document_service.delete_document(document_id)
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/search", response_model=SearchResponse)
def search_documents(request: SearchRequest):
    """
    Development endpoint to test semantic retrieval from the vector store.
    """
    try:
        results = document_service.search_documents(
            query=request.query,
            document_ids=request.document_ids,
            top_k=request.top_k
        )
        return SearchResponse(query=request.query, results=results)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

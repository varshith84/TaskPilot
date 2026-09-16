"""
Document service orchestrating ingestion, retrieval, listing and deletion.
Provides the core business logic separating API routes from underlying storage/ML mechanisms.
"""

from __future__ import annotations

import os
import shutil
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import UploadFile

from app.core.config import settings
from app.core.logging import get_logger
from app.db import metadata

logger = get_logger(__name__)


def _secure_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal and remove strange characters."""
    import re
    # Keep only alphanumerics, hyphens, underscores, dots
    clean = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', filename)
    # Strip any leading dots/hyphens
    return clean.lstrip(".-_")


def ingest_document(upload: UploadFile) -> Dict[str, Any]:
    """
    Complete ingestion pipeline:
    1. Validate extension & sizes (size done mostly by FastAPI limit config).
    2. Save safely to disk.
    3. Parse to LangChain Documents.
    4. Chunk.
        1. Validate extension and enforce the configured size limit.
    6. Persist metadata.
    """
    if not upload.filename:
        raise ValueError("Filename is required.")
        
    ext = upload.filename.split('.')[-1].lower() if '.' in upload.filename else ""
    if ext not in ["pdf", "txt", "md", "docx"]:
        raise ValueError(f"Unsupported file extension: {ext}")
        
    document_id = str(uuid.uuid4())
    safe_name = _secure_filename(upload.filename)
    stored_filename = f"{document_id}_{safe_name}"
    stored_path = settings.UPLOAD_DIR / stored_filename
    
    logger.info("Starting ingestion for %s (ID: %s)", upload.filename, document_id)
    
    # Write file to disk
    try:
        with open(stored_path, "wb") as buffer:
            shutil.copyfileobj(upload.file, buffer)
            
        file_size = os.path.getsize(stored_path)
        if file_size == 0:
            os.remove(stored_path)
            raise ValueError("File is empty.")

        from app.rag import chunking, loaders, vector_store
            
        # Initial DB record (processing)
        metadata.insert_document(
            document_id=document_id,
            filename=upload.filename,
            stored_filename=stored_filename,
            file_type=ext,
            file_size=file_size,
            pages=None,
            chunks=0,
            status="processing"
        )
        
        # Parse
        docs = loaders.load_document(str(stored_path), ext, document_id, upload.filename)
        if not docs:
            raise ValueError("No extractable content found in document.")
            
        # Extract page count safely if applicable
        pages = max([d.metadata.get("page", 1) for d in docs]) if ext == "pdf" else None
        
        # Chunk
        chunks = chunking.chunk_documents(docs)
        if not chunks:
            raise ValueError("Document yielded no chunks after processing.")
            
        # Add to vector store
        vector_store.add_chunks_to_store(chunks)
        
        # Update metadata to ready
        num_chunks = len(chunks)
        metadata.update_document_after_ingestion(
            document_id=document_id,
            chunks=num_chunks,
            pages=pages,
            status="ready"
        )
        
        logger.info("Successfully ingested %s: %d chunks.", upload.filename, num_chunks)
        
        # Fetch the updated record to return
        doc_record = metadata.get_document(document_id)
        return doc_record.to_dict() if doc_record else {}
        
    except Exception as e:
        logger.error("Ingestion failed for %s: %s", upload.filename, e)
        # Cleanup
        if os.path.exists(stored_path):
            os.remove(stored_path)
        try:
            metadata.mark_document_failed(document_id, reason=str(e)[:50])
        except Exception:
            pass
        raise e


def list_documents() -> List[Dict[str, Any]]:
    """Return all document records."""
    records = metadata.list_documents()
    return [r.to_dict() for r in records]


def delete_document(document_id: str) -> bool:
    """
    Remove document from metadata DB, delete chunks from vector store,
    and remove the physical file.
    """
    doc = metadata.get_document(document_id)
    if not doc:
        return False
        
    logger.info("Deleting document %s", document_id)
    from app.rag import vector_store
    
    # 1. Remove from vector store
    try:
        vector_store.delete_document_from_store(document_id)
    except Exception as e:
        logger.error("Error deleting vectors for %s: %s", document_id, e)
        
    # 2. Delete physical file
    stored_path = settings.UPLOAD_DIR / doc.stored_filename
    if stored_path.exists():
        try:
            stored_path.unlink()
        except OSError as e:
            logger.error("Error deleting file %s: %s", stored_path, e)
            
    # 3. Remove from database
    return metadata.delete_document(document_id)


def search_documents(query: str, document_ids: Optional[List[str]] = None, top_k: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Search documents for chunks relevant to the query.
    Returns list of dicts with source metadata and score.
    """
    if not query or not query.strip():
        raise ValueError("Search query cannot be empty.")

    from app.rag import vector_store
        
    k = top_k or settings.RAG_TOP_K
    results = vector_store.search_store(query=query, top_k=k, document_ids=document_ids)
    
    formatted = []
    for doc, score in results:
        # doc is a LangChain Document
        meta = doc.metadata
        formatted.append({
            "document_id": meta.get("document_id"),
            "filename": meta.get("filename"),
            "chunk_id": meta.get("chunk_id"),
            "page": meta.get("page"),
            "content": doc.page_content,
            "distance": float(score)  # Lower is better (L2 distance)
        })
        
    return formatted

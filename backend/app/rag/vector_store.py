"""
Persistent vector store abstraction using FAISS.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Tuple

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from app.core.config import settings
from app.rag.embeddings import get_embedding_model

def get_vector_store() -> FAISS:
    """
    Load the persistent FAISS vector store or initialize a new empty one.
    """
    embeddings = get_embedding_model()
    index_path = str(settings.VECTOR_STORE_PATH)
    
    # We only load if index.faiss exists in the expected directory
    if os.path.exists(os.path.join(index_path, "index.faiss")):
        # allow_dangerous_deserialization is needed for loading the .pkl docstore.
        # It's safe here because we only load local files we created in VECTOR_STORE_PATH.
        return FAISS.load_local(
            folder_path=index_path, 
            embeddings=embeddings, 
            allow_dangerous_deserialization=True
        )
    else:
        # Create an empty FAISS index wrapper.
        # We need at least one dummy document or we can just initialize using the class.
        import faiss
        from langchain_community.docstore.in_memory import InMemoryDocstore
        
        # Dimensions for all-MiniLM-L6-v2 are 384
        index = faiss.IndexFlatL2(384)
        return FAISS(
            embedding_function=embeddings,
            index=index,
            docstore=InMemoryDocstore(),
            index_to_docstore_id={}
        )

def save_vector_store(vectorstore: FAISS) -> None:
    """
    Persist the FAISS vector store to disk.
    """
    vectorstore.save_local(str(settings.VECTOR_STORE_PATH))

def add_chunks_to_store(chunks: list[Document]) -> None:
    """
    Embed and add chunks to the persistent vector store.
    """
    if not chunks:
        return
        
    vs = get_vector_store()
    
    # Use the pre-assigned chunk_id as the docstore ID for reliable deletion mapping
    ids = [chunk.metadata["chunk_id"] for chunk in chunks]
    vs.add_documents(chunks, ids=ids)
    
    save_vector_store(vs)

def search_store(query: str, top_k: int = 5, document_ids: list[str] | None = None) -> list[Tuple[Document, float]]:
    """
    Search the vector store for relevant chunks.
    Optionally filter by document_ids.
    Returns list of (Document, score) where score is L2 distance (lower is better).
    """
    vs = get_vector_store()
    
    # If the index is completely empty, search will fail or return empty.
    if vs.index is None or vs.index.ntotal == 0:
        return []
        
    filter_dict = None
    if document_ids:
        # We need a filter function for FAISS
        # FAISS in LangChain supports filtering via callable or dict depending on implementation.
        # Current LangChain FAISS supports dictionary filtering by metadata keys.
        # However, filtering by a LIST of ids might require a custom callable.
        # We can fetch a bit more and filter manually, or use a custom callable filter.
        def filter_func(metadata: dict) -> bool:
            return metadata.get("document_id") in document_ids
        filter_dict = filter_func
        
    results = vs.similarity_search_with_score(query, k=top_k, filter=filter_dict)
    return results

def delete_document_from_store(document_id: str) -> None:
    """
    Delete all chunks belonging to a document_id from the vector store.
    """
    vs = get_vector_store()
    
    if vs.index is None or vs.index.ntotal == 0:
        return
        
    # Iterate through the docstore to find chunk IDs belonging to this document
    ids_to_delete = []
    for docstore_id, doc in vs.docstore._dict.items():
        if doc.metadata.get("document_id") == document_id:
            ids_to_delete.append(docstore_id)
            
    if ids_to_delete:
        vs.delete(ids_to_delete)
        save_vector_store(vs)

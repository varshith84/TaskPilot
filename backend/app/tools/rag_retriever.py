"""
RAG Retriever Tool.
Searches uploaded user documents semantically.
"""
import json
from typing import Optional, List
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig

from app.services import document_service

@tool
def search_uploaded_documents(query: str, document_ids: Optional[List[str]] = None, top_k: int = 5) -> str:
    """
    Use this tool when you need to answer questions using the user's uploaded documents.
    It performs semantic retrieval over the knowledge base.
    
    Args:
        query: The semantic search query.
        document_ids: Optional list of document IDs to restrict the search.
        top_k: Number of relevant chunks to retrieve.
    """
    try:
        results = document_service.search_documents(query, document_ids=document_ids, top_k=top_k)
        if not results:
            return "No relevant document evidence found."
            
        # Format results into a structured string for the LLM and metadata for the state
        formatted_content = []
        structured_sources = []
        
        for r in results:
            meta = f"Source: {r['filename']} (ID: {r['document_id']})"
            if r.get('page'):
                meta += f", Page {r['page']}"
            formatted_content.append(f"{meta}\nContent:\n{r['content']}")
            
            structured_sources.append({
                "type": "document",
                "document_id": r['document_id'],
                "filename": r['filename'],
                "page": r.get('page'),
                "chunk_id": r.get('chunk_id'),
                "snippet": r['content'][:200] + "..."
            })
            
        return json.dumps({
            "content": "\n\n---\n\n".join(formatted_content),
            "sources": structured_sources
        })
    except Exception as e:
        return json.dumps({
            "content": f"Error searching documents: {str(e)}",
            "sources": []
        })

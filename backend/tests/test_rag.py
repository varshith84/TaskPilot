"""
Tests for Phase 2: RAG Ingestion Pipeline.
"""

import os
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app
from app.db import metadata
from app.core.config import settings

client = TestClient(app)
# We will test using actual text files to avoid expensive PDF parsing in simple unit tests,
# but we will rely on the real Sentence Transformers model for the smoke test.

def setup_module():
    """Ensure data directories and DB are ready."""
    settings.ensure_data_directories()
    metadata.init_db()

def test_document_listing_empty():
    """Listing documents initially or when empty."""
    res = client.get("/api/documents")
    assert res.status_code == 200
    assert "documents" in res.json()
    assert isinstance(res.json()["documents"], list)

def test_document_upload_unsupported():
    """Test uploading an unsupported file type."""
    # Create a dummy python file
    files = {"file": ("test.py", b"print('hello')", "text/x-python")}
    res = client.post("/api/documents/upload", files=files)
    assert res.status_code == 400
    assert "Unsupported file extension" in res.json()["detail"]
def test_document_upload_and_search_txt():
    """End-to-end smoke test: upload text, search it, and delete it."""
    
    # 1. Create a dummy text file
    content = (
        "TaskPilot is a multi-tool AI agent. "
        "Inflow AI provides retrieval augmented generation. "
        "The system stores document chunks using vector embeddings. "
        "LangGraph will later decide which tools to invoke."
    ).encode("utf-8")
    
    files = {"file": ("smoke_test.txt", content, "text/plain")}
    
    # 2. Upload
    res = client.post("/api/documents/upload", files=files)
    assert res.status_code == 201
    
    data = res.json()
    assert "document_id" in data
    assert data["filename"] == "smoke_test.txt"
    assert data["status"] == "ready"
    assert data["chunks"] > 0
    
    doc_id = data["document_id"]
    
    # 3. List and verify it appears
    res_list = client.get("/api/documents")
    docs = res_list.json()["documents"]
    assert any(d["document_id"] == doc_id for d in docs)
    
    # 4. Search for specific content
    search_req = {
        "query": "What provides retrieval augmented generation?",
        "top_k": 3
    }
    res_search = client.post("/api/documents/search", json=search_req)
    assert res_search.status_code == 200
    search_data = res_search.json()
    assert "results" in search_data
    
    results = search_data["results"]
    assert len(results) > 0
    
    # Check if the right chunk was returned
    found = False
    for r in results:
        if "Inflow AI" in r["content"]:
            found = True
            break
    assert found is True, "Expected semantic content was not found in retrieval."
    
    # 5. Search with document_id filter
    search_req_filtered = {
        "query": "LangGraph",
        "document_ids": [doc_id]
    }
    res_filtered = client.post("/api/documents/search", json=search_req_filtered)
    assert res_filtered.status_code == 200
    assert any(r["document_id"] == doc_id for r in res_filtered.json()["results"])
    
    search_req_bad_filter = {
        "query": "LangGraph",
        "document_ids": ["non-existent-id"]
    }
    res_bad_filter = client.post("/api/documents/search", json=search_req_bad_filter)
    assert len(res_bad_filter.json()["results"]) == 0
    
    # 6. Delete document
    res_del = client.delete(f"/api/documents/{doc_id}")
    assert res_del.status_code == 204
    
    # 7. List and verify it's gone
    res_list2 = client.get("/api/documents")
    docs2 = res_list2.json()["documents"]
    assert not any(d["document_id"] == doc_id for d in docs2)
    
    # 8. Search again and verify it's not found
    res_search2 = client.post("/api/documents/search", json=search_req)
    # The result could be empty or contain other docs, but NOT this doc_id
    results2 = res_search2.json()["results"]
    assert not any(r["document_id"] == doc_id for r in results2)

def test_delete_non_existent():
    res = client.delete("/api/documents/invalid-id-here")
    assert res.status_code == 404

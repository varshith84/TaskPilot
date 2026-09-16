"""
Tests for the Chat API Endpoint (Phase 4).
"""

import pytest
import uuid
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.db import metadata
from app.core.config import settings
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

client = TestClient(app)

# Helper mock responses
def mock_direct_response(*args, **kwargs):
    return AIMessage(content="This is a direct answer.")

def mock_rag_response(*args, **kwargs):
    messages = args[0]
    if isinstance(messages[-1], ToolMessage):
        return AIMessage(content="The document says X.")
    return AIMessage(
        content="",
        tool_calls=[{"name": "search_uploaded_documents", "args": {"query": "test"}, "id": "t1"}]
    )

def mock_multi_response(*args, **kwargs):
    messages = args[0]
    if isinstance(messages[-1], ToolMessage):
        if messages[-1].name == "search_uploaded_documents":
            return AIMessage(
                content="",
                tool_calls=[{"name": "search_web", "args": {"query": "test"}, "id": "t2"}]
            )
        return AIMessage(content="Combined answer.")
    return AIMessage(
        content="",
        tool_calls=[{"name": "search_uploaded_documents", "args": {"query": "test"}, "id": "t1"}]
    )

@pytest.fixture(autouse=True)
def setup_db():
    settings.ensure_data_directories()
    metadata.init_db()

@patch("app.api.chat.run_agent")
def test_chat_empty_message(mock_run):
    res = client.post("/api/chat", json={"message": "   "})
    assert res.status_code == 400
    assert "Message cannot be empty" in res.json()["detail"]

@patch("app.agent.nodes.get_chat_model")
def test_direct_response_api(mock_get_chat_model):
    mock_llm = MagicMock()
    mock_llm.bind_tools.return_value.invoke.side_effect = mock_direct_response
    mock_get_chat_model.return_value = mock_llm
    
    res = client.post("/api/chat", json={"message": "Hello"})
    assert res.status_code == 200
    data = res.json()
    assert "session_id" in data
    assert data["answer"] == "This is a direct answer."
    assert data["tools_used"] == []
    assert data["tool_trace"] == []
    assert data["sources"] == []

@patch("app.agent.nodes.get_chat_model")
@patch("app.tools.rag_retriever.document_service.search_documents")
def test_rag_api(mock_search, mock_get_chat_model):
    mock_llm = MagicMock()
    mock_llm.bind_tools.return_value.invoke.side_effect = mock_rag_response
    mock_get_chat_model.return_value = mock_llm
    
    mock_search.return_value = [{
        "document_id": "test-id",
        "filename": "file.txt",
        "content": "rag content"
    }]
    
    res = client.post("/api/chat", json={"message": "Search"})
    assert res.status_code == 200
    data = res.json()
    assert "search_uploaded_documents" in data["tools_used"]
    assert len(data["tool_trace"]) == 1
    assert data["tool_trace"][0]["tool"] == "search_uploaded_documents"
    assert len(data["sources"]) == 1
    assert data["sources"][0]["type"] == "document"
    assert data["sources"][0]["filename"] == "file.txt"

@patch("app.agent.nodes.get_chat_model")
def test_missing_gemini_key_api(mock_get_chat_model):
    mock_get_chat_model.side_effect = ValueError("GEMINI_API_KEY is not configured.")
    
    res = client.post("/api/chat", json={"message": "Fail"})
    assert res.status_code == 503
    assert "TaskPilot AI is not configured" in res.json()["detail"]["message"]

@patch("app.agent.nodes.get_chat_model")
def test_invalid_document_id(mock_get_chat_model):
    res = client.post("/api/chat", json={"message": "Fail", "document_ids": ["does-not-exist"]})
    assert res.status_code == 400
    assert "does not exist" in res.json()["detail"]

@patch("app.agent.nodes.get_chat_model")
def test_conversation_memory_api(mock_get_chat_model):
    mock_llm = MagicMock()
    mock_llm.bind_tools.return_value.invoke.side_effect = mock_direct_response
    mock_get_chat_model.return_value = mock_llm
    
    session_id = str(uuid.uuid4())
    
    # Request 1
    res1 = client.post("/api/chat", json={"message": "Msg 1", "session_id": session_id})
    assert res1.status_code == 200
    
    # Request 2
    res2 = client.post("/api/chat", json={"message": "Msg 2", "session_id": session_id})
    assert res2.status_code == 200
    
    # Verify graph state directly to see 4 messages (2 human, 2 ai)
    from app.agent.graph import agent_graph
    state = agent_graph.get_state({"configurable": {"thread_id": session_id}})
    msgs = state.values["messages"]
    assert len(msgs) == 4
    assert msgs[0].content == "Msg 1"
    assert msgs[2].content == "Msg 2"

@patch("app.agent.nodes.get_chat_model")
def test_session_isolation(mock_get_chat_model):
    mock_llm = MagicMock()
    mock_llm.bind_tools.return_value.invoke.side_effect = mock_direct_response
    mock_get_chat_model.return_value = mock_llm
    
    sessA = str(uuid.uuid4())
    sessB = str(uuid.uuid4())
    
    client.post("/api/chat", json={"message": "A", "session_id": sessA})
    client.post("/api/chat", json={"message": "B", "session_id": sessB})
    
    from app.agent.graph import agent_graph
    msgsA = agent_graph.get_state({"configurable": {"thread_id": sessA}}).values["messages"]
    msgsB = agent_graph.get_state({"configurable": {"thread_id": sessB}}).values["messages"]
    
    assert len(msgsA) == 2
    assert msgsA[0].content == "A"
    assert len(msgsB) == 2
    assert msgsB[0].content == "B"

@patch("app.agent.nodes.get_chat_model")
@patch("app.tools.rag_retriever.document_service.search_documents")
@patch("app.tools.web_search.TavilySearchResults")
@patch("app.tools.web_search.settings.TAVILY_API_KEY", "fake")
def test_multi_tool_api(mock_tavily_cls, mock_search, mock_get_chat_model):
    mock_llm = MagicMock()
    mock_llm.bind_tools.return_value.invoke.side_effect = mock_multi_response
    mock_get_chat_model.return_value = mock_llm
    
    mock_search.return_value = [{"document_id": "test-id", "filename": "file.txt", "content": "rag"}]
    mock_tavily_cls.return_value.invoke.return_value = [{"url": "http://x", "content": "web"}]
    
    res = client.post("/api/chat", json={"message": "Multi"})
    assert res.status_code == 200
    data = res.json()
    assert "search_uploaded_documents" in data["tools_used"]
    assert "search_web" in data["tools_used"]
    
    assert len(data["sources"]) == 2
    types = {s["type"] for s in data["sources"]}
    assert types == {"document", "web"}

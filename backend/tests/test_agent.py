"""
Tests for Phase 3: LangGraph Agent, Routing, and Tools.
"""

import pytest
import uuid
from typing import List
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

# Mock the LLM before importing graph to avoid config errors
from unittest.mock import patch, MagicMock

# Mock settings
with patch("app.core.config.settings.GEMINI_API_KEY", "fake_key"):
    from app.agent.graph import agent_graph, run_agent
    from app.agent.state import AgentState

def mock_llm_direct_response(*args, **kwargs):
    """Mocks an LLM returning a direct string answer without tool calls."""
    return AIMessage(content="This is a direct response.")

def mock_llm_call_rag(*args, **kwargs):
    """Mocks an LLM calling the RAG tool."""
    messages = args[0]
    # If the last message is a ToolMessage, it means the tool already ran, so now we synthesize
    if isinstance(messages[-1], ToolMessage):
        return AIMessage(content="Final synthesized RAG answer.")
        
    return AIMessage(
        content="",
        tool_calls=[{
            "name": "search_uploaded_documents",
            "args": {"query": "test query"},
            "id": "call_rag_1"
        }]
    )

def mock_llm_call_summarizer(*args, **kwargs):
    """Mocks an LLM calling the Summarizer tool."""
    messages = args[0]
    if isinstance(messages[-1], ToolMessage):
        return AIMessage(content="Final summary synthesis.")
        
    return AIMessage(
        content="",
        tool_calls=[{
            "name": "summarize_document",
            "args": {"document_id": "doc123"},
            "id": "call_sum_1"
        }]
    )

def mock_llm_call_web(*args, **kwargs):
    """Mocks an LLM calling the Web tool."""
    messages = args[0]
    if isinstance(messages[-1], ToolMessage):
        return AIMessage(content="Final web answer.")
        
    return AIMessage(
        content="",
        tool_calls=[{
            "name": "search_web",
            "args": {"query": "latest news"},
            "id": "call_web_1"
        }]
    )

def mock_llm_multi_tool(*args, **kwargs):
    """Mocks an LLM calling multiple tools iteratively."""
    messages = args[0]
    if isinstance(messages[-1], ToolMessage):
        if messages[-1].name == "search_uploaded_documents":
            # After RAG, call Web Search
            return AIMessage(
                content="",
                tool_calls=[{
                    "name": "search_web",
                    "args": {"query": "latest news"},
                    "id": "call_web_2"
                }]
            )
        else:
            return AIMessage(content="Final combined answer.")
            
    # Initially call RAG
    return AIMessage(
        content="",
        tool_calls=[{
            "name": "search_uploaded_documents",
            "args": {"query": "test query"},
            "id": "call_rag_2"
        }]
    )

@patch("app.agent.nodes.get_chat_model")
def test_direct_response(mock_get_chat_model):
    """Test 2: Direct response without tool calls."""
    mock_llm = MagicMock()
    mock_llm.bind_tools.return_value.invoke.side_effect = mock_llm_direct_response
    mock_get_chat_model.return_value = mock_llm
    
    session_id = str(uuid.uuid4())
    result = run_agent("What is an embedding?", session_id)
    
    assert result["answer"] == "This is a direct response."
    assert len(result["tool_trace"]) == 0
    assert len(result["sources"]) == 0

@patch("app.agent.nodes.get_chat_model")
@patch("app.tools.rag_retriever.document_service.search_documents")
def test_rag_routing(mock_search_docs, mock_get_chat_model):
    """Test 3: RAG tool routing, execution, and source tracking."""
    mock_llm = MagicMock()
    mock_llm.bind_tools.return_value.invoke.side_effect = mock_llm_call_rag
    mock_get_chat_model.return_value = mock_llm
    
    mock_search_docs.return_value = [{
        "document_id": "test_id",
        "filename": "test.txt",
        "content": "This is semantic context."
    }]
    
    session_id = str(uuid.uuid4())
    result = run_agent("Search documents", session_id)
    
    assert result["answer"] == "Final synthesized RAG answer."
    assert len(result["tool_trace"]) == 1
    assert result["tool_trace"][0]["tool"] == "search_uploaded_documents"
    assert result["tool_trace"][0]["status"] == "completed"
    
    assert len(result["sources"]) == 1
    assert result["sources"][0]["type"] == "document"
    assert result["sources"][0]["filename"] == "test.txt"

@patch("app.agent.nodes.get_chat_model")
@patch("app.tools.web_search.TavilySearchResults")
@patch("app.tools.web_search.settings.TAVILY_API_KEY", "fake")
def test_web_routing(mock_tavily_cls, mock_get_chat_model):
    """Test 5: Web routing and mock tool result preservation."""
    mock_llm = MagicMock()
    mock_llm.bind_tools.return_value.invoke.side_effect = mock_llm_call_web
    mock_get_chat_model.return_value = mock_llm
    
    mock_tavily = MagicMock()
    mock_tavily.invoke.return_value = [{
        "url": "https://example.com",
        "content": "Web content here."
    }]
    mock_tavily_cls.return_value = mock_tavily
    
    session_id = str(uuid.uuid4())
    result = run_agent("Search web", session_id)
    
    assert result["answer"] == "Final web answer."
    assert len(result["tool_trace"]) == 1
    assert result["tool_trace"][0]["tool"] == "search_web"
    
    assert len(result["sources"]) == 1
    assert result["sources"][0]["type"] == "web"
    assert result["sources"][0]["url"] == "https://example.com"

@patch("app.agent.nodes.get_chat_model")
@patch("app.tools.rag_retriever.document_service.search_documents")
@patch("app.tools.web_search.TavilySearchResults")
@patch("app.tools.web_search.settings.TAVILY_API_KEY", "fake")
def test_multi_tool_flow(mock_tavily_cls, mock_search_docs, mock_get_chat_model):
    """Test 6 & 7: Multi-tool flow and combined source tracking."""
    mock_llm = MagicMock()
    mock_llm.bind_tools.return_value.invoke.side_effect = mock_llm_multi_tool
    mock_get_chat_model.return_value = mock_llm
    
    mock_search_docs.return_value = [{
        "document_id": "test_id",
        "filename": "test.txt",
        "content": "Doc content."
    }]
    
    mock_tavily = MagicMock()
    mock_tavily.invoke.return_value = [{
        "url": "https://example.com",
        "content": "Web content here."
    }]
    mock_tavily_cls.return_value = mock_tavily
    
    session_id = str(uuid.uuid4())
    result = run_agent("Do both", session_id)
    
    assert result["answer"] == "Final combined answer."
    assert len(result["tool_trace"]) == 2
    assert result["tool_trace"][0]["tool"] == "search_uploaded_documents"
    assert result["tool_trace"][1]["tool"] == "search_web"
    
    assert len(result["sources"]) == 2

@patch("app.agent.nodes.get_chat_model")
def test_conversation_continuity(mock_get_chat_model):
    """Test 12 & 13: Conversation memory and session isolation."""
    mock_llm = MagicMock()
    mock_llm.bind_tools.return_value.invoke.side_effect = mock_llm_direct_response
    mock_get_chat_model.return_value = mock_llm
    
    # Session A
    sess_a = str(uuid.uuid4())
    run_agent("Hello", sess_a)
    
    # Session B
    sess_b = str(uuid.uuid4())
    run_agent("Hi", sess_b)
    
    # Check graph state for sess_a
    config_a = {"configurable": {"thread_id": sess_a}}
    state_a = agent_graph.get_state(config_a)
    msgs_a = state_a.values["messages"]
    assert len(msgs_a) == 2  # Human, AI
    
    config_b = {"configurable": {"thread_id": sess_b}}
    state_b = agent_graph.get_state(config_b)
    msgs_b = state_b.values["messages"]
    assert len(msgs_b) == 2
    
    # Verify no overlap
    assert msgs_a[0].content == "Hello"
    assert msgs_b[0].content == "Hi"

def test_missing_gemini_key():
    """Test 14: Application behavior with missing Gemini API key."""
    from app.agent.llm import get_chat_model
    with patch("app.agent.llm.settings.GEMINI_API_KEY", ""):
        with pytest.raises(ValueError, match="GEMINI_API_KEY is not configured"):
            get_chat_model()

def test_real_rag_integration_with_agent(tmp_path):
    """Test 23: Real RAG integration using the actual vector store but mocked LLM."""
    from fastapi.testclient import TestClient
    from app.main import app
    from app.db import metadata
    from app.core.config import settings
    
    settings.ensure_data_directories()
    metadata.init_db()
    client = TestClient(app)
    
    # 1. Upload a real document
    content = "TaskPilot is coordinated by a LangGraph state machine. Inflow AI provides semantic retrieval."
    files = {"file": ("integration.txt", content.encode("utf-8"), "text/plain")}
    res = client.post("/api/documents/upload", files=files)
    assert res.status_code == 201
    
    # 2. Run agent with mocked LLM that calls RAG
    with patch("app.agent.nodes.get_chat_model") as mock_get_chat_model:
        mock_llm = MagicMock()
        mock_llm.bind_tools.return_value.invoke.side_effect = mock_llm_call_rag
        mock_get_chat_model.return_value = mock_llm
        
        session_id = str(uuid.uuid4())
        result = run_agent("What provides semantic retrieval?", session_id)
        
        assert result["answer"] == "Final synthesized RAG answer."
        assert len(result["tool_trace"]) == 1
        assert result["tool_trace"][0]["tool"] == "search_uploaded_documents"
        
        # Real source metadata should be extracted
        assert len(result["sources"]) > 0
        assert "Inflow AI" in result["sources"][0]["snippet"] or "TaskPilot" in result["sources"][0]["snippet"]


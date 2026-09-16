"""
Agent State representation.
"""
from typing import Annotated, TypedDict, List, Dict, Any, Optional
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    """
    State of the TaskPilot agent graph.
    """
    # Use add_messages to correctly append new messages to the existing list rather than overwriting.
    messages: Annotated[List[BaseMessage], add_messages]
    
    # Active document context provided by the user request.
    active_document_ids: List[str]
    
    # High-level tool trace to expose to the frontend.
    tool_trace: List[Dict[str, Any]]
    
    # Accumulated sources from RAG and Web Search.
    sources: List[Dict[str, Any]]

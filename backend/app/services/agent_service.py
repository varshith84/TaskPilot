"""
Agent Service.
Bridges the FastAPI HTTP layer with the internal LangGraph AI logic.
"""

from __future__ import annotations

import uuid
import logging
from typing import Dict, Any, List, Optional
from langchain_core.messages import HumanMessage, AIMessage

from app.agent.graph import agent_graph
from app.db import metadata
from app.core.config import settings

logger = logging.getLogger(__name__)

def run_agent(
    message: str,
    session_id: Optional[str] = None,
    document_ids: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Executes the TaskPilot AI agent for a user message.
    
    Args:
        message: The user's input string.
        session_id: Optional session UUID. Generated if missing.
        document_ids: Optional list of selected document UUIDs.
        
    Returns:
        Dict representing a valid ChatResponse.
    """
    # 1. Setup session ID
    if not session_id or not session_id.strip():
        session_id = str(uuid.uuid4())
        
    # 2. Validate Document IDs
    valid_doc_ids = []
    if document_ids:
        # Deduplicate
        unique_ids = list(set(document_ids))
        for doc_id in unique_ids:
            doc_record = metadata.get_document(doc_id)
            if not doc_record:
                raise ValueError(f"Document with ID {doc_id} does not exist.")
            valid_doc_ids.append(doc_id)
            
    # 3. Configure the graph invocation
    config = {
        "configurable": {"thread_id": session_id},
        "recursion_limit": 15
    }
    
    # We only send the NEW message. LangGraph checkpointing restores the rest of the conversation.
    input_state = {
        "messages": [HumanMessage(content=message)],
        "active_document_ids": valid_doc_ids,
        # We don't overwrite tool_trace or sources completely, but for a clean API response
        # representing *this turn*, it's better to clear out the accumulated ones 
        # from previous turns if we only want this turn's metadata. 
        # Wait, if we clear them in state, we lose them. The prompt says: 
        # "Return sources/tool trace". Let's extract them directly from the final state.
    }
    
    try:
        # 4. Invoke graph
        final_state = agent_graph.invoke(input_state, config=config)
        
        # 5. Extract Answer
        messages = final_state.get("messages", [])
        if not messages:
            raise RuntimeError("Agent returned no messages.")
            
        last_message = messages[-1]
        if not isinstance(last_message, AIMessage):
            # If the last message is a ToolMessage, the model stopped without synthesizing.
            # This is technically an incomplete execution, but we'll try to handle it.
            answer = "The agent stopped unexpectedly without providing a final response."
        else:
            # Safely extract text from AIMessage which can be str or list of dicts
            content = last_message.content
            if isinstance(content, list):
                # Extract text parts
                text_parts = []
                for part in content:
                    if isinstance(part, dict) and "text" in part:
                        text_parts.append(part["text"])
                    elif isinstance(part, str):
                        text_parts.append(part)
                answer = " ".join(text_parts)
            else:
                answer = str(content)
                
        # 6. Extract and Normalize Trace & Sources
        raw_trace = final_state.get("tool_trace", [])
        raw_sources = final_state.get("sources", [])
        
        # Tools used: unique and ordered
        tools_used = []
        for t in raw_trace:
            name = t.get("tool")
            if name and name not in tools_used:
                tools_used.append(name)
                
        # Deduplicate sources
        deduped_sources = []
        seen_docs = set()
        seen_urls = set()
        
        for src in raw_sources:
            if src.get("type") == "document":
                doc_id = src.get("document_id", "")
                filename = src.get("filename", "Unknown")
                page = src.get("page")
                chunk_id = src.get("chunk_id")
                
                key = (doc_id, chunk_id)
                if key not in seen_docs and doc_id:
                    seen_docs.add(key)
                    deduped_sources.append({
                        "type": "document",
                        "document_id": doc_id,
                        "filename": filename,
                        "page": page,
                        "chunk_id": chunk_id,
                        "snippet": src.get("snippet", "")
                    })
            elif src.get("type") == "web":
                url = src.get("url")
                title = src.get("title")
                
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    deduped_sources.append({
                        "type": "web",
                        "title": title,
                        "url": url,
                        "snippet": src.get("snippet", "")
                    })
                    
        return {
            "session_id": session_id,
            "answer": answer,
            "tools_used": tools_used,
            "tool_trace": raw_trace,
            "sources": deduped_sources
        }
        
    except ValueError as ve:
        # Re-raise ValueError for chat router to handle (like missing API key)
        raise ve
    except Exception as e:
        logger.exception("Agent execution failed")
        error_text = str(e).lower()
        if "recursion" in error_text or "iteration" in error_text:
            raise RuntimeError("TaskPilot could not complete the request within the allowed agent steps.")
        if any(marker in error_text for marker in ("429", "quota", "resource_exhausted")):
            raise RuntimeError("The AI provider quota is currently exhausted. Please try again later.")
        if any(marker in error_text for marker in ("google", "gemini", "provider", "api error")):
            raise RuntimeError("The AI provider could not complete this request.")
        raise RuntimeError(f"Agent execution failed: {str(e)}")

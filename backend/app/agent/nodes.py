"""
Agent and tool execution nodes.
"""
import json
from typing import Dict, Any, List
from langchain_core.messages import ToolMessage, AIMessage, SystemMessage

from app.agent.state import AgentState
from app.agent.llm import get_chat_model
from app.agent.prompts import TASKPILOT_SYSTEM_PROMPT

# Import tools
from app.tools.rag_retriever import search_uploaded_documents
from app.tools.document_summarizer import summarize_document
from app.tools.web_search import search_web

# Combine tools
TOOLS = [search_uploaded_documents, summarize_document, search_web]

# Map tool names to actual callables for execution
TOOL_MAP = {t.name: t for t in TOOLS}

def agent_node(state: AgentState) -> Dict[str, Any]:
    """
    Invokes the LLM to decide the next action.
    """
    llm = get_chat_model()
    llm_with_tools = llm.bind_tools(TOOLS)
    
    # Inject system prompt if it's the first message or simply prepend it conceptually.
    # It's cleaner to just prepend the SystemMessage to the current messages for the LLM call.
    messages = [SystemMessage(content=TASKPILOT_SYSTEM_PROMPT)] + state["messages"]
    
    # Actually call the model
    response = llm_with_tools.invoke(messages)
    
    return {"messages": [response]}

def tool_node(state: AgentState) -> Dict[str, Any]:
    """
    Executes the tools requested by the LLM in the last message.
    """
    messages = state["messages"]
    last_message = messages[-1]
    
    if not isinstance(last_message, AIMessage) or not last_message.tool_calls:
        return {"messages": []}
        
    tool_trace = state.get("tool_trace", [])
    sources = state.get("sources", [])
    active_document_ids = state.get("active_document_ids", [])
    
    new_messages = []
    
    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        tool_id = tool_call["id"]
        
        # Enforce active_document_ids if calling RAG tool and not explicitly passed by LLM
        if tool_name == "search_uploaded_documents":
            if active_document_ids and not tool_args.get("document_ids"):
                tool_args["document_ids"] = active_document_ids
                
        # Execute tool
        try:
            tool_instance = TOOL_MAP.get(tool_name)
            if not tool_instance:
                result_content = f"Error: Tool {tool_name} not found."
                trace_status = "error"
            else:
                raw_result = tool_instance.invoke(tool_args)
                trace_status = "completed"
                
                # Check if the tool returned our structured JSON payload
                try:
                    parsed = json.loads(raw_result)
                    if isinstance(parsed, dict) and "content" in parsed and "sources" in parsed:
                        result_content = parsed["content"]
                        # Directly append the structured sources
                        sources.extend(parsed["sources"])
                    else:
                        result_content = raw_result
                except (json.JSONDecodeError, TypeError):
                    result_content = raw_result
                            
        except Exception as e:
            result_content = f"Error executing {tool_name}: {str(e)}"
            trace_status = "error"
            
        new_messages.append(ToolMessage(
            tool_call_id=tool_id,
            name=tool_name,
            content=str(result_content)
        ))
        
        # Record trace
        tool_trace.append({
            "tool": tool_name,
            "status": trace_status,
            "description": f"Executed {tool_name}"
        })
        
    return {
        "messages": new_messages,
        "tool_trace": tool_trace,
        "sources": sources
    }

def should_continue(state: AgentState) -> str:
    """
    Conditional edge routing function.
    Returns "tools" if there are tool calls to execute, else "END".
    """
    messages = state["messages"]
    last_message = messages[-1]
    
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tools"
        
    return "END"

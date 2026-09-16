"""
StateGraph compilation and API helper.
"""
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from app.agent.state import AgentState
from app.agent.nodes import agent_node, tool_node, should_continue
from app.core.config import settings


class _LazyCompiledGraph:
    """Defer graph/checkpointer setup until the agent is actually used."""

    def __init__(self) -> None:
        self._graph = None

    def _get_graph(self):
        if self._graph is None:
            self._graph = build_graph()
        return self._graph

    def invoke(self, *args, **kwargs):
        return self._get_graph().invoke(*args, **kwargs)

    def get_state(self, *args, **kwargs):
        return self._get_graph().get_state(*args, **kwargs)

def build_graph():
    """
    Builds and compiles the TaskPilot LangGraph.
    """
    workflow = StateGraph(AgentState)
    
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tool_node)
    
    workflow.add_edge(START, "agent")
    
    # Conditional edge from agent to either tools or END based on LLM tool calls
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "END": END
        }
    )
    
    workflow.add_edge("tools", "agent")
    
    # In Phase 3, we'll use MemorySaver or SQLiteSaver.
    # Since we installed langgraph-checkpoint-sqlite, let's use it if configured,
    # otherwise fallback to MemorySaver for simplicity.
    # To keep it completely reliable across restarts during dev without complex migrations:
    # MemorySaver is often safer for immediate tests, but the prompt prefers SQLite.
    try:
        from langgraph.checkpoint.sqlite import SqliteSaver
        import sqlite3
        import os
        
        # Ensure checkpoint directory exists
        checkpoint_dir = settings.UPLOAD_DIR.parent / "checkpoints"
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        db_path = checkpoint_dir / "taskpilot_checkpoints.sqlite"
        
        # Connect to a simple local file for checkpoints
        conn = sqlite3.connect(str(db_path), check_same_thread=False)
        memory = SqliteSaver(conn)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning("Failed to initialize SqliteSaver, using MemorySaver instead. Error: %s", e)
        memory = MemorySaver()
        
    # Compile with loop protection (recursion_limit)
    return workflow.compile(checkpointer=memory)

# Keep the public graph handle stable while avoiding import-time database setup.
agent_graph = _LazyCompiledGraph()

def run_agent(message: str, session_id: str, document_ids: list[str] = None):
    """
    Convenience function to run the agent from API.
    """
    from langchain_core.messages import HumanMessage
    
    config = {
        "configurable": {"thread_id": session_id},
        "recursion_limit": 10
    }
    
    input_state = {
        "messages": [HumanMessage(content=message)],
        "active_document_ids": document_ids or []
    }
    
    try:
        # Stream the graph or invoke directly
        final_state = agent_graph.invoke(input_state, config=config)
        
        # Extract the final answer and structured state
        final_message = final_state["messages"][-1].content
        
        return {
            "answer": final_message,
            "tool_trace": final_state.get("tool_trace", []),
            "sources": final_state.get("sources", [])
        }
    except Exception as e:
        return {
            "error": str(e)
        }

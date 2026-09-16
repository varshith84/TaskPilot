# TaskPilot Interview Guide

## 30-second explanation

TaskPilot is a multi-tool AI agent built on top of the Inflow AI RAG foundation. Instead of always retrieving documents, a Gemini tool-enabled model decides whether to answer directly, search selected documents, summarize a whole document, or search the web. LangGraph stores the conversation and routes requested tool calls back to the agent until it produces a final answer. FastAPI exposes the service and React provides the Knowledge Base and chat UI.

## 2-minute technical explanation

The browser sends a message, session ID, and selected document IDs to `POST /api/chat`. `AgentService` validates the selected IDs, maps the session ID to a LangGraph thread, and invokes the compiled `StateGraph`. The agent node calls Gemini with the three tools bound. If the model returns tool calls, the conditional edge enters the tool node; each requested tool executes, appends an observable trace, and contributes structured sources to `AgentState`. Control then returns to the agent node. When the model returns an answer without tool calls, the graph reaches `END`. The service normalizes the answer, preserves first-seen source ordering, deduplicates document sources by `(document_id, chunk_id)` and web sources by URL, and returns a `ChatResponse`.

Document ingestion saves a UUID-prefixed safe filename, parses PDF/DOCX/TXT/MD content, chunks it with `RecursiveCharacterTextSplitter`, embeds chunks with `all-MiniLM-L6-v2`, and persists them in FAISS. SQLite stores document metadata and the LangGraph SQLite checkpointer stores conversation state. The frontend renders Markdown safely with `react-markdown`, shows only generic loading text before the response, and renders tools and sources only from the response payload.

## Explain LangGraph

LangGraph is useful here because the workflow is stateful and cyclic: an agent can call one tool, inspect the result, call another tool, and then finish. A simple linear chain does not model that conditional loop as clearly. The graph has an agent node, a tool node, a conditional `tool_calls` edge, a tool-to-agent loop, and an `END` path.

## Why not a plain LangChain chain?

A chain is a good fit for fixed steps. TaskPilot needs model-selected tools, optional repeated tool calls, per-session memory, request-scoped document IDs, and an explicit stop condition. `StateGraph` makes those transitions and state boundaries visible and testable.

## Explain AgentState

`AgentState` contains:

- `messages`, merged with LangGraph's `add_messages` reducer
- `active_document_ids`, supplied for the current request
- `tool_trace`, observable tool execution events
- `sources`, structured document and web evidence

The model's hidden reasoning is never exposed as state or returned to the browser.

## Explain the RAG pipeline

Upload -> loader -> normalized LangChain documents -> recursive chunks -> local Sentence Transformer embeddings -> persistent FAISS -> filtered semantic retrieval. Each chunk carries document ID, filename, optional page, and chunk ID metadata.

## RAG Retriever versus Summarizer

The RAG Retriever finds the most relevant chunks for a focused question. The Summarizer loads and chunks the whole selected document, summarizes each chunk, and reduces the partial summaries into a final summary. It is useful for global understanding rather than one fact lookup.

## Why FAISS and Sentence Transformers?

FAISS is a practical local vector index for a small single-user deployment. Sentence Transformers provides local semantic embeddings without sending document text to an embedding API, which keeps the ingestion path simple and controllable.

## How multi-tool execution works

The model can return multiple tool calls in one turn or request another tool after receiving a prior tool result. The tool node executes the requested calls, appends structured results, and routes back to the agent. There is no keyword-based routing.

## How conversation memory works

The frontend stores only the current session ID under `taskpilot_session_id`. The backend maps it to LangGraph's `thread_id`; the SQLite checkpointer restores prior messages for that thread. New Chat clears the frontend session ID, causing a new thread on the next message. Document IDs are supplied on every request, so selection scope is request-scoped rather than inherited from an old turn.

## How citations work

Tools return a structured JSON envelope containing human-readable tool content and source objects. The tool node appends those objects directly to `AgentState.sources`. `AgentService` validates, deduplicates, and returns them. The frontend never invents citations or parses model prose for source metadata.

## Prompt-injection boundary

The summarizer prompt explicitly tells the model to treat document text as untrusted content and not follow instructions found inside it. Tool selection remains controlled by the model's bound tool schema, while source metadata comes from application-created objects rather than uploaded text.

## Real implementation challenges

- Keeping the Python 3.12 environment stable for the installed ML stack.
- Avoiding Sentence Transformer, FAISS, Gemini, Tavily, and checkpointer work during ordinary API imports.
- Preserving structured source metadata across tools, graph state, API schemas, and React.
- Enforcing selected document scope on each request while using persistent conversation state.
- Removing a tracked virtual environment without deleting the local environment.

## Likely interviewer questions

**Why is tool selection trustworthy?**  The graph branches on `AIMessage.tool_calls`, not on query keywords.

**What happens when Gemini is missing?**  The chat endpoint returns a clean 503 configuration response; health, docs, and document management still work.

**How are sources deduplicated?**  Documents use `(document_id, chunk_id)` and web sources use URL, preserving first-seen order.

**Can the agent use more than one tool?**  Yes. Tool results loop back to the agent, which can request additional tools before `END`.

**How are document IDs validated?**  `AgentService` checks every submitted ID against SQLite before invoking the graph.

**How does deletion work?**  The service removes FAISS chunks, the uploaded file, and the SQLite metadata row.

**Why lazy initialization?**  It keeps imports and test collection fast and prevents credentials or model downloads from being required to boot the API.

**What does the frontend show while waiting?**  Only `TaskPilot is working...`; specific tools appear only after real backend trace data arrives.

**How is model output rendered?**  `react-markdown` and `remark-gfm` render Markdown without `dangerouslySetInnerHTML`.

**What is the deployment boundary?**  This is a local/small deployment with SQLite, local FAISS, and no authentication or multi-user workspace isolation.

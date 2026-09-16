# TaskPilot Demo Guide

## Startup

Backend (Windows PowerShell):

```powershell
cd backend
.\.venv_new\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

Frontend:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

## Scenario 1 - Direct reasoning

Prompt: `Explain vector embeddings simply in one sentence.`

Expected: a direct answer with no tool badge when Gemini is configured.

## Scenario 2 - Document retrieval

Upload a TXT, Markdown, PDF, or DOCX file and select it in Knowledge Base.

Prompt: `According to my selected document, what are the main findings?`

Expected: the LLM requests `search_uploaded_documents`; the response shows the RAG Retriever activity and document source cards.

## Scenario 3 - Document summary

Prompt: `Give me a concise summary of the selected document.`

Expected: the LLM requests `summarize_document`; source metadata remains attached to the response.

## Scenario 4 - Web search

Prompt: `Search the web for recent LangGraph developments.`

Expected: the LLM requests `search_web`; web source cards preserve real URLs and open in a new tab.

## Scenario 5 - Multi-tool comparison

Prompt: `Compare the approach in my selected document with current approaches online.`

Expected: the graph may call the RAG Retriever, return to the agent, call Web Search, and then produce one answer with both source types.

## What to point out

- Knowledge Base selection scopes document retrieval for the current request.
- Tool badges and expanded traces come from backend `tools_used` and `tool_trace`.
- Source cards come from structured backend source objects.
- New Chat clears the visible conversation but keeps the Knowledge Base.
- Without `GEMINI_API_KEY`, the UI remains usable and shows a friendly configuration message.

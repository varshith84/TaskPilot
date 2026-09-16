import { FileSearch, FileText, Globe, GitCompare } from 'lucide-react'

interface EmptyStateProps {
  onSuggest: (prompt: string) => void
  hasDocuments: boolean
}

export function EmptyState({ onSuggest, hasDocuments }: EmptyStateProps) {
  return (
    <div className="empty-state">
      <h2>How can TaskPilot help?</h2>
      {!hasDocuments ? (
        <p className="empty-subtitle">Upload a document to start asking questions about your own knowledge base.</p>
      ) : (
        <p className="empty-subtitle">Ask questions across your documents, summarize files, or search the web.</p>
      )}

      <div className="suggestions-grid">
        <button className="suggestion-card" onClick={() => onSuggest("What are the key findings in my uploaded documents?")}>
          <FileSearch size={20} className="icon" />
          <div className="content">
            <h4>Ask about my documents</h4>
            <p>What are the key findings in my uploaded documents?</p>
          </div>
        </button>
        <button className="suggestion-card" onClick={() => onSuggest("Give me a detailed summary of the selected document.")}>
          <FileText size={20} className="icon" />
          <div className="content">
            <h4>Summarize a file</h4>
            <p>Give me a detailed summary of the selected document.</p>
          </div>
        </button>
        <button className="suggestion-card" onClick={() => onSuggest("Search the web for the latest developments in LangGraph.")}>
          <Globe size={20} className="icon" />
          <div className="content">
            <h4>Search the web</h4>
            <p>Search the web for the latest developments in LangGraph.</p>
          </div>
        </button>
        <button className="suggestion-card" onClick={() => onSuggest("Compare the approach in my document with recent information online.")}>
          <GitCompare size={20} className="icon" />
          <div className="content">
            <h4>Compare sources</h4>
            <p>Compare the approach in my document with recent information online.</p>
          </div>
        </button>
      </div>
    </div>
  )
}

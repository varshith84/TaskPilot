import { Wrench, CheckCircle, AlertCircle } from 'lucide-react'
import type { ToolTraceItem } from '../../types/api'
import { useState } from 'react'

const TOOL_LABELS: Record<string, string> = {
  'search_uploaded_documents': 'RAG Retriever',
  'summarize_document': 'Document Summarizer',
  'search_web': 'Web Search'
}

interface ToolBadgeProps {
  toolsUsed: string[]
  toolTrace: ToolTraceItem[]
}

export function ToolBadge({ toolsUsed, toolTrace }: ToolBadgeProps) {
  const [expanded, setExpanded] = useState(false)

  if (!toolsUsed.length && !toolTrace.length) return null

  const displayNames = toolsUsed.map(t => TOOL_LABELS[t] || t).join(' + ')

  return (
    <div className="tool-activity">
      <button 
        className="tool-summary-btn" 
        onClick={() => setExpanded(!expanded)}
        aria-expanded={expanded}
      >
        <Wrench size={14} className="icon" />
        <span>Used {displayNames || 'Tools'}</span>
      </button>

      {expanded && toolTrace.length > 0 && (
        <ul className="tool-details-list">
          {toolTrace.map((trace, idx) => (
            <li key={idx} className={`tool-trace-item ${trace.status}`}>
              {trace.status === 'completed' ? (
                <CheckCircle size={14} className="trace-icon success" />
              ) : (
                <AlertCircle size={14} className="trace-icon error" />
              )}
              <span className="trace-desc">{trace.description}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

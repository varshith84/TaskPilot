import { FileText, Globe } from 'lucide-react'
import type { Source } from '../../types/api'

interface SourcesListProps {
  sources: Source[]
}

export function SourcesList({ sources }: SourcesListProps) {
  if (!sources || sources.length === 0) return null

  return (
    <div className="sources-container">
      <div className="sources-header">Sources</div>
      <div className="sources-grid">
        {sources.map((source, index) => (
          <div key={index} className="source-card">
            {source.type === 'document' ? (
              <>
                <div className="source-card-header">
                  <FileText size={14} />
                  <span className="source-title" title={source.filename}>{source.filename}</span>
                </div>
                {source.page && <div className="source-meta">Page {source.page}</div>}
              </>
            ) : (
              <>
                <div className="source-card-header">
                  <Globe size={14} />
                  <a href={source.url} target="_blank" rel="noopener noreferrer" className="source-title" title={source.title || source.url}>
                    {source.title || new URL(source.url).hostname}
                  </a>
                </div>
                <div className="source-meta">{new URL(source.url).hostname}</div>
              </>
            )}
            {source.snippet && (
              <div className="source-snippet">{source.snippet}</div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

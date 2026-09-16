import type { DocumentResponse } from '../../types/api'
import { DocumentItem } from './DocumentItem'
import { Loader2 } from 'lucide-react'

interface DocumentListProps {
  documents: DocumentResponse[]
  selectedIds: string[]
  isLoading: boolean
  onToggle: (id: string) => void
  onDelete: (id: string) => void
}

export function DocumentList({ documents, selectedIds, isLoading, onToggle, onDelete }: DocumentListProps) {
  if (isLoading && documents.length === 0) {
    return (
      <div className="doc-list-empty">
        <Loader2 className="spinner" size={20} />
      </div>
    )
  }

  if (documents.length === 0) {
    return (
      <div className="doc-list-empty">
        <p>No documents yet.</p>
        <small>Upload PDF, DOCX, TXT or Markdown files.</small>
      </div>
    )
  }

  return (
    <div className="document-list">
      {documents.map(doc => (
        <DocumentItem 
          key={doc.document_id}
          doc={doc}
          isSelected={selectedIds.includes(doc.document_id)}
          onToggle={onToggle}
          onDelete={onDelete}
        />
      ))}
    </div>
  )
}

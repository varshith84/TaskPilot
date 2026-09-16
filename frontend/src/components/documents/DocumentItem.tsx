import { FileText, Trash2, CheckCircle2 } from 'lucide-react'
import type { DocumentResponse } from '../../types/api'

interface DocumentItemProps {
  doc: DocumentResponse
  isSelected: boolean
  onToggle: (id: string) => void
  onDelete: (id: string) => void
}

export function DocumentItem({ doc, isSelected, onToggle, onDelete }: DocumentItemProps) {
  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation()
    if (confirm(`Delete ${doc.filename}?`)) {
      onDelete(doc.document_id)
    }
  }

  return (
    <div className={`document-item ${isSelected ? 'selected' : ''}`} onClick={() => onToggle(doc.document_id)}>
      <div className="doc-icon-wrapper">
        <FileText size={16} />
        {isSelected && <CheckCircle2 size={12} className="check-icon" />}
      </div>
      <div className="doc-info">
        <span className="doc-filename" title={doc.filename}>{doc.filename}</span>
        <span className="doc-meta">
          {(doc.file_size / 1024).toFixed(1)} KB • {doc.status}
        </span>
      </div>
      <button 
        className="doc-delete-btn" 
        onClick={handleDelete}
        title="Delete document"
        aria-label="Delete document"
      >
        <Trash2 size={14} />
      </button>
    </div>
  )
}

import { DocumentUploader } from '../documents/DocumentUploader'
import { DocumentList } from '../documents/DocumentList'
import type { DocumentResponse } from '../../types/api'

interface SidebarProps {
  documents: DocumentResponse[]
  selectedIds: string[]
  isLoading: boolean
  error: string | null
  onUpload: (file: File) => Promise<void>
  onToggleSelection: (id: string) => void
  onDeleteDocument: (id: string) => void
}

export function Sidebar({ documents, selectedIds, isLoading, error, onUpload, onToggleSelection, onDeleteDocument }: SidebarProps) {
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <h2>Knowledge Base</h2>
        <p>Documents TaskPilot can reason over</p>
      </div>
      
      <div className="sidebar-section">
        <DocumentUploader onUpload={onUpload} />
        {error && <p className="sidebar-error" role="alert">{error}</p>}
      </div>

      <div className="sidebar-section sidebar-list-container">
        <div className="list-header">
          <h3>Uploaded Files</h3>
          <span className="badge">{documents.length}</span>
        </div>
        <DocumentList 
          documents={documents} 
          selectedIds={selectedIds}
          isLoading={isLoading}
          onToggle={onToggleSelection}
          onDelete={onDeleteDocument}
        />
      </div>
    </aside>
  )
}

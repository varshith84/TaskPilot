import { Compass } from 'lucide-react'
import { StatusBadge } from '../StatusBadge'
import type { HealthStatus } from '../../types/api'

interface HeaderProps {
  healthStatus: HealthStatus | 'loading' | 'error'
  onNewChat: () => void
}

export function Header({ healthStatus, onNewChat }: HeaderProps) {
  return (
    <header className="app-header">
      <div className="brand">
        <div className="logo">
          <Compass size={24} />
        </div>
        <div>
          <h1>TaskPilot</h1>
          <span className="subtitle">Documents • Summaries • Web</span>
        </div>
      </div>
      
      <div className="header-actions">
        <StatusBadge status={healthStatus} />
        <button className="new-chat-btn" onClick={onNewChat}>
          New Chat
        </button>
      </div>
    </header>
  )
}

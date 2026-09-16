import { useEffect, useState } from 'react'
import { getHealth } from './services/api'
import type { HealthStatus } from './types/api'
import { Header } from './components/layout/Header'
import { Sidebar } from './components/layout/Sidebar'
import { ChatWindow } from './components/chat/ChatWindow'
import { useDocuments } from './hooks/useDocuments'
import { useChat } from './hooks/useChat'
import './App.css'

export default function App() {
  const [healthStatus, setHealthStatus] = useState<HealthStatus | 'loading' | 'error'>('loading')
  
  const { 
    documents, 
    selectedIds, 
    isLoading: docsLoading, 
    error: docsError,
    upload, 
    remove, 
    toggleSelection 
  } = useDocuments()
  
  const { 
    messages, 
    isLoading: chatLoading, 
    sendMessage, 
    resetChat 
  } = useChat()

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const data = await getHealth()
        setHealthStatus(data.status)
      } catch {
        setHealthStatus('error')
      }
    }
    
    checkHealth()
    const interval = setInterval(checkHealth, 30_000)
    return () => clearInterval(interval)
  }, [])

  const handleSendMessage = (msg: string) => {
    sendMessage(msg, selectedIds)
  }

  return (
    <div className="app-container">
      <Sidebar 
        documents={documents}
        selectedIds={selectedIds}
        isLoading={docsLoading}
        error={docsError}
        onUpload={async (file) => {
          await upload(file)
        }}
        onToggleSelection={toggleSelection}
        onDeleteDocument={remove}
      />
      <div className="main-content">
        <Header 
          healthStatus={healthStatus}
          onNewChat={resetChat}
        />
        <ChatWindow 
          messages={messages}
          isLoading={chatLoading}
          hasDocuments={documents.length > 0}
          onSendMessage={handleSendMessage}
        />
      </div>
    </div>
  )
}

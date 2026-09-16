import { useState, useCallback, useEffect } from 'react'
import { sendChat } from '../services/api'
import type { ToolTraceItem, Source } from '../types/api'

export interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  toolsUsed?: string[]
  toolTrace?: ToolTraceItem[]
  sources?: Source[]
}

const SESSION_KEY = 'taskpilot_session_id'

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [sessionId, setSessionId] = useState<string | null>(() => localStorage.getItem(SESSION_KEY))
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (sessionId) {
      localStorage.setItem(SESSION_KEY, sessionId)
    } else {
      localStorage.removeItem(SESSION_KEY)
    }
  }, [sessionId])

  const sendMessage = useCallback(async (content: string, documentIds: string[]) => {
    const userMsgId = crypto.randomUUID()
    setMessages(prev => [...prev, { id: userMsgId, role: 'user', content }])
    setIsLoading(true)
    setError(null)

    try {
      const response = await sendChat({
        message: content,
        session_id: sessionId,
        document_ids: documentIds.length > 0 ? documentIds : undefined
      })
      
      setSessionId(response.session_id)
      
      setMessages(prev => [...prev, {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: response.answer,
        toolsUsed: response.tools_used,
        toolTrace: response.tool_trace,
        sources: response.sources
      }])
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Unknown error'
      setError(msg)
      setMessages(prev => [...prev, {
        id: crypto.randomUUID(),
        role: 'system',
        content: `Error: ${msg}`
      }])
    } finally {
      setIsLoading(false)
    }
  }, [sessionId])

  const resetChat = useCallback(() => {
    setMessages([])
    setSessionId(null)
    setError(null)
  }, [])

  return {
    messages,
    isLoading,
    error,
    sendMessage,
    resetChat
  }
}

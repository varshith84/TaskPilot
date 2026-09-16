import { useEffect, useRef } from 'react'
import type { Message } from '../../hooks/useChat'
import { ChatMessage } from './ChatMessage'
import { ChatInput } from './ChatInput'
import { EmptyState } from './EmptyState'
import { Loader2 } from 'lucide-react'

interface ChatWindowProps {
  messages: Message[]
  isLoading: boolean
  hasDocuments: boolean
  onSendMessage: (msg: string) => void
}

export function ChatWindow({ messages, isLoading, hasDocuments, onSendMessage }: ChatWindowProps) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  return (
    <main className="chat-window">
      <div className="chat-history">
        {messages.length === 0 ? (
          <EmptyState onSuggest={onSendMessage} hasDocuments={hasDocuments} />
        ) : (
          messages.map(msg => <ChatMessage key={msg.id} message={msg} />)
        )}
        {isLoading && (
          <div className="message-wrapper assistant loading">
            <div className="message-bubble">
              <Loader2 className="spinner" size={20} />
              <span>TaskPilot is working...</span>
            </div>
          </div>
        )}
        <div ref={bottomRef} className="scroll-anchor" />
      </div>
      
      <div className="chat-input-area">
        <ChatInput onSend={onSendMessage} isLoading={isLoading} />
      </div>
    </main>
  )
}

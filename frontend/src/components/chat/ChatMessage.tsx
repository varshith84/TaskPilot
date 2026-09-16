import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import type { Message } from '../../hooks/useChat'
import { ToolBadge } from '../agent/ToolBadge'
import { SourcesList } from '../sources/SourcesList'

interface ChatMessageProps {
  message: Message
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user'
  const isSystem = message.role === 'system'

  if (isSystem) {
    return (
      <div className="message system-message">
        <div className="message-content">{message.content}</div>
      </div>
    )
  }

  return (
    <div className={`message-wrapper ${isUser ? 'user' : 'assistant'}`}>
      <div className="message-bubble">
        {!isUser && message.toolsUsed && message.toolsUsed.length > 0 && (
          <ToolBadge toolsUsed={message.toolsUsed} toolTrace={message.toolTrace || []} />
        )}
        
        <div className="message-content markdown-body">
          {isUser ? (
            <p>{message.content}</p>
          ) : (
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {message.content}
            </ReactMarkdown>
          )}
        </div>

        {!isUser && message.sources && message.sources.length > 0 && (
          <SourcesList sources={message.sources} />
        )}
      </div>
    </div>
  )
}

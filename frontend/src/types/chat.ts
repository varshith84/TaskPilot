export interface DocumentResponse {
  document_id: string
  filename: string
  uploaded_at: string
  file_size: number
  status: string
  error_message?: string
}

export interface ChatRequest {
  message: string
  session_id?: string | null
  document_ids?: string[] | null
}

export interface ToolTraceItem {
  tool: string
  status: 'completed' | 'error'
  description: string
}

export interface DocumentSource {
  type: 'document'
  document_id: string
  filename: string
  page?: number | null
  chunk_id?: string | null
  snippet: string
}

export interface WebSource {
  type: 'web'
  title?: string | null
  url: string
  snippet: string
}

export type Source = DocumentSource | WebSource

export interface ChatResponse {
  session_id: string
  answer: string
  tools_used: string[]
  tool_trace: ToolTraceItem[]
  sources: Source[]
}

import { useState, useEffect, useCallback } from 'react'
import { getDocuments, uploadDocument, deleteDocument } from '../services/api'
import type { DocumentResponse } from '../types/api'

export function useDocuments() {
  const [documents, setDocuments] = useState<DocumentResponse[]>([])
  const [selectedIds, setSelectedIds] = useState<string[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchDocuments = useCallback(async () => {
    try {
      setIsLoading(true)
      setError(null)
      const data = await getDocuments()
      setDocuments(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch documents')
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchDocuments()
  }, [fetchDocuments])

  const upload = async (file: File) => {
    try {
      setError(null)
      const doc = await uploadDocument(file)
      setDocuments(prev => [...prev, doc])
      setSelectedIds(prev => [...prev, doc.document_id])
      return doc
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to upload document'
      setError(msg)
      throw new Error(msg)
    }
  }

  const remove = async (id: string) => {
    try {
      setError(null)
      await deleteDocument(id)
      setDocuments(prev => prev.filter(d => d.document_id !== id))
      setSelectedIds(prev => prev.filter(selectedId => selectedId !== id))
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to delete document'
      setError(msg)
      throw new Error(msg)
    }
  }

  const toggleSelection = (id: string) => {
    setSelectedIds(prev =>
      prev.includes(id) ? prev.filter(sid => sid !== id) : [...prev, id]
    )
  }

  return {
    documents,
    selectedIds,
    isLoading,
    error,
    upload,
    remove,
    toggleSelection,
    refresh: fetchDocuments
  }
}

/**
 * Centralized API service for TaskPilot.
 *
 * All backend HTTP communication is routed through this module.
 * The base URL is read from the VITE_API_BASE_URL environment variable
 * so that it never needs to be hard-coded in components.
 *
 * During local development the Vite proxy handles /api/* → backend,
 * so we default to an empty string (same-origin) when the var is unset.
 */

import type { HealthResponse } from '../types/api'

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

/**
 * Base URL for all API requests.
 *
 * In development the Vite dev-server proxy forwards /api/* to FastAPI, so
 * relative paths work without setting VITE_API_BASE_URL.
 * In production builds set VITE_API_BASE_URL to the deployed API origin.
 */
const API_BASE_URL: string = import.meta.env.VITE_API_BASE_URL ?? ''

// ---------------------------------------------------------------------------
// Core fetch helper
// ---------------------------------------------------------------------------

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'
  body?: unknown
  signal?: AbortSignal
}

async function apiFetch<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const { method = 'GET', body, signal } = options

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
    signal,
  })

  if (!response.ok) {
    // Attempt to extract the FastAPI error envelope.
    let errorDetail = `HTTP ${response.status} ${response.statusText}`
    try {
      const errorBody = await response.json()
      const detail = errorBody?.detail
      errorDetail = typeof detail === 'string'
        ? detail
        : detail?.message || detail?.detail || errorDetail
    } catch {
      // Ignore JSON parse errors on error responses.
    }
    throw new Error(errorDetail)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return response.json() as Promise<T>
}

// ---------------------------------------------------------------------------
// Health API
// ---------------------------------------------------------------------------

/**
 * Fetch the current health status of the TaskPilot backend.
 *
 * @returns {Promise<HealthResponse>} Structured health response.
 */
export async function getHealth(signal?: AbortSignal): Promise<HealthResponse> {
  return apiFetch<HealthResponse>('/api/health', { signal })
}

// ---------------------------------------------------------------------------
// Document API
// ---------------------------------------------------------------------------

export async function getDocuments(signal?: AbortSignal): Promise<import('../types/api').DocumentResponse[]> {
  const response = await apiFetch<{ documents: import('../types/api').DocumentResponse[] }>('/api/documents', { signal })
  return response.documents
}

export async function uploadDocument(file: File, signal?: AbortSignal): Promise<import('../types/api').DocumentResponse> {
  const formData = new FormData()
  formData.append('file', file)
  
  const response = await fetch(`${API_BASE_URL}/api/documents/upload`, {
    method: 'POST',
    body: formData,
    signal,
  })

  if (!response.ok) {
    let errorDetail = `HTTP ${response.status} ${response.statusText}`
    try {
      const errorBody = await response.json()
      const detail = errorBody?.detail
      errorDetail = typeof detail === 'string'
        ? detail
        : detail?.message || detail?.detail || errorDetail
    } catch {
      // Ignore JSON parse errors
    }
    throw new Error(errorDetail)
  }

  return response.json()
}

export async function deleteDocument(documentId: string, signal?: AbortSignal): Promise<{status: string, message: string}> {
  return apiFetch<{status: string, message: string}>(`/api/documents/${documentId}`, { method: 'DELETE', signal })
}

// ---------------------------------------------------------------------------
// Chat API
// ---------------------------------------------------------------------------

export async function sendChat(request: import('../types/api').ChatRequest, signal?: AbortSignal): Promise<import('../types/api').ChatResponse> {
  return apiFetch<import('../types/api').ChatResponse>('/api/chat', {
    method: 'POST',
    body: request,
    signal,
  })
}

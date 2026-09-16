/**
 * Shared TypeScript types for the TaskPilot frontend.
 *
 * These mirror the Pydantic schemas defined in backend/app/models/schemas.py.
 * Keep them in sync as new schemas are added in later phases.
 */

// ---------------------------------------------------------------------------
// Health endpoint
// ---------------------------------------------------------------------------

export type HealthStatus = 'healthy' | 'degraded' | 'unhealthy'

export interface HealthResponse {
  status: HealthStatus
  service: string
  version: string
  environment: string
  timestamp: string // ISO-8601 UTC string
}

// ---------------------------------------------------------------------------
// Generic API error
// ---------------------------------------------------------------------------

export interface ApiError {
  detail: string
  code?: string | null
  meta?: Record<string, unknown> | null
}

export * from './chat'

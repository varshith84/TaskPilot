/**
 * StatusBadge — displays a coloured pill indicating the backend health status.
 */

import type { HealthStatus } from '../types/api'
import styles from './StatusBadge.module.css'

interface StatusBadgeProps {
  status: HealthStatus | 'loading' | 'error'
}

const LABELS: Record<StatusBadgeProps['status'], string> = {
  loading: 'Checking…',
  healthy: 'Healthy',
  degraded: 'Degraded',
  unhealthy: 'Unhealthy',
  error: 'Unreachable',
}

export function StatusBadge({ status }: StatusBadgeProps) {
  return (
    <span className={`${styles.badge} ${styles[status]}`} role="status" aria-label={`Backend status: ${LABELS[status]}`}>
      <span className={styles.dot} aria-hidden="true" />
      {LABELS[status]}
    </span>
  )
}

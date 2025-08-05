export interface Job {
  jobId: string
  name: string
  status: 'success' | 'warning' | 'failed' | 'running' | 'unknown' | 'no-data'
  scheduleStatus: 'on-time' | 'overdue' | 'unknown'
  lastBackup: string
  lastBackupRelative?: string
  lastSuccessfulBackup?: string
  lastSuccessfulBackupRelative?: string
  tags?: string[]
  stats: JobStats
}

export interface JobStats {
  archiveCount: number
  fullSize: string
  compressedSize: string
  deduplicatedSize: string
  compressionRatio: string
}

export interface Archive {
  name: string
  createdAt: string
  originalSize: string
  compressedSize: string
  deduplicatedSize: string
  tags?: string[]
}

export interface BackupEvent {
  id: string
  type: 'start' | 'stop' | 'success' | 'failed' | 'log' | 'info'
  timestamp: string
  timestampRelative?: string
  message: string
  hasInfo: boolean
  extra?: Record<string, any>
}

export interface EventInfoDetails {
  lines: string[]
  totalLines: number
  hasMore: boolean
  nextOffset?: number
}

export interface BackupRun {
  id: string
  status: 'success' | 'warning' | 'failed' | 'running'
  timestamp: string
  timestampRelative?: string
  duration: string
  logPreview?: string
}

export interface BackupRunDetails extends BackupRun {
  logLines: string[]
  totalLines: number
  hasMore: boolean
  nextOffset?: number
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  hasMore: boolean
  nextOffset?: number
}

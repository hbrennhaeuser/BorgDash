import type { Job, JobStats, Archive, BackupRun, BackupRunDetails, BackupEvent, EventInfoDetails, PaginatedResponse } from '@/types'
import { authService } from '@/services/auth'
import router from '@/router'

const API_BASE = '/api/v1'

class ApiService {
  private async request<T>(endpoint: string): Promise<T> {
    const headers = {
      'Content-Type': 'application/json',
      ...authService.getAuthHeaders()
    }

    const response = await fetch(`${API_BASE}${endpoint}`, {
      headers
    })
    
    if (!response.ok) {
      if (response.status === 401) {
        // Unauthorized - token likely expired
        authService.logout()
        // Use the router's base path for login redirect
        const basePath = router.options.history.base.replace(/\/$/, '') // Remove trailing slash
        window.location.href = `${basePath}/login`
        throw new Error('Authentication expired. Please log in again.')
      }
      throw new Error(`API request failed: ${response.statusText}`)
    }
    return response.json()
  }

  // Get all jobs with optional search and filter parameters
  async getJobs(queryParams?: string): Promise<Job[]> {
    const endpoint = queryParams ? `/jobs?${queryParams}` : '/jobs'
    return this.request<Job[]>(endpoint)
  }

  // Get specific job details
  async getJob(jobId: string): Promise<Job> {
    return this.request<Job>(`/jobs/${jobId}`)
  }

  // Get job statistics
  async getJobStats(jobId: string): Promise<JobStats> {
    return this.request<JobStats>(`/jobs/${jobId}/stats`)
  }

  // Get job archives with pagination and sorting
  async getJobArchives(
    jobId: string, 
    offset: number = 0, 
    limit: number = 15, 
    sortBy: string = 'date', 
    sortOrder: string = 'desc'
  ): Promise<PaginatedResponse<Archive>> {
    const params = new URLSearchParams({
      offset: offset.toString(),
      limit: limit.toString(),
      sort_by: sortBy,
      sort_order: sortOrder
    })
    return this.request<PaginatedResponse<Archive>>(`/jobs/${jobId}/archives?${params}`)
  }

  // Get job backup runs
  async getJobRuns(jobId: string, limit: number = 15): Promise<BackupRun[]> {
    return this.request<BackupRun[]>(`/jobs/${jobId}/runs?limit=${limit}`)
  }

  // Get detailed backup run with paginated log
  async getBackupRunDetails(jobId: string, runId: string, offset: number = 0, limit: number = 20): Promise<BackupRunDetails> {
    return this.request<BackupRunDetails>(`/jobs/${jobId}/runs/${runId}?offset=${offset}&limit=${limit}`)
  }

  // Get job events with pagination (sorted by timestamp desc)
  async getJobEvents(jobId: string, offset: number = 0, limit: number = 15): Promise<PaginatedResponse<BackupEvent>> {
    return this.request<PaginatedResponse<BackupEvent>>(`/jobs/${jobId}/events?offset=${offset}&limit=${limit}`)
  }

  // Get event info content with pagination
  async getEventInfo(jobId: string, eventId: string, offset: number = 0, limit: number = 50): Promise<EventInfoDetails> {
    return this.request<EventInfoDetails>(`/jobs/${jobId}/events/${eventId}/info?offset=${offset}&limit=${limit}`)
  }

  // Sync job summary from events
  async syncJobSummary(jobId: string): Promise<{ success: boolean; message: string; events_processed: number; final_status?: string; last_backup?: string; last_successful_backup?: string }> {
    const response = await fetch(`${API_BASE}/jobs/${jobId}/sync`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...authService.getAuthHeaders()
      }
    })
    
    if (!response.ok) {
      if (response.status === 401) {
        authService.logout()
        const basePath = router.options.history.base.replace(/\/$/, '')
        window.location.href = `${basePath}/login`
        throw new Error('Authentication expired. Please log in again.')
      }
      throw new Error(`Sync failed: ${response.statusText}`)
    }
    
    return response.json()
  }

  // Get chart data for dashboard
  async getChartData(type: string, params: { tags?: string[]; search?: string }): Promise<{ success: boolean; type: string; data: Array<{ name: string; value: number }>; total_jobs: number }> {
    const queryParams = new URLSearchParams()
    queryParams.append('type', type)
    
    if (params.tags && params.tags.length > 0) {
      queryParams.append('tags', params.tags.join(','))
    }
    
    if (params.search) {
      queryParams.append('search', params.search)
    }
    
    // Chart endpoint is under /ui/chart (UI component, not API)
    const headers = {
      'Content-Type': 'application/json',
      ...authService.getAuthHeaders()
    }

    const response = await fetch(`/ui/chart?${queryParams.toString()}`, {
      headers
    })
    
    if (!response.ok) {
      if (response.status === 401) {
        // Unauthorized - token likely expired
        authService.logout()
        // Use the router's base path for login redirect
        const basePath = router.options.history.base.replace(/\/$/, '') // Remove trailing slash
        window.location.href = `${basePath}/login`
        throw new Error('Authentication expired. Please log in again.')
      }
      throw new Error(`Chart API request failed: ${response.statusText}`)
    }
    return response.json()
  }
}

export const apiService = new ApiService()

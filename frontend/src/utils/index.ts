export function formatDateTime(dateString: string | null | undefined): string {
  if (!dateString) return 'Unknown'
  
  try {
    const date = new Date(dateString)
    if (isNaN(date.getTime())) return 'Invalid Date'
    
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    })
  } catch (error) {
    return 'Invalid Date'
  }
}

export function formatRelativeTime(dateString: string | null | undefined): string {
  if (!dateString) return 'Unknown'
  
  try {
    const date = new Date(dateString)
    if (isNaN(date.getTime())) return 'Invalid Date'
    
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    
    const diffSeconds = Math.floor(diffMs / 1000)
    const diffMinutes = Math.floor(diffSeconds / 60)
    const diffHours = Math.floor(diffMinutes / 60)
    const diffDays = Math.floor(diffHours / 24)
    
    if (diffSeconds < 60) {
      return 'just now'
    } else if (diffMinutes < 60) {
      return `${diffMinutes} minute${diffMinutes !== 1 ? 's' : ''} ago`
    } else if (diffHours < 24) {
      return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`
    } else if (diffDays < 30) {
      return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`
    } else {
      return date.toLocaleDateString()
    }
  } catch (error) {
    return 'Invalid Date'
  }
}

export function getStatusColor(status: string): string {
  switch (status) {
    case 'success':
      return 'bg-green-100 text-green-800'
    case 'warning':
      return 'bg-yellow-100 text-yellow-800'
    case 'failed':
      return 'bg-red-100 text-red-800'
    case 'running':
      return 'bg-blue-100 text-blue-800'
    case 'on-time':
      return 'bg-green-100 text-green-800'
    case 'overdue':
      return 'bg-yellow-100 text-yellow-800'
    case 'unknown':
      return 'bg-gray-100 text-gray-800'
    case 'no-data':
      return 'bg-slate-100 text-slate-600'
    default:
      return 'bg-purple-100 text-purple-800'
  }
}

export function getEventTypeColor(eventType: string): string {
  switch (eventType) {
    case 'success':
      return 'bg-green-100 text-green-800'
    case 'failed':
      return 'bg-red-100 text-red-800'
    case 'start':
      return 'bg-blue-100 text-blue-800'
    case 'stop':
      return 'bg-blue-100 text-blue-800'
    case 'log':
      return 'bg-blue-100 text-blue-800'
    case 'info':
      return 'bg-blue-100 text-blue-800'
    default:
      return 'bg-blue-100 text-blue-800'
  }
}

export function getEventTypeIcon(eventType: string): string {
  switch (eventType) {
    case 'success':
      return 'CheckIcon'
    case 'failed':
      return 'ErrorIcon'
    case 'start':
      return 'PlayIcon'
    case 'stop':
      return 'StopIcon'
    case 'log':
      return 'LogIcon'
    case 'info':
      return 'InfoIcon'
    default:
      return 'InfoIcon'
  }
}

export function getStatusIcon(status: string): string {
  switch (status) {
    case 'success':
    case 'on-time':
      return '✓'
    case 'warning':
    case 'overdue':
      return '⚠'
    case 'failed':
      return '✗'
    case 'running':
      return '⟳'
    case 'unknown':
      return '?'
    case 'no-data':
      return '◦'
    default:
      return '?'
  }
}

export function getScheduleStatusText(status: string): string {
  switch (status) {
    case 'on-time':
      return 'On Schedule'
    case 'overdue':
      return 'Overdue'
    default:
      return 'Unknown'
  }
}

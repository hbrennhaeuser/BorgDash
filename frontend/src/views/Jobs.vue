<template>
  <div class="min-h-screen bg-gray-50 flex flex-col">
    <AppHeader />
    
    <!-- Add padding for fixed header -->
    <div class="pt-16 flex-1">
      <main class="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div class="px-4 py-6 sm:px-0">
          <!-- Page Header -->
          <div class="mb-8">
            <h1 class="text-3xl font-bold text-gray-900">Backup Jobs</h1>
            <p class="mt-2 text-gray-600">Monitor your backup jobs and view recent activity</p>
          </div>

          <!-- Search and Filter Controls -->
          <div v-if="!loading && !error && (jobs.length > 0 || searchQuery || selectedTags.length > 0)" class="mb-6 space-y-4">
            <!-- Search Bar -->
            <div class="relative">
              <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <SearchIcon class="h-5 w-5 text-gray-400" />
              </div>
              <input
                v-model="searchQuery"
                @input="debouncedSearch"
                type="text"
                placeholder="Search backup jobs by name or date..."
                class="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
              />
              <div v-if="searchQuery" class="absolute inset-y-0 right-0 pr-3 flex items-center">
                <button
                  @click="clearSearch"
                  class="text-gray-400 hover:text-gray-600"
                >
                  <XMarkIcon class="h-5 w-5" />
                </button>
              </div>
            </div>

            <!-- Filters Row -->
            <div class="flex flex-wrap items-center justify-between gap-4">
              <!-- Left side: Status and Tag Filters -->
              <div class="flex flex-wrap items-center gap-4">
                <!-- Status & Schedule Filter -->
                <div class="flex items-center space-x-2">
                  <label class="text-sm font-medium text-gray-700">Status:</label>
                  <div class="relative">
                    <button
                      @click="showStatusDropdown = !showStatusDropdown"
                      class="flex items-center px-3 py-1 text-sm border border-gray-300 rounded-md bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    >
                      <span v-if="selectedStatusFilters.length === 0" class="text-gray-500">Select status...</span>
                      <span v-else class="text-gray-900">{{ selectedStatusFilters.length }} selected</span>
                      <ChevronDownIcon :class="{ 'rotate-180': showStatusDropdown }" class="h-4 w-4 ml-2 transition-transform duration-200" />
                    </button>
                    
                    <div
                      v-if="showStatusDropdown"
                      class="absolute z-10 mt-1 w-48 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-auto"
                    >
                      <div class="py-1">
                        <!-- Backup Status -->
                        <div class="px-3 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wide border-b border-gray-200">
                          Backup Status
                        </div>
                                                <button
                          v-for="status in ['success', 'warning', 'failed', 'running', 'unknown', 'no-data']"
                          :key="status"
                          @click="toggleStatusFilter('status-' + status)"
                          class="flex items-center w-full px-3 py-2 text-sm hover:bg-gray-100 transition-colors text-left"
                        >
                          <input
                            :checked="selectedStatusFilters.includes(`status-${status}`)"
                            type="checkbox"
                            class="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                            readonly
                          />
                          <span class="ml-2 text-gray-900 capitalize">{{ status }}</span>
                        </button>
                        
                        <!-- Schedule Status -->
                        <div class="px-3 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wide border-b border-gray-200 mt-2">
                          Schedule Status
                        </div>
                        <button
                          v-for="scheduleStatus in ['on-time', 'overdue', 'unknown']"
                          :key="`schedule-${scheduleStatus}`"
                          @click="toggleStatusFilter(`schedule-${scheduleStatus}`)"
                          class="flex items-center w-full px-3 py-2 text-sm hover:bg-gray-100 transition-colors"
                        >
                          <input
                            :checked="selectedStatusFilters.includes(`schedule-${scheduleStatus}`)"
                            type="checkbox"
                            class="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                            readonly
                          />
                          <span class="ml-2 text-gray-900">{{ 
                            scheduleStatus === 'on-time' ? 'On Time' : 
                            scheduleStatus === 'overdue' ? 'Overdue' : 
                            'Unknown' 
                          }}</span>
                        </button>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Tag Filter -->
                <div class="flex items-center space-x-2">
                  <label class="text-sm font-medium text-gray-700">Tags:</label>
                  <div class="relative">
                    <button
                      @click="showTagDropdown = !showTagDropdown"
                      class="flex items-center px-3 py-1 text-sm border border-gray-300 rounded-md bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    >
                      <span v-if="selectedTags.length === 0" class="text-gray-500">Select tags...</span>
                      <span v-else class="text-gray-900">{{ selectedTags.length }} selected</span>
                      <ChevronDownIcon :class="{ 'rotate-180': showTagDropdown }" class="h-4 w-4 ml-2 transition-transform duration-200" />
                    </button>
                    
                    <div
                      v-if="showTagDropdown"
                      class="absolute z-10 mt-1 min-w-48 max-w-80 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-auto"
                    >
                      <div class="py-1">
                        <button
                          v-for="tag in availableTags"
                          :key="tag"
                          @click="toggleTagFilter(tag)"
                          class="flex items-start w-full px-3 py-2 text-sm hover:bg-gray-100 transition-colors text-left"
                        >
                          <input
                            :checked="selectedTags.includes(tag)"
                            type="checkbox"
                            class="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500 mt-0.5 flex-shrink-0"
                            readonly
                          />
                          <span class="ml-2 text-gray-900 break-words">{{ tag }}</span>
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Right side: Sort Controls -->
              <div class="flex items-center space-x-2">
                <label class="text-sm font-medium text-gray-700">Sort by:</label>
                <select
                  v-model="sortBy"
                  @change="applySorting"
                  class="rounded-md border-gray-300 text-sm focus:border-blue-500 focus:ring-blue-500"
                >
                  <option value="name">Name</option>
                  <option value="lastBackup">Last Backup</option>
                  <option value="status">Status</option>
                </select>
                <button
                  @click="toggleSortDirection"
                  class="flex items-center px-2 py-1 text-sm border border-gray-300 rounded-md bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                  :title="sortDir === 'asc' ? 'Click to sort descending' : 'Click to sort ascending'"
                >
                  <ChevronUpIcon v-if="sortDir === 'asc'" class="h-4 w-4 mr-1" />
                  <ChevronDownIcon v-else class="h-4 w-4 mr-1" />
                  <span class="text-gray-700">{{ sortDir === 'asc' ? 'Ascending' : 'Descending' }}</span>
                </button>
              </div>
            </div>

            <!-- Active Filters Summary -->
            <div v-if="hasActiveFilters" class="flex items-center space-x-2">
              <span class="text-sm text-gray-500">Active filters:</span>
              <div class="flex flex-wrap gap-1">
                <!-- Status filters -->
                <span
                  v-for="statusFilter in selectedStatusFilters"
                  :key="statusFilter"
                  class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium"
                  :class="getStatusFilterBadgeClass(statusFilter)"
                >
                  {{ getStatusFilterLabel(statusFilter) }}
                  <button
                    @click="toggleStatusFilter(statusFilter)"
                    class="ml-1 hover:opacity-75"
                  >
                    <XMarkIcon class="h-3 w-3" />
                  </button>
                </span>
                
                <!-- Tag filters -->
                <span
                  v-for="tag in selectedTags"
                  :key="`tag-${tag}`"
                  class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                >
                  Tag: {{ tag }}
                  <button
                    @click="toggleTagFilter(tag)"
                    class="ml-1 text-blue-600 hover:text-blue-800"
                  >
                    <XMarkIcon class="h-3 w-3" />
                  </button>
                </span>
              </div>
              <button
                @click="clearAllFilters"
                class="text-sm text-gray-500 hover:text-gray-700 underline"
              >
                Clear all
              </button>
            </div>
          </div>

          <!-- Loading State -->
          <div v-if="loading" class="flex justify-center items-center py-12">
            <LoadingSpinner size="lg" text="Loading backup jobs..." />
          </div>

          <!-- Error State -->
          <div v-else-if="error" class="text-center py-12">
            <div class="bg-red-50 border border-red-200 rounded-lg p-6 max-w-md mx-auto">
              <div class="flex items-center justify-center w-12 h-12 mx-auto bg-red-100 rounded-full mb-4">
                <span class="text-red-600 text-xl">⚠</span>
              </div>
              <h3 class="text-lg font-medium text-red-900 mb-2">Failed to load jobs</h3>
              <p class="text-red-700 mb-4">{{ error }}</p>
              <button
                @click="loadJobs"
                class="bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700 transition-colors"
              >
                Try Again
              </button>
            </div>
          </div>

          <!-- Empty State -->
          <div v-else-if="jobs.length === 0" class="text-center py-12">
            <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-8 max-w-md mx-auto">
              <div class="flex items-center justify-center w-16 h-16 mx-auto bg-gray-100 rounded-full mb-4">
                <span class="text-gray-400 text-2xl">📦</span>
              </div>
              <h3 class="text-lg font-medium text-gray-900 mb-2">No jobs configured</h3>
              <p class="text-gray-600 mb-6">
                Get started by creating your first backup job to monitor.
              </p>
              <RouterLink
                to="/jobs/new"
                class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 transition-colors"
              >
                <PlusIcon class="h-4 w-4 mr-2" />
                Create First Job
              </RouterLink>
            </div>
          </div>

          <!-- Jobs Grid -->
          <div v-else class="space-y-6">
            <!-- No results message -->
            <div v-if="filteredJobs.length === 0 && (searchQuery || selectedTags.length > 0)" class="text-center py-8">
              <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div class="flex items-center justify-center w-12 h-12 mx-auto bg-gray-100 rounded-full mb-4">
                  <SearchIcon class="h-6 w-6 text-gray-400" />
                </div>
                <h3 class="text-lg font-medium text-gray-900 mb-2">No jobs found</h3>
                <p class="text-gray-600 mb-4">
                  No backup jobs match your current search or filter criteria.
                </p>
                <button
                  @click="clearAllFilters"
                  class="text-blue-600 hover:text-blue-800 font-medium"
                >
                  Clear all filters
                </button>
              </div>
            </div>
            
            <!-- Job Cards -->
            <JobCard
              v-for="job in filteredJobs"
              :key="job.jobId"
              :job="job"
              :expanded-job-id="expandedJobId"
              :ref="(el: any) => jobCardRefs[job.jobId] = el"
              @refresh="refreshJob(job.jobId)"
              @toggle-expansion="handleToggleExpansion"
            />
          </div>
        </div>
      </main>
    </div>
    
    <AppFooter />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { RouterLink } from 'vue-router'
import type { Job } from '@/types'
import { apiService } from '@/services/api'
import AppHeader from '@/components/AppHeader.vue'
import AppFooter from '@/components/AppFooter.vue'
import JobCard from '@/components/JobCard.vue'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import PlusIcon from '@/components/icons/PlusIcon.vue'
import SearchIcon from '@/components/icons/SearchIcon.vue'
import XMarkIcon from '@/components/icons/XMarkIcon.vue'
import ChevronUpIcon from '@/components/icons/ChevronUpIcon.vue'
import ChevronDownIcon from '@/components/icons/ChevronDownIcon.vue'

// Simple debounce function
function debounce<T extends (...args: any[]) => any>(func: T, wait: number): T {
  let timeout: ReturnType<typeof setTimeout>
  return ((...args: any[]) => {
    clearTimeout(timeout)
    timeout = setTimeout(() => func(...args), wait)
  }) as T
}

// State
const jobs = ref<Job[]>([])
const loading = ref(true)
const error = ref<string | null>(null)
const expandedJobId = ref<string | null>(null)
const jobCardRefs = ref<Record<string, any>>({})

// Search and Filter State
const searchQuery = ref('')
const sortBy = ref('name')
const sortDir = ref<'asc' | 'desc'>('asc')
const selectedTags = ref<string[]>([])
const selectedStatusFilters = ref<string[]>([])
const showTagDropdown = ref(false)
const showStatusDropdown = ref(false)
const selectedTagFilter = ref('')

// Computed
const availableTags = computed(() => {
  const allTags = jobs.value.flatMap(job => job.tags || [])
  return [...new Set(allTags)].sort()
})

const hasActiveFilters = computed(() => {
  return selectedTags.value.length > 0 || 
         selectedStatusFilters.value.length > 0
})

const filteredJobs = computed(() => {
  // Start with all jobs
  let filtered = [...jobs.value]
  
  // Apply search filter (done on frontend for immediate response)
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    // Name matches get priority
    const nameMatches = filtered.filter(job => 
      job.name.toLowerCase().includes(query)
    )
    const dateMatches = filtered.filter(job => 
      !nameMatches.includes(job) &&
      job.lastBackup && typeof job.lastBackup === 'string' && job.lastBackup.toLowerCase().includes(query)
    )
    filtered = [...nameMatches, ...dateMatches]
  }
  
  // Apply status filters
  if (selectedStatusFilters.value.length > 0) {
    filtered = filtered.filter(job => {
      // Check backup status filters
      const backupStatusFilters = selectedStatusFilters.value.filter(f => f.startsWith('status-'))
      const scheduleStatusFilters = selectedStatusFilters.value.filter(f => f.startsWith('schedule-'))
      
      let matchesBackupStatus = backupStatusFilters.length === 0 || 
        backupStatusFilters.some(f => f === `status-${job.status}`)
      
      let matchesScheduleStatus = scheduleStatusFilters.length === 0 || 
        scheduleStatusFilters.some(f => f === `schedule-${job.scheduleStatus}`)
      
      return matchesBackupStatus && matchesScheduleStatus
    })
  }
  
  // Apply tag filters
  if (selectedTags.value.length > 0) {
    filtered = filtered.filter(job =>
      job.tags && selectedTags.value.every(tag => 
        job.tags!.map((t: string) => t.toLowerCase()).includes(tag.toLowerCase())
      )
    )
  }
  
  // Apply sorting
  filtered.sort((a, b) => {
    let result = 0
    if (sortBy.value === 'lastBackup') {
      const dateA = a.lastBackup ? new Date(a.lastBackup) : new Date(0)
      const dateB = b.lastBackup ? new Date(b.lastBackup) : new Date(0)
      
      // Handle invalid dates
      const timeA = isNaN(dateA.getTime()) ? 0 : dateA.getTime()
      const timeB = isNaN(dateB.getTime()) ? 0 : dateB.getTime()
      
      result = timeA - timeB
    } else if (sortBy.value === 'status') {
      result = a.status.localeCompare(b.status)
    } else {
      result = a.name.localeCompare(b.name)
    }
    return sortDir.value === 'desc' ? -result : result
  })
  
  return filtered
})

// Methods
const loadJobs = async () => {
  loading.value = true
  error.value = null
  
  try {
    // Use the new API with search and filter support
    const params = new URLSearchParams()
    if (searchQuery.value) params.append('search', searchQuery.value)
    if (selectedTags.value.length > 0) params.append('tags', selectedTags.value.join(','))
    params.append('sortBy', sortBy.value)
    params.append('sortDir', sortDir.value)
    
    jobs.value = await apiService.getJobs(params.toString())
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'An unexpected error occurred'
    console.error('Failed to load jobs:', err)
  } finally {
    loading.value = false
  }
}

const refreshJob = async (jobId: string) => {
  try {
    const updatedJob = await apiService.getJob(jobId)
    const index = jobs.value.findIndex(j => j.jobId === jobId)
    if (index !== -1) {
      jobs.value[index] = updatedJob
    }
  } catch (err) {
    console.error(`Failed to refresh job ${jobId}:`, err)
  }
}

const handleToggleExpansion = (jobId: string) => {
  // If a different job is being expanded, collapse the currently expanded one
  if (expandedJobId.value && expandedJobId.value !== jobId) {
    const previousJobCard = jobCardRefs.value[expandedJobId.value]
    if (previousJobCard?.collapseAll) {
      previousJobCard.collapseAll()
    }
  }
  
  // Set the currently expanded job
  expandedJobId.value = jobId
}

// Search and Filter Methods
const debouncedSearch = debounce(() => {
  // Search is now handled in the computed property for immediate response
}, 300)

const clearSearch = () => {
  searchQuery.value = ''
}

const applySorting = () => {
  // Sorting is handled in computed property
}

const toggleSortDirection = () => {
  sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
}

const toggleStatusFilter = (statusFilter: string) => {
  const index = selectedStatusFilters.value.indexOf(statusFilter)
  if (index > -1) {
    selectedStatusFilters.value.splice(index, 1)
  } else {
    selectedStatusFilters.value.push(statusFilter)
  }
}

const getStatusFilterLabel = (statusFilter: string): string => {
  if (statusFilter.startsWith('status-')) {
    const status = statusFilter.replace('status-', '')
    return `Status: ${status.charAt(0).toUpperCase() + status.slice(1)}`
  } else if (statusFilter.startsWith('schedule-')) {
    const schedule = statusFilter.replace('schedule-', '')
    return schedule === 'on-time' ? 'On Time' : 'Overdue'
  }
  return statusFilter
}

const getStatusFilterBadgeClass = (statusFilter: string): string => {
  if (statusFilter.startsWith('status-')) {
    const status = statusFilter.replace('status-', '')
    if (status === 'success') return 'bg-green-100 text-green-800'
    if (status === 'warning') return 'bg-yellow-100 text-yellow-800'
    if (status === 'failed') return 'bg-red-100 text-red-800'
    if (status === 'running') return 'bg-blue-100 text-blue-800'
    if (status === 'no-data') return 'bg-slate-100 text-slate-600'
  } else if (statusFilter.startsWith('schedule-')) {
    return 'bg-purple-100 text-purple-800'
  }
  return 'bg-gray-100 text-gray-800'
}

const toggleTagFilter = (tag: string) => {
  const index = selectedTags.value.indexOf(tag)
  if (index > -1) {
    selectedTags.value.splice(index, 1)
  } else {
    selectedTags.value.push(tag)
  }
}

const addTagFilter = () => {
  if (selectedTagFilter.value && !selectedTags.value.includes(selectedTagFilter.value)) {
    selectedTags.value.push(selectedTagFilter.value)
    selectedTagFilter.value = ''
  }
}

const removeTagFilter = (tag: string) => {
  selectedTags.value = selectedTags.value.filter(t => t !== tag)
}

const clearAllFilters = () => {
  searchQuery.value = ''
  selectedTags.value = []
  selectedStatusFilters.value = []
  selectedTagFilter.value = ''
  showTagDropdown.value = false
  showStatusDropdown.value = false
}

// Lifecycle
onMounted(() => {
  loadJobs()
  
  // Listen for global refresh events from the header
  window.addEventListener('refresh-repositories', handleGlobalRefresh)
})

// Cleanup event listener when component is unmounted
onUnmounted(() => {
  window.removeEventListener('refresh-repositories', handleGlobalRefresh)
})

// Add refresh functionality
const refreshAllJobs = async () => {
  loading.value = true
  try {
    await loadJobs()
    // Also refresh all individual jobs that might have changed
    for (const job of jobs.value) {
      await refreshJob(job.jobId)
    }
  } finally {
    loading.value = false
  }
}

const handleGlobalRefresh = () => {
  refreshAllJobs()
}
</script>

<template>
  <div class="bg-white rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
    <!-- Card Header -->
    <div class="px-6 py-4 border-b border-gray-200">
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-3">
          <h3 class="text-lg font-semibold text-gray-900">{{ job.name }}</h3>
          <span 
            class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
            :class="getStatusColor(job.status)"
          >
            <span class="mr-1">{{ getStatusIcon(job.status) }}</span>
            {{ job.status }}
          </span>
          <span 
            class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
            :class="getStatusColor(job.scheduleStatus)"
          >
            <span class="mr-1">{{ getStatusIcon(job.scheduleStatus) }}</span>
            {{ getScheduleStatusText(job.scheduleStatus) }}
          </span>
        </div>
        
        <div class="flex items-center space-x-2">
          <button
            @click="refreshJob"
            :disabled="isRefreshing"
            class="p-2 text-gray-400 hover:text-gray-600 rounded-full hover:bg-gray-100 transition-colors disabled:opacity-50"
            title="Refresh job data"
          >
            <RefreshIcon :class="{ 'animate-spin': isRefreshing }" />
          </button>
          
          <!-- 3-dots menu -->
          <div class="relative">
            <button
              @click="toggleDropdown"
              class="p-2 text-gray-400 hover:text-gray-600 rounded-full hover:bg-gray-100 transition-colors"
              title="Job actions"
            >
              <DotsVerticalIcon />
            </button>
            
            <!-- Custom dropdown -->
            <div
              v-if="showDropdown"
              class="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-2 z-50"
              @click.stop
            >
              <RouterLink
                :to="`/jobs/${job.jobId}/settings`"
                class="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 transition-colors"
                @click="closeDropdown"
              >
                <CogIcon class="w-4 h-4 mr-3" />
                Settings
              </RouterLink>
              <button
                @click="syncJob"
                :disabled="isSyncing"
                class="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 transition-colors disabled:opacity-50"
              >
                <RefreshIcon :class="['w-4 h-4 mr-3', { 'animate-spin': isSyncing }]" />
                {{ isSyncing ? 'Syncing...' : 'Sync' }}
              </button>
            </div>
          </div>
        </div>
      </div>
      
      <div class="mt-1 flex items-center justify-between">
        <div class="text-sm">
          <span class="text-gray-900 font-medium">{{ formatDateTime(job.lastBackup) }}</span>
          <span class="text-gray-500 text-xs ml-2">({{ job.lastBackupRelative || formatRelativeTime(job.lastBackup) }})</span>
        </div>
        
        <!-- Tags -->
        <div v-if="job.tags && job.tags.length > 0" class="flex flex-wrap gap-1">
          <span
            v-for="tag in job.tags"
            :key="tag"
            class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
          >
            {{ tag }}
          </span>
        </div>
      </div>
    </div>

    <!-- Statistics Row -->
    <div class="px-6 py-4 border-b border-gray-200">
      <div class="grid grid-cols-2 md:grid-cols-5 gap-4">
        <div class="text-center">
          <div class="text-2xl font-bold text-gray-900">{{ job.stats.archiveCount }}</div>
          <div class="text-sm text-gray-500">Archives</div>
        </div>
        <div class="text-center">
          <div class="text-2xl font-bold text-gray-900">{{ job.stats.fullSize }}</div>
          <div class="text-sm text-gray-500">Full Size</div>
        </div>
        <div class="text-center">
          <div class="text-2xl font-bold text-gray-900">{{ job.stats.compressedSize }}</div>
          <div class="text-sm text-gray-500">Compressed</div>
        </div>
        <div class="text-center">
          <div class="text-2xl font-bold text-gray-900">{{ job.stats.deduplicatedSize }}</div>
          <div class="text-sm text-gray-500">Deduplicated</div>
        </div>
        <div class="text-center">
          <div class="text-2xl font-bold text-gray-900">{{ job.stats.compressionRatio }}</div>
          <div class="text-sm text-gray-500">Compression</div>
        </div>
      </div>
    </div>

    <!-- Expandable Sections -->
    <div class="px-6 py-4 space-y-4">
      <!-- Archives -->
      <div>
        <div class="flex items-center justify-between mb-3">
          <button
            @click="toggleArchives"
            class="flex items-center text-left text-sm font-medium text-gray-700 hover:text-gray-900 transition-colors"
          >
            <span>Archives</span>
            <ChevronDownIcon :class="{ 'rotate-180': showArchives }" class="ml-2 transition-transform duration-200" />
          </button>
          
          <div v-if="showArchives" class="flex items-center space-x-2">
            <select
              v-model="archiveSortBy"
              @change="sortArchives"
              class="text-xs border border-gray-300 rounded-md px-2 py-1 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="date">Sort by Date</option>
              <option value="name">Sort by Name</option>
              <option value="originalSize">Sort by Original Size</option>
              <option value="compressedSize">Sort by Compressed Size</option>
              <option value="deduplicatedSize">Sort by Deduplicated Size</option>
            </select>
            <button
              @click="toggleArchiveSortOrder"
              class="text-xs text-gray-600 hover:text-gray-800 px-2 py-1 border border-gray-300 rounded-md"
              :title="archiveSortOrder === 'desc' ? 'Descending' : 'Ascending'"
            >
              {{ archiveSortOrder === 'desc' ? '↓' : '↑' }}
            </button>
          </div>
        </div>
        
        <div v-if="showArchives" class="mt-3">
          <LoadingSpinner v-if="loadingArchives" size="sm" text="Loading archives..." />
          <div v-else-if="sortedArchives.length > 0" class="space-y-2">
            <div
              v-for="archive in sortedArchives"
              :key="archive.name"
              class="py-3 px-4 bg-gray-50 rounded-md"
            >
              <div class="flex items-center justify-between mb-2">
                <span class="font-mono text-sm text-gray-900">{{ archive.name }}</span>
                <span class="text-xs text-gray-500">{{ formatDateTime(archive.createdAt) }}</span>
              </div>
              <div class="grid grid-cols-3 gap-4 text-xs text-gray-600">
                <div>
                  <span class="font-medium">Original:</span> {{ archive.originalSize }}
                </div>
                <div>
                  <span class="font-medium">Compressed:</span> {{ archive.compressedSize }}
                </div>
                <div>
                  <span class="font-medium">Deduplicated:</span> {{ archive.deduplicatedSize }}
                </div>
              </div>
            </div>
            
            <button
              v-if="hasMoreArchives"
              @click="loadMoreArchives"
              :disabled="loadingMoreArchives"
              class="w-full py-2 px-4 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors disabled:opacity-50"
            >
              <LoadingSpinner v-if="loadingMoreArchives" size="sm" class="inline mr-2" />
              {{ loadingMoreArchives ? 'Loading...' : 'Load More' }}
            </button>
          </div>
          <p v-else class="text-sm text-gray-500 py-2">No archives found</p>
        </div>
      </div>

      <!-- Recent Events -->
      <div>
        <div class="flex items-center justify-between mb-3">
          <button
            @click="toggleEvents"
            class="flex items-center text-left text-sm font-medium text-gray-700 hover:text-gray-900 transition-colors"
          >
            <span>Recent Events</span>
            <ChevronDownIcon :class="{ 'rotate-180': showEvents }" class="ml-2 transition-transform duration-200" />
          </button>
        </div>
        
        <div v-if="showEvents" class="mt-3">
          <LoadingSpinner v-if="loadingEvents" size="sm" text="Loading events..." />
          <div v-else-if="sortedEvents.length > 0" class="space-y-2">
            <div
              v-for="(event, index) in sortedEvents"
              :key="event.id"
            >
              <div class="bg-gray-50 rounded-md">
                <div 
                  class="flex items-center justify-between py-2 px-3"
                  :class="{ 'cursor-pointer hover:bg-gray-100 transition-colors': event.hasInfo }"
                  @click="event.hasInfo ? toggleEventInfo(event.id) : null"
                >
                  <div class="flex items-center space-x-2">
                    <span 
                      class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium"
                      :class="getEventTypeColor(event.type)"
                    >
                      <component :is="getEventIconComponent(event.type)" class="w-3 h-3" />
                    </span>
                    <span class="text-sm text-gray-900">{{ event.message }}</span>
                    <span class="text-xs text-gray-500">({{ event.timestampRelative || formatRelativeTime(event.timestamp) }})</span>
                  </div>
                  <div class="flex items-center space-x-2">
                    <span class="text-xs text-gray-500">{{ formatDateTime(event.timestamp) }}</span>
                    <ChevronDownIcon 
                      :class="{ 
                        'rotate-180': expandedEventId === event.id && event.hasInfo,
                        'text-gray-400': !event.hasInfo,
                        'text-gray-600': event.hasInfo
                      }" 
                      class="h-4 w-4 transition-transform duration-200" 
                    />
                  </div>
                </div>
                
                <!-- Expandable info section -->
                <div v-if="expandedEventId === event.id && event.hasInfo" class="px-3 pb-3">
                  <LoadingSpinner v-if="loadingEventInfo" size="sm" text="Loading info..." />
                  <div v-else-if="currentEventInfo" class="mt-2">
                    <div class="bg-gray-900 text-green-400 text-xs rounded-md font-mono relative">
                      <div class="p-3 overflow-auto max-h-80" ref="infoContainer">
                        <div v-for="(line, index) in displayedInfoLines" :key="index" v-html="highlightLogLine(line)"></div>
                      </div>
                      <div v-if="currentEventInfo.hasMore" class="border-t border-gray-700 p-2 text-center">
                        <button
                          @click="loadMoreInfoLines"
                          :disabled="loadingMoreInfoLines"
                          class="text-xs text-blue-400 hover:text-blue-300 disabled:opacity-50"
                        >
                          <LoadingSpinner v-if="loadingMoreInfoLines" size="sm" class="inline mr-1" />
                          {{ loadingMoreInfoLines ? 'Loading...' : 'Load More Lines' }}
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              
              <!-- Visual separator after start events (except for the last event) -->
              <div 
                v-if="event.type === 'start' && index < sortedEvents.length - 1" 
                class="flex items-center my-4"
              >
                <div class="flex-grow border-t border-gray-300"></div>
                <!-- <span class="px-3 text-xs text-gray-500 bg-white">New Backup Session</span> -->
                <!-- <div class="flex-grow border-t border-gray-300"></div> -->
              </div>
            </div>
          </div>
          <p v-else class="text-sm text-gray-500 py-2">No events found</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { RouterLink } from 'vue-router'
import type { Job, Archive, BackupEvent, EventInfoDetails } from '@/types'
import { apiService } from '@/services/api'
import { formatDateTime, formatRelativeTime, getStatusColor, getStatusIcon, getScheduleStatusText, getEventTypeColor } from '@/utils'
import RefreshIcon from '@/components/icons/RefreshIcon.vue'
import CogIcon from '@/components/icons/CogIcon.vue'
import DotsVerticalIcon from '@/components/icons/DotsVerticalIcon.vue'
import ChevronDownIcon from '@/components/icons/ChevronDownIcon.vue'
import CheckIcon from '@/components/icons/CheckIcon.vue'
import ErrorIcon from '@/components/icons/ErrorIcon.vue'
import PlayIcon from '@/components/icons/PlayIcon.vue'
import StopIcon from '@/components/icons/StopIcon.vue'
import LogIcon from '@/components/icons/LogIcon.vue'
import InfoIcon from '@/components/icons/InfoIcon.vue'
// Simple log highlighter for timestamps, levels, and errors
function highlightLogLine(line: string): string {
  // Highlight timestamp (ISO or date)
  let html = line.replace(/^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})/, '<span style="color:#93c5fd;">$1</span>')
  // Highlight log levels
  html = html.replace(/\b(INFO|WARNING|ERROR|DEBUG)\b/, (level) => {
    if (level === 'ERROR') return '<span style="color:#f87171;font-weight:bold;">' + level + '</span>'
    if (level === 'WARNING') return '<span style="color:#fbbf24;font-weight:bold;">' + level + '</span>'
    if (level === 'INFO') return '<span style="color:#34d399;">' + level + '</span>'
    if (level === 'DEBUG') return '<span style="color:#a78bfa;">' + level + '</span>'
    return level
  })
  // Highlight error lines
  if (/error|failed|exception/i.test(line)) {
    html = '<span style="color:#f87171;">' + html + '</span>'
  }
  // Highlight warning lines
  else if (/warn|warning/i.test(line)) {
    html = '<span style="color:#fbbf24;">' + html + '</span>'
  }
  return html
}
import LoadingSpinner from '@/components/LoadingSpinner.vue'

interface Props {
  job: Job
  expandedJobId?: string | null
  expandedSections?: string[]
}

const props = defineProps<Props>()
const emit = defineEmits<{
  refresh: []
  toggleExpansion: [jobId: string, section: 'archives' | 'events']
}>()

// State
const showArchives = ref(props.expandedSections?.includes('archives') || false)
const showEvents = ref(props.expandedSections?.includes('events') || false)
const archives = ref<Archive[]>([])
const events = ref<BackupEvent[]>([])
const currentEventInfo = ref<EventInfoDetails | null>(null)
const expandedEventId = ref<string | null>(null)
const displayedInfoLines = ref<string[]>([])

// Loading states
const loadingEventInfo = ref(false)
const loadingArchives = ref(false)
const loadingEvents = ref(false)
const loadingMoreArchives = ref(false)
const loadingMoreInfoLines = ref(false)
const isRefreshing = ref(false)
const isSyncing = ref(false)

// Dropdown state
const showDropdown = ref(false)

// Pagination
const archivesOffset = ref(0)
const hasMoreArchives = ref(false)
const infoOffset = ref(0)

// Sorting variables (archives only)
const archiveSortBy = ref<'date' | 'name' | 'originalSize' | 'compressedSize' | 'deduplicatedSize'>('date')
const archiveSortOrder = ref<'asc' | 'desc'>('desc')

// Computed properties for data display
const sortedArchives = computed(() => {
  // Archives are now sorted server-side, so just return them as-is
  return archives.value
})

const sortedEvents = computed(() => {
  // Events are now sorted server-side by timestamp (desc), so just return them as-is
  return events.value
})

// Helper function to get the correct icon component
const getEventIconComponent = (eventType: string) => {
  switch (eventType) {
    case 'success':
      return CheckIcon
    case 'failed':
      return ErrorIcon
    case 'start':
      return PlayIcon
    case 'stop':
      return StopIcon
    case 'log':
      return LogIcon
    case 'info':
      return InfoIcon
    default:
      return InfoIcon
  }
}

// Methods
const refreshJob = async () => {
  isRefreshing.value = true
  try {
    emit('refresh')
  } finally {
    setTimeout(() => {
      isRefreshing.value = false
    }, 1000)
  }
}

const toggleArchives = async () => {
  const newState = !showArchives.value
  
  if (newState) {
    // Notify parent to collapse other sections
    emit('toggleExpansion', props.job.jobId, 'archives')
  }
  
  showArchives.value = newState
  
  if (showArchives.value && archives.value.length === 0) {
    await loadArchives()
  }
}

const toggleEvents = async () => {
  const newState = !showEvents.value
  
  if (newState) {
    // Notify parent to collapse other sections
    emit('toggleExpansion', props.job.jobId, 'events')
  }
  
  showEvents.value = newState
  
  if (showEvents.value && events.value.length === 0) {
    await loadEvents()
  }
}

const loadArchives = async () => {
  loadingArchives.value = true
  try {
    const response = await apiService.getJobArchives(
      props.job.jobId, 
      0, 
      15, 
      archiveSortBy.value, 
      archiveSortOrder.value
    )
    archives.value = response.items
    hasMoreArchives.value = response.hasMore
    archivesOffset.value = 15
  } catch (error) {
    console.error('Failed to load archives:', error)
  } finally {
    loadingArchives.value = false
  }
}

const loadMoreArchives = async () => {
  loadingMoreArchives.value = true
  try {
    const response = await apiService.getJobArchives(
      props.job.jobId, 
      archivesOffset.value, 
      15, 
      archiveSortBy.value, 
      archiveSortOrder.value
    )
    archives.value = [...archives.value, ...response.items]
    hasMoreArchives.value = response.hasMore
    archivesOffset.value += 15
  } catch (error) {
    console.error('Failed to load more archives:', error)
  } finally {
    loadingMoreArchives.value = false
  }
}

const loadEvents = async () => {
  loadingEvents.value = true
  try {
    const response = await apiService.getJobEvents(props.job.jobId, 0, 15)
    events.value = response.items
  } catch (error) {
    console.error('Failed to load events:', error)
  } finally {
    loadingEvents.value = false
  }
}

const toggleEventInfo = async (eventId: string) => {
  if (expandedEventId.value === eventId) {
    // Collapse current event
    expandedEventId.value = null
    currentEventInfo.value = null
    displayedInfoLines.value = []
    infoOffset.value = 0
  } else {
    // Expand new event (accordion behavior)
    expandedEventId.value = eventId
    currentEventInfo.value = null
    displayedInfoLines.value = []
    infoOffset.value = 0
    
    await loadEventInfo(eventId)
  }
}

const loadEventInfo = async (eventId: string) => {
  loadingEventInfo.value = true
  try {
    const info = await apiService.getEventInfo(props.job.jobId, eventId, 0, 20)
    currentEventInfo.value = info
    displayedInfoLines.value = info.lines
    infoOffset.value = 20
  } catch (error) {
    console.error(`Failed to load event info for ${eventId}:`, error)
  } finally {
    loadingEventInfo.value = false
  }
}

const loadMoreInfoLines = async () => {
  if (!currentEventInfo.value || !expandedEventId.value) return
  
  loadingMoreInfoLines.value = true
  try {
    const info = await apiService.getEventInfo(
      props.job.jobId, 
      expandedEventId.value, 
      infoOffset.value, 
      20
    )
    
    displayedInfoLines.value = [...displayedInfoLines.value, ...info.lines]
    currentEventInfo.value.hasMore = info.hasMore
    currentEventInfo.value.nextOffset = info.nextOffset
    infoOffset.value += 20
  } catch (error) {
    console.error('Failed to load more info lines:', error)
  } finally {
    loadingMoreInfoLines.value = false
  }
}

// Sorting methods
const sortArchives = async () => {
  // Reset to first page and reload with new sorting
  archivesOffset.value = 0
  await loadArchives()
}

const toggleArchiveSortOrder = async () => {
  archiveSortOrder.value = archiveSortOrder.value === 'asc' ? 'desc' : 'asc'
  // Reset to first page and reload with new sorting
  archivesOffset.value = 0
  await loadArchives()
}

// Dropdown methods
const toggleDropdown = () => {
  showDropdown.value = !showDropdown.value
}

const closeDropdown = () => {
  showDropdown.value = false
}

// Sync job method
const syncJob = async () => {
  if (isSyncing.value) return
  
  isSyncing.value = true
  try {
    await apiService.syncJobSummary(props.job.jobId)
    // Close dropdown after successful sync
    closeDropdown()
    // Emit refresh to update the job data
    emit('refresh')
  } catch (error) {
    console.error('Failed to sync job:', error)
    // You could add a toast notification here if you have one
  } finally {
    setTimeout(() => {
      isSyncing.value = false
    }, 1000)
  }
}

// Watch for external collapse requests
const collapseAll = () => {
  showArchives.value = false
  showEvents.value = false
  expandedEventId.value = null
  currentEventInfo.value = null
  displayedInfoLines.value = []
}

// Load data on mount if sections are expanded
onMounted(async () => {
  if (showEvents.value && events.value.length === 0) {
    await loadEvents()
  }
  
  // Add click outside listener for dropdown
  document.addEventListener('click', handleClickOutside)
})

// Cleanup event listener
onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})

// Handle click outside dropdown
const handleClickOutside = (event: Event) => {
  const target = event.target as HTMLElement
  if (!target.closest('.relative')) {
    showDropdown.value = false
  }
}

// Expose collapse method for parent component
defineExpose({
  collapseAll
})
</script>

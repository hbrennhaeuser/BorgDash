<template>
  <div :class="className">
    <ChartLoading v-if="loading" />
    <div v-else-if="hasData" :id="chartId" ref="chartContainer" class="w-full h-full"></div>
    <div v-else class="flex items-center justify-center h-full min-h-32">
      <div class="text-center">
        <div class="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-gray-100 mb-4">
          <svg class="h-8 w-8 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
        </div>
        <p class="text-sm text-gray-500">No data available</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { apiService } from '@/services/api'
import ChartLoading from './ChartLoading.vue'

interface Props {
  chartId: string
  type: 'backup-status' | 'backup-overdue'
  tags?: string[]
  search?: string
  className?: string
}

const props = withDefaults(defineProps<Props>(), {
  tags: () => [],
  search: '',
  className: 'w-full h-64'
})

// Define emits
const emit = defineEmits<{
  segmentClick: [filter: { type: string, value: string }]
}>()

const chartContainer = ref<HTMLElement>()
const loading = ref(true)
const hasData = ref(false)
let chartInstance: any = null

const initChart = async () => {
  loading.value = true
  hasData.value = false

  try {
    // Get chart data from API first
    const chartData = await apiService.getChartData(props.type, {
      tags: props.tags,
      search: props.search
    })

    console.log('Chart data received:', chartData) // Debug log

    // Check if we have data
    if (!chartData.data || chartData.data.length === 0 || chartData.data.every(item => item.value === 0)) {
      hasData.value = false
      loading.value = false
      return
    }

    hasData.value = true
    loading.value = false

    // Wait for next tick to ensure DOM is updated
    await new Promise(resolve => setTimeout(resolve, 0))

    if (!chartContainer.value) {
      console.error('Chart container not found')
      return
    }

    // Lazy load ECharts
    const echarts = await import('echarts')

    // Dispose existing chart instance
    if (chartInstance) {
      chartInstance.dispose()
    }

    // Initialize new chart
    chartInstance = echarts.init(chartContainer.value)

    // Configure chart options based on type
    let option: any = null

    if (props.type === 'backup-status') {
      option = {
        title: {
          text: '',
          left: 'center'
        },
        tooltip: {
          trigger: 'item',
          formatter: '{b}: {c} ({d}%)'
        },
        legend: {
          orient: 'horizontal',
          bottom: '10px',
          left: 'center'
        },
        series: [
          {
            name: 'Backup Status',
            type: 'pie',
            radius: ['40%', '70%'],
            center: ['50%', '45%'],
            avoidLabelOverlap: false,
            itemStyle: {
              borderRadius: 4,
              borderColor: '#fff',
              borderWidth: 2
            },
            label: {
              show: false,
              position: 'center'
            },
            emphasis: {
              label: {
                show: true,
                fontSize: 20,
                fontWeight: 'bold'
              },
              itemStyle: {
                shadowBlur: 10,
                shadowOffsetX: 0,
                shadowColor: 'rgba(0, 0, 0, 0.5)'
              }
            },
            labelLine: {
              show: false
            },
            data: chartData.data.map((item: any) => ({
              value: item.value,
              name: item.name,
              itemStyle: {
                color: getStatusColor(item.name)
              }
            }))
          }
        ]
      }
    } else if (props.type === 'backup-overdue') {
      option = {
        title: {
          text: '',
          left: 'center'
        },
        tooltip: {
          trigger: 'item',
          formatter: '{b}: {c} ({d}%)'
        },
        legend: {
          orient: 'horizontal',
          bottom: '10px',
          left: 'center'
        },
        series: [
          {
            name: 'Schedule Status',
            type: 'pie',
            radius: ['40%', '70%'],
            center: ['50%', '45%'],
            avoidLabelOverlap: false,
            itemStyle: {
              borderRadius: 4,
              borderColor: '#fff',
              borderWidth: 2
            },
            label: {
              show: false,
              position: 'center'
            },
            emphasis: {
              label: {
                show: true,
                fontSize: 20,
                fontWeight: 'bold'
              },
              itemStyle: {
                shadowBlur: 10,
                shadowOffsetX: 0,
                shadowColor: 'rgba(0, 0, 0, 0.5)'
              }
            },
            labelLine: {
              show: false
            },
            data: chartData.data.map((item: any) => ({
              value: item.value,
              name: item.name,
              itemStyle: {
                color: getScheduleColor(item.name)
              }
            }))
          }
        ]
      }
    }

    if (option) {
      chartInstance.setOption(option)
      
      // Add click event handler
      chartInstance.on('click', (params: any) => {
        if (params.data && params.data.name) {
          const segmentName = params.data.name.toLowerCase()
          
          if (props.type === 'backup-status') {
            // Map status names to filter values
            emit('segmentClick', { 
              type: 'status', 
              value: `status-${segmentName}` 
            })
          } else if (props.type === 'backup-overdue') {
            // Map schedule status names to filter values
            let filterValue = ''
            if (segmentName === 'on time') {
              filterValue = 'schedule-on-time'
            } else if (segmentName === 'overdue') {
              filterValue = 'schedule-overdue'
            } else if (segmentName === 'unknown') {
              filterValue = 'schedule-unknown'
            }
            
            if (filterValue) {
              emit('segmentClick', { 
                type: 'status', 
                value: filterValue 
              })
            }
          }
        }
      })
    }

    // Handle resize
    const handleResize = () => {
      if (chartInstance) {
        chartInstance.resize()
      }
    }

    window.addEventListener('resize', handleResize)

    // Store resize handler for cleanup
    ;(chartInstance as any).resizeHandler = handleResize

  } catch (error) {
    console.error('Failed to load chart data:', error)
    hasData.value = false
  } finally {
    loading.value = false
  }
}

const getStatusColor = (status: string): string => {
  switch (status.toLowerCase()) {
    case 'success':
      return '#10b981' // green-500
    case 'failed':
      return '#ef4444' // red-500
    case 'warning':
      return '#f59e0b' // amber-500
    case 'running':
      return '#3b82f6' // blue-500
    case 'unknown':
    default:
      return '#6b7280' // gray-500
  }
}

const getScheduleColor = (status: string): string => {
  const normalized = status.toLowerCase().replace(/[-_ ]/g, '');
  if (normalized === 'ontime') {
    return '#10b981'; // green-500 (same as success)
  }
  if (normalized === 'overdue') {
    return '#ef4444'; // red-500
  }
  if (normalized === 'warning') {
    return '#f59e0b'; // amber-500
  }
  if (normalized === 'noschedule') {
    return '#6b7280'; // gray-500
  }
  return '#6b7280'; // gray-500
}

// Watch for prop changes and reinitialize chart
watch(() => [props.type, props.tags, props.search], initChart, { deep: true })

onMounted(() => {
  initChart()
})

onUnmounted(() => {
  if (chartInstance) {
    // Remove resize handler
    if ((chartInstance as any).resizeHandler) {
      window.removeEventListener('resize', (chartInstance as any).resizeHandler)
    }
    chartInstance.dispose()
  }
})
</script>

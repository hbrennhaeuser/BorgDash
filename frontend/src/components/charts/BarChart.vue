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
  type: string
  tags?: string[]
  search?: string
  className?: string
}

const props = withDefaults(defineProps<Props>(), {
  tags: () => [],
  search: '',
  className: 'w-full h-64'
})

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

    console.log('Bar chart data received:', chartData) // Debug log

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

    // Configure chart options for bar chart
    const option: any = {
      title: {
        text: '',
        left: 'center'
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow'
        }
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: chartData.data.map((item: any) => item.name),
        axisTick: {
          alignWithLabel: true
        }
      },
      yAxis: {
        type: 'value'
      },
      series: [
        {
          name: 'Count',
          type: 'bar',
          barWidth: '60%',
          data: chartData.data.map((item: any) => ({
            value: item.value,
            itemStyle: {
              color: getBarColor(item.name, props.type)
            }
          }))
        }
      ]
    }

    chartInstance.setOption(option)

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

const getBarColor = (name: string, type: string): string => {
  if (type === 'backup-status') {
    switch (name.toLowerCase()) {
      case 'success':
        return '#10b981' // green-500
      case 'failed':
        return '#ef4444' // red-500
      case 'warning':
        return '#f59e0b' // amber-500
      case 'running':
        return '#3b82f6' // blue-500
      default:
        return '#6b7280' // gray-500
    }
  }
  return '#3b82f6' // blue-500 as default
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

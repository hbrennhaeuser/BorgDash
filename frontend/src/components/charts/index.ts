// Chart Components Export
export { default as DonutChart } from './DonutChart.vue'
export { default as BarChart } from './BarChart.vue'
export { default as ChartLoading } from './ChartLoading.vue'

// Chart types that can be used with the API
export type ChartType = 'backup-status' | 'backup-overdue'

// Chart component props interface
export interface ChartProps {
  chartId: string
  type: ChartType | string
  tags?: string[]
  search?: string
  className?: string
}

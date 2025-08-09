<template>
  <div class="min-h-screen bg-gray-50 flex flex-col">
    <AppHeader />
    
    <!-- Add padding for fixed header -->
    <div class="pt-16 flex-1">
      <main class="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div class="px-4 py-6 sm:px-0">
          <!-- Page Header -->
          <div class="mb-8">
            <h1 class="text-3xl ft-bold text-gray-900">Dashboard</h1>
            <p class="mt-2 text-gray-600">Overview of your backup infrastructure</p>
          </div>

          <!-- Chart Grid -->
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <!-- Backup Status Donut Chart -->
            <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h3 class="text-lg font-semibold text-gray-900 mb-4">Backup Status</h3>
              <DonutChart 
                chart-id="backup-status" 
                type="backup-status"
                :tags="[]"
                :search="''"
                class="h-64"
              />
            </div>

            <!-- Backup Overdue Donut Chart -->
            <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h3 class="text-lg font-semibold text-gray-900 mb-4">Backup Schedule Status</h3>
              <DonutChart 
                chart-id="backup-overdue" 
                type="backup-overdue"
                :tags="[]"
                :search="''"
                class="h-64"
              />
            </div>

            <!-- Quick Stats Card -->
            <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h3 class="text-lg font-semibold text-gray-900 mb-4">Quick Stats</h3>
              <div class="space-y-4">
                <div class="flex justify-between items-center">
                  <span class="text-sm text-gray-600">Total Jobs</span>
                  <span class="text-2xl font-bold text-gray-900">{{ totalJobs }}</span>
                </div>
                <div class="flex justify-between items-center">
                  <span class="text-sm text-gray-600">Successful</span>
                  <span class="text-2xl font-bold text-green-600">{{ successfulJobs }}</span>
                </div>
                <div class="flex justify-between items-center">
                  <span class="text-sm text-gray-600">Failed</span>
                  <span class="text-2xl font-bold text-red-600">{{ failedJobs }}</span>
                </div>
                <div class="flex justify-between items-center">
                  <span class="text-sm text-gray-600">Warning</span>
                  <span class="text-2xl font-bold text-yellow-600">{{ warningJobs }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Quick Actions -->
          <div class="mt-8">
            <h2 class="text-xl font-semibold text-gray-900 mb-4">Quick Actions</h2>
            <div class="flex flex-wrap gap-4">
              <RouterLink
                to="/jobs"
                class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
              >
                View All Jobs
              </RouterLink>
              <RouterLink
                to="/jobs/new"
                class="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
              >
                Add New Job
              </RouterLink>
              <RouterLink
                to="/settings"
                class="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
              >
                Settings
              </RouterLink>
            </div>
          </div>
        </div>
      </main>
    </div>
    
    <AppFooter />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import AppHeader from '@/components/AppHeader.vue'
import AppFooter from '@/components/AppFooter.vue'
import DonutChart from '@/components/charts/DonutChart.vue'
import { apiService } from '@/services/api'
import type { Job } from '@/types'

// State
const totalJobs = ref(0)
const successfulJobs = ref(0)
const failedJobs = ref(0)
const warningJobs = ref(0)

// Load dashboard data
const loadDashboardData = async () => {
  try {
    const jobs: Job[] = await apiService.getJobs()
    
    totalJobs.value = jobs.length
    successfulJobs.value = jobs.filter(job => job.status === 'success').length
    failedJobs.value = jobs.filter(job => job.status === 'failed').length
    warningJobs.value = jobs.filter(job => job.status === 'warning').length
  } catch (error) {
    console.error('Failed to load dashboard data:', error)
  }
}

onMounted(() => {
  loadDashboardData()
})
</script>

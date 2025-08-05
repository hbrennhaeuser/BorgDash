<template>
  <header class="fixed top-0 left-0 right-0 z-50 bg-white/80 shadow-sm border-b border-gray-200 backdrop-blur-md supports-[backdrop-filter]:bg-white/75">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex justify-between items-center h-16">
        <!-- Left: Logo/Title -->
        <div class="flex items-center">
          <RouterLink to="/" class="text-2xl font-bold text-gray-900 hover:text-blue-600 transition-colors">
            BorgDash
          </RouterLink>
        </div>
        
        <!-- Right: Action Buttons -->
        <div class="flex items-center space-x-3">
          <!-- User info -->
          <div v-if="currentUser" class="text-sm text-gray-600">
            Welcome, <span class="font-medium">{{ currentUser.username }}</span>
          </div>

          <!-- New Job Button -->
          <RouterLink
            to="/jobs/new"
            class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
          >
            <PlusIcon class="h-4 w-4 mr-2" />
            New Job
          </RouterLink>

          <!-- Refresh Button -->
          <button
            @click="handleRefresh"
            class="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
            title="Refresh all repositories"
            :disabled="refreshing"
          >
            <RefreshIcon :class="['h-4 w-4', { 'animate-spin': refreshing }]" />
          </button>
          
          <!-- Settings Button -->
          <RouterLink
            to="/settings"
            class="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
          >
            <CogIcon class="h-4 w-4" />
          </RouterLink>

          <!-- Logout Button -->
          <button
            @click="handleLogout"
            class="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
            title="Logout"
          >
            <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink, useRouter, useRoute } from 'vue-router'
import PlusIcon from '@/components/icons/PlusIcon.vue'
import CogIcon from '@/components/icons/CogIcon.vue'
import RefreshIcon from '@/components/icons/RefreshIcon.vue'
import { authService, currentUser } from '@/services/auth'

const router = useRouter()
const route = useRoute()
const refreshing = ref(false)

const handleLogout = () => {
  authService.logout()
  router.push('/login')
}

const handleRefresh = async () => {
  if (refreshing.value) return
  
  refreshing.value = true
  
  try {
    // Emit a custom event that can be caught by Dashboard or other components
    if (route.name === 'Dashboard' || route.path === '/') {
      // If we're on the dashboard, emit a global refresh event
      window.dispatchEvent(new CustomEvent('refresh-repositories'))
    }
    
    // Add a small delay to show the animation
    await new Promise(resolve => setTimeout(resolve, 1000))
  } finally {
    refreshing.value = false
  }
}
</script>

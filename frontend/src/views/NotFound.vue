<template>
  <div class="min-h-screen bg-gray-50 flex flex-col">
    <AppHeader />
    
    <!-- Add padding for fixed header -->
    <div class="pt-16 flex-1 flex items-center justify-center">
      <div class="max-w-md mx-auto text-center">
        <div class="mb-8">
          <!-- 404 Icon -->
          <div class="mx-auto flex items-center justify-center h-24 w-24 rounded-full bg-red-100 mb-6">
            <svg class="h-12 w-12 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          
          <!-- Error Message -->
          <h1 class="text-4xl font-bold text-gray-900 mb-4">404</h1>
          <h2 class="text-xl font-semibold text-gray-700 mb-2">Page Not Found</h2>
          <p class="text-gray-600 mb-8">
            Sorry, we couldn't find the page you're looking for. It might have been moved, deleted, or you entered the wrong URL.
          </p>
          
          <!-- Action Buttons -->
          <div class="space-y-3 sm:space-y-0 sm:space-x-3 sm:flex sm:justify-center">
            <RouterLink
              to="/"
              class="w-full sm:w-auto inline-flex items-center justify-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
            >
              <svg class="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
              </svg>
              Go to Dashboard
            </RouterLink>
            
            <RouterLink
              to="/jobs"
              class="w-full sm:w-auto inline-flex items-center justify-center px-6 py-3 border border-gray-300 text-base font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
            >
              <svg class="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
              </svg>
              View Jobs
            </RouterLink>
          </div>
          
          <!-- Help Links -->
          <div class="mt-8 pt-6 border-t border-gray-200">
            <p class="text-sm text-gray-500 mb-4">Need help? Try these common pages:</p>
            <div class="flex flex-wrap justify-center gap-4 text-sm">
              <RouterLink to="/jobs/new" class="text-blue-600 hover:text-blue-800 transition-colors">
                Create New Job
              </RouterLink>
              <RouterLink to="/settings" class="text-blue-600 hover:text-blue-800 transition-colors">
                Settings
              </RouterLink>
              <a href="mailto:support@example.com" class="text-blue-600 hover:text-blue-800 transition-colors">
                Contact Support
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <AppFooter />
  </div>
</template>

<script setup lang="ts">
import { RouterLink } from 'vue-router'
import AppHeader from '@/components/AppHeader.vue'
import AppFooter from '@/components/AppFooter.vue'
</script>

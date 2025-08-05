<template>
  <div class="min-h-screen bg-gray-50 flex flex-col">
    <AppHeader />
    
    <div class="pt-16 flex-1">
      <main class="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div class="px-4 py-6 sm:px-0">
          <div class="text-center py-12">
            <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-8 max-w-md mx-auto">
              <div class="flex items-center justify-center w-16 h-16 mx-auto bg-purple-100 rounded-full mb-4">
                <CogIcon class="text-purple-600" />
              </div>
              <h1 class="text-2xl font-bold text-gray-900 mb-2">Job Settings</h1>
              <p class="text-gray-600 mb-2">
                Settings for job: <span class="font-mono">{{ jobName }}</span>
              </p>
              <p class="text-gray-600 mb-6">
                Job-specific configuration is not yet available in the web interface. Most options are configurable through the configuration files. For further details, please refer to the documentation.
              </p>
              <RouterLink
                to="/"
                class="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 transition-colors"
              >
                Back to Dashboard
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
import { RouterLink } from 'vue-router'
import AppHeader from '@/components/AppHeader.vue'
import AppFooter from '@/components/AppFooter.vue'
import CogIcon from '@/components/icons/CogIcon.vue'

interface Props {
  jobName: string
}

defineProps<Props>()
</script>

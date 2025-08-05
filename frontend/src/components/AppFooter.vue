<template>
  <footer class="bg-gray-50 border-t border-gray-200 mt-16">
    <div class="max-w-7xl mx-auto py-12 px-4 sm:px-6 lg:px-8">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
        <!-- Project Info -->
        <div class="md:col-span-1">
          <div class="flex items-center mb-2">
            <h3 class="text-lg font-bold text-gray-900">BorgDash</h3>
          </div>
          <p class="text-sm text-gray-500 mb-4">Version 1.0.0</p>
          <p class="text-sm text-gray-600 mb-4">
            A modern web dashboard for monitoring Borg and Borgmatic backup operations.
          </p>
          <div class="flex items-center space-x-4">
            <a
              href="https://github.com/hbrennhaeuser/borgdash"
              target="_blank"
              rel="noopener noreferrer"
              class="text-gray-400 hover:text-gray-600 transition-colors"
              title="GitHub Repository"
            >
              <GitHubIcon class="h-5 w-5" />
            </a>
          </div>
        </div>

        <!-- Documentation -->
        <div>
          <h4 class="text-sm font-semibold text-gray-900 uppercase tracking-wider mb-4">Links</h4>
          <ul class="space-y-2">
            <li>
              <a href="https://github.com/hbrennhaeuser/borgdash" target="_blank" rel="noopener noreferrer" class="text-sm text-gray-600 hover:text-gray-900 transition-colors">
                Homepage
              </a>
            </li>
            <li>
              <a href="https://github.com/hbrennhaeuser/borgdash" target="_blank" rel="noopener noreferrer" class="text-sm text-gray-600 hover:text-gray-900 transition-colors">
                Source
              </a>
            </li>
            <li>
              <a href="https://github.com/hbrennhaeuser/borgdash/blob/main/docs/index.md" target="_blank" rel="noopener noreferrer" class="text-sm text-gray-600 hover:text-gray-900 transition-colors">
                Documentation
              </a>
            </li>
          </ul>
        </div>

        <!-- Legal -->
        <div>
          <h4 class="text-sm font-semibold text-gray-900 uppercase tracking-wider mb-4">Legal</h4>
          <ul class="space-y-2">
            <li>
              <a
                href="https://www.gnu.org/licenses/gpl-3.0.html"
                target="_blank"
                rel="noopener noreferrer"
                class="text-sm text-gray-600 hover:text-gray-900 transition-colors"
              >
                GPL v3 License
              </a>
            </li>
            <li>
              <a href="/privacy" class="text-sm text-gray-600 hover:text-gray-900 transition-colors">
                Privacy Policy
              </a>
            </li>
            <li>
              <a href="/terms" class="text-sm text-gray-600 hover:text-gray-900 transition-colors">
                Terms of Service
              </a>
            </li>
          </ul>
        </div>
      </div>

      <!-- Bottom Section -->
      <div class="mt-8 pt-8 border-t border-gray-200">
        <div class="flex flex-col md:flex-row justify-between items-center">
          <div class="flex items-center space-x-4 text-sm text-gray-500">
            <span>© 2025 BorgDash</span>
          </div>
        </div>
      </div>
    </div>
  </footer>
</template>

<script setup lang="ts">
import GitHubIcon from '@/components/icons/GitHubIcon.vue'
</script>

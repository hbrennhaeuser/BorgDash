import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  base: '/ui/',
  plugins: [vue(), tailwindcss()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  build: {
    // Increased chunkSizeWarningLimit to 1200 to allow large ECharts chunk without warning
    // This is intentional: ECharts is lazy-loaded and does not affect initial bundle size
    chunkSizeWarningLimit: 1200,
    rollupOptions: {
      output: {
        manualChunks: {
          // Vue ecosystem
          'vue-vendor': ['vue', 'vue-router'],
          
          // Charts library (separate chunk for lazy loading)
          'echarts': ['echarts'],
          
          // Other vendor libraries
          'vendor': [
            // Add other large dependencies here as needed
          ]
        }
      }
    }
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/push': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})

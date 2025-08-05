import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import './assets/main.css'

// Import views
import Dashboard from './views/Dashboard.vue'
import NewJob from './views/NewJob.vue'
import JobSettings from './views/JobSettings.vue'
import AppSettings from './views/AppSettings.vue'
import Login from './views/Login.vue'

// Import auth service for route guards
import { authService, isAuthenticated } from '@/services/auth'

// Create router
const router = createRouter({
  history: createWebHistory('/ui/'),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: Login,
      meta: { requiresAuth: false }
    },
    {
      path: '/',
      name: 'Dashboard',
      component: Dashboard,
      meta: { requiresAuth: true }
    },
    {
      path: '/jobs/new',
      name: 'NewJob',
      component: NewJob,
      meta: { requiresAuth: true }
    },
    {
      path: '/jobs/:jobName/settings',
      name: 'JobSettings',
      component: JobSettings,
      props: true,
      meta: { requiresAuth: true }
    },
    {
      path: '/settings',
      name: 'AppSettings',
      component: AppSettings,
      meta: { requiresAuth: true }
    }
  ]
})

// Navigation guard for authentication
router.beforeEach(async (to, from, next) => {
  const requiresAuth = to.meta.requiresAuth !== false // Default to requiring auth
  
  if (requiresAuth) {
    // Check if user is authenticated
    if (!isAuthenticated.value) {
      // Try to verify existing token
      const isValid = await authService.verifyToken()
      if (!isValid) {
        // Redirect to login
        next('/login')
        return
      }
    }
  } else if (to.path === '/login' && isAuthenticated.value) {
    // If already authenticated and trying to access login, redirect to dashboard
    next('/')
    return
  }
  
  next()
})

const app = createApp(App)
app.use(router)
app.mount('#app')

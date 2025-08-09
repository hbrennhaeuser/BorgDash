import { createRouter, createWebHistory } from 'vue-router'

// Import auth service for route guards
import { authService, isAuthenticated } from '@/services/auth'

// Create router with lazy-loaded components
const router = createRouter({
  history: createWebHistory('/ui/'),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('./views/Login.vue'),
      meta: { requiresAuth: false }
    },
    {
      path: '/',
      name: 'Dashboard',
      component: () => import('./views/Dashboard.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/jobs',
      name: 'Jobs',
      component: () => import('./views/Jobs.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/jobs/new',
      name: 'NewJob',
      component: () => import('./views/NewJob.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/jobs/:jobName/settings',
      name: 'JobSettings',
      component: () => import('./views/JobSettings.vue'),
      props: true,
      meta: { requiresAuth: true }
    },
    {
      path: '/settings',
      name: 'AppSettings',
      component: () => import('./views/AppSettings.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'NotFound',
      component: () => import('./views/NotFound.vue'),
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

export default router

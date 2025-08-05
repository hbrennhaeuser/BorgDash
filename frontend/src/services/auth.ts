/**
 * Authentication service for BorgDash frontend
 */

import { ref, computed } from 'vue'

interface LoginResponse {
  access_token: string
  token_type: string
  expires_at: string
}

interface User {
  username: string
}

class AuthService {
  private token = ref<string | null>(null)
  private user = ref<User | null>(null)
  private tokenExpiry = ref<Date | null>(null)

  constructor() {
    // Load token from localStorage on initialization
    this.loadTokenFromStorage()
  }

  get isAuthenticated() {
    return computed(() => {
      if (!this.token.value || !this.tokenExpiry.value) {
        return false
      }
      
      // Check if token is expired
      const now = new Date()
      return now < this.tokenExpiry.value
    })
  }

  get currentUser() {
    return computed(() => this.user.value)
  }

  get authToken() {
    return computed(() => this.token.value)
  }

  private loadTokenFromStorage() {
    try {
      const storedToken = localStorage.getItem('borgdash-token')
      const storedExpiry = localStorage.getItem('borgdash-token-expiry')
      const storedUser = localStorage.getItem('borgdash-user')

      if (storedToken && storedExpiry && storedUser) {
        const expiryDate = new Date(storedExpiry)
        const now = new Date()

        // Only load if token hasn't expired
        if (now < expiryDate) {
          this.token.value = storedToken
          this.tokenExpiry.value = expiryDate
          this.user.value = JSON.parse(storedUser)
        } else {
          // Clear expired token
          this.clearTokenFromStorage()
        }
      }
    } catch (error) {
      console.error('Error loading token from storage:', error)
      this.clearTokenFromStorage()
    }
  }

  private saveTokenToStorage(token: string, expiresAt: string, username: string) {
    try {
      localStorage.setItem('borgdash-token', token)
      localStorage.setItem('borgdash-token-expiry', expiresAt)
      localStorage.setItem('borgdash-user', JSON.stringify({ username }))
    } catch (error) {
      console.error('Error saving token to storage:', error)
    }
  }

  private clearTokenFromStorage() {
    localStorage.removeItem('borgdash-token')
    localStorage.removeItem('borgdash-token-expiry')
    localStorage.removeItem('borgdash-user')
  }

  async login(username: string, password: string): Promise<boolean> {
    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      })

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error('Invalid credentials')
        }
        throw new Error(`Login failed: ${response.statusText}`)
      }

      const data: LoginResponse = await response.json()
      
      // Store token and user info
      this.token.value = data.access_token
      this.tokenExpiry.value = new Date(data.expires_at)
      this.user.value = { username }
      
      // Save to localStorage
      this.saveTokenToStorage(data.access_token, data.expires_at, username)

      return true
    } catch (error) {
      console.error('Login error:', error)
      throw error
    }
  }

  logout() {
    this.token.value = null
    this.tokenExpiry.value = null
    this.user.value = null
    this.clearTokenFromStorage()
  }

  async verifyToken(): Promise<boolean> {
    if (!this.token.value) {
      return false
    }

    try {
      const response = await fetch('/api/auth/verify', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.token.value}`,
        },
      })

      if (!response.ok) {
        // Token is invalid, clear it
        this.logout()
        return false
      }

      return true
    } catch (error) {
      console.error('Token verification error:', error)
      this.logout()
      return false
    }
  }

  getAuthHeaders(): Record<string, string> {
    if (!this.token.value) {
      return {}
    }

    return {
      'Authorization': `Bearer ${this.token.value}`,
    }
  }
}

// Create and export singleton instance
export const authService = new AuthService()

// Export reactive computed properties for use in components
export const isAuthenticated = authService.isAuthenticated
export const currentUser = authService.currentUser

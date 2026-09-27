import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../services/api'
import router from '../router'

export interface User {
  id: string
  email: string
  full_name: string
  role: 'Administrator' | 'Clinician' | 'Lab_Officer' | 'Auditor'
  is_active: boolean
  created_at: string
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const accessToken = ref<string | null>(localStorage.getItem('pm_access_token'))
  const refreshToken = ref<string | null>(localStorage.getItem('pm_refresh_token'))
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Initialize cached user if available
  const storedUser = localStorage.getItem('pm_user')
  if (storedUser) {
    try {
      user.value = JSON.parse(storedUser)
    } catch {
      localStorage.removeItem('pm_user')
    }
  }

  // Role permissions
  const isAuthenticated = computed(() => !!accessToken.value && !!user.value)
  const userRole = computed(() => user.value?.role || '')
  const isAdmin = computed(() => user.value?.role === 'Administrator')
  const isClinician = computed(() => user.value?.role === 'Clinician')
  const isLabOfficer = computed(() => user.value?.role === 'Lab_Officer')
  const isAuditor = computed(() => user.value?.role === 'Auditor')
  const canViewClinicalCharts = computed(() => user.value?.role !== 'Auditor')
  const canModifyGenomics = computed(() => user.value?.role === 'Lab_Officer' || user.value?.role === 'Administrator')
  const canAcknowledgeAlerts = computed(() => user.value?.role === 'Clinician' || user.value?.role === 'Administrator')

  async function login(email: string, password: string) {
    loading.value = true
    error.value = null
    try {
      const response = await api.post('/auth/login', { email, password })
      const data = response.data

      accessToken.value = data.access_token
      refreshToken.value = data.refresh_token
      user.value = data.user

      localStorage.setItem('pm_access_token', data.access_token)
      localStorage.setItem('pm_refresh_token', data.refresh_token)
      localStorage.setItem('pm_user', JSON.stringify(data.user))

      // Navigate based on role
      if (isAuditor.value) {
        await router.push('/audit')
      } else if (isLabOfficer.value) {
        await router.push('/lab-ingest')
      } else {
        await router.push('/')
      }
      return true
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Authentication failed. Please check credentials.'
      return false
    } finally {
      loading.value = false
    }
  }

  async function logout() {
    try {
      if (accessToken.value) {
        await api.post('/auth/logout').catch(() => {})
      }
    } finally {
      user.value = null
      accessToken.value = null
      refreshToken.value = null
      localStorage.removeItem('pm_access_token')
      localStorage.removeItem('pm_refresh_token')
      localStorage.removeItem('pm_user')
      await router.push('/login')
    }
  }

  async function fetchCurrentUser() {
    if (!accessToken.value) return null
    try {
      const response = await api.get('/auth/me')
      user.value = response.data
      localStorage.setItem('pm_user', JSON.stringify(response.data))
      return user.value
    } catch {
      await logout()
      return null
    }
  }

  return {
    user,
    accessToken,
    refreshToken,
    loading,
    error,
    isAuthenticated,
    userRole,
    isAdmin,
    isClinician,
    isLabOfficer,
    isAuditor,
    canViewClinicalCharts,
    canModifyGenomics,
    canAcknowledgeAlerts,
    login,
    logout,
    fetchCurrentUser,
  }
})

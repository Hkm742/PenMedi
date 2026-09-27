import axios from 'axios'

// Base axios instance with fallback to proxied /api/v1 or env URL
export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
})

let isRefreshing = false
let failedQueue: Array<{
  resolve: (value?: unknown) => void
  reject: (reason?: unknown) => void
}> = []

const processQueue = (error: unknown, token: string | null = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error)
    } else {
      prom.resolve(token)
    }
  })
  failedQueue = []
}

// Request interceptor: attach JWT access token
api.interceptors.request.use(
  config => {
    const token = localStorage.getItem('pm_access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => Promise.reject(error)
)

// Response interceptor: handle 401 refresh flow
api.interceptors.response.use(
  response => response,
  async error => {
    const originalRequest = error.config

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (originalRequest.url?.includes('/auth/login') || originalRequest.url?.includes('/auth/refresh')) {
        return Promise.reject(error)
      }

      const refreshToken = localStorage.getItem('pm_refresh_token')
      if (!refreshToken) {
        localStorage.removeItem('pm_access_token')
        localStorage.removeItem('pm_user')
        window.location.href = '/login'
        return Promise.reject(error)
      }

      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        })
          .then(token => {
            originalRequest.headers.Authorization = `Bearer ${token}`
            return api(originalRequest)
          })
          .catch(err => Promise.reject(err))
      }

      originalRequest._retry = true
      isRefreshing = true

      try {
        const response = await axios.post(
          `${import.meta.env.VITE_API_URL || '/api/v1'}/auth/refresh`,
          { refresh_token: refreshToken }
        )
        const { access_token, refresh_token: new_refresh } = response.data

        localStorage.setItem('pm_access_token', access_token)
        localStorage.setItem('pm_refresh_token', new_refresh)

        api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
        originalRequest.headers['Authorization'] = `Bearer ${access_token}`

        processQueue(null, access_token)
        return api(originalRequest)
      } catch (refreshErr) {
        processQueue(refreshErr, null)
        localStorage.removeItem('pm_access_token')
        localStorage.removeItem('pm_refresh_token')
        localStorage.removeItem('pm_user')
        window.location.href = '/login'
        return Promise.reject(refreshErr)
      } finally {
        isRefreshing = false
      }
    }

    return Promise.reject(error)
  }
)

export default api

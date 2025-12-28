import axios from 'axios'

const apiClient = axios.create({
  baseURL: (import.meta as any).env?.VITE_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
})

// Track if we're currently refreshing to avoid multiple simultaneous refresh requests
let isRefreshing = false
let failedQueue: Array<{
  resolve: (value?: any) => void
  reject: (reason?: any) => void
}> = []

const processQueue = (error: any = null, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error)
    } else {
      prom.resolve(token)
    }
  })

  failedQueue = []
}

// Request interceptor - add JWT token to all requests
apiClient.interceptors.request.use(
  (config) => {
    // Add access token if available
    const accessToken = localStorage.getItem('access_token')
    if (accessToken) {
      config.headers.Authorization = `Bearer ${accessToken}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor - handle token refresh on 401
apiClient.interceptors.response.use(
  (response) => response.data,
  async (error) => {
    const originalRequest = error.config

    // If error is 401 and we haven't tried to refresh yet
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        // If already refreshing, queue this request
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        })
          .then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`
            return apiClient(originalRequest)
          })
          .catch((err) => Promise.reject(err))
      }

      originalRequest._retry = true
      isRefreshing = true

      const refreshToken = localStorage.getItem('refresh_token')

      if (!refreshToken) {
        // No refresh token, redirect to login
        window.location.href = '/login'
        return Promise.reject(error)
      }

      try {
        // Call refresh endpoint
        const response = await axios.post(
          `${apiClient.defaults.baseURL}/api/auth/refresh`,
          { refresh_token: refreshToken },
          {
            headers: { 'Content-Type': 'application/json' },
          }
        )

        const { access_token, refresh_token: newRefreshToken } = response.data

        // Store new tokens
        localStorage.setItem('access_token', access_token)
        localStorage.setItem('refresh_token', newRefreshToken)

        // Update authorization header
        apiClient.defaults.headers.common.Authorization = `Bearer ${access_token}`
        originalRequest.headers.Authorization = `Bearer ${access_token}`

        // Process queued requests
        processQueue(null, access_token)

        isRefreshing = false

        // Retry original request with new token
        return apiClient(originalRequest)
      } catch (refreshError) {
        processQueue(refreshError, null)
        isRefreshing = false

        // Refresh failed, clear tokens and redirect to login
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        window.location.href = '/login'

        return Promise.reject(refreshError)
      }
    }

    // Extract error message
    const message = error.response?.data?.detail || error.message
    return Promise.reject(new Error(message))
  }
)

export default apiClient

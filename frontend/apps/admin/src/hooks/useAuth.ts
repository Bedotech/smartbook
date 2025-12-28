import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiClient } from '@smartbook/api'

export interface User {
  id: string
  email: string
  name: string
  role: 'admin' | 'staff'
  picture_url?: string
  property_ids: string[]
}

interface UseAuthReturn {
  user: User | null
  loading: boolean
  error: string | null
  login: (accessToken: string, refreshToken: string) => void
  logout: () => void
  refreshAccessToken: () => Promise<boolean>
  isAuthenticated: boolean
}

export function useAuth(): UseAuthReturn {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()

  // Decode JWT to extract user info
  const decodeToken = useCallback((token: string): User | null => {
    try {
      const base64Url = token.split('.')[1]
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/')
      const jsonPayload = decodeURIComponent(
        atob(base64)
          .split('')
          .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      )

      const payload = JSON.parse(jsonPayload)

      return {
        id: payload.sub,
        email: payload.email,
        name: payload.name,
        role: payload.role,
        picture_url: payload.picture_url,
        property_ids: payload.property_ids || [],
      }
    } catch (err) {
      console.error('Failed to decode token:', err)
      return null
    }
  }, [])

  // Check if token is expired
  const isTokenExpired = useCallback((token: string): boolean => {
    try {
      const base64Url = token.split('.')[1]
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/')
      const jsonPayload = decodeURIComponent(
        atob(base64)
          .split('')
          .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      )

      const payload = JSON.parse(jsonPayload)
      const expirationTime = payload.exp * 1000 // Convert to milliseconds

      // Token is expired if expiration time is in the past
      return Date.now() >= expirationTime
    } catch (err) {
      console.error('Failed to check token expiration:', err)
      return true // Treat as expired if we can't decode it
    }
  }, [])

  // Refresh access token using refresh token
  const refreshAccessToken = useCallback(async (): Promise<boolean> => {
    const refreshToken = localStorage.getItem('refresh_token')

    if (!refreshToken) {
      return false
    }

    try {
      const response = await apiClient.post<{
        access_token: string
        refresh_token: string
        user: {
          id: string
          email: string
          name: string
          role: 'admin' | 'staff'
          picture_url?: string
          property_ids: string[]
        }
      }>('/api/auth/refresh', {
        refresh_token: refreshToken,
      })

      const { access_token, refresh_token: newRefreshToken, user: userData } = response as any

      // Store new tokens
      localStorage.setItem('access_token', access_token)
      localStorage.setItem('refresh_token', newRefreshToken)

      // Update user state
      setUser({
        id: userData.id,
        email: userData.email,
        name: userData.name,
        role: userData.role,
        picture_url: userData.picture_url,
        property_ids: userData.property_ids,
      })

      return true
    } catch (err) {
      console.error('Token refresh failed:', err)
      // Clear tokens on refresh failure
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      setUser(null)
      return false
    }
  }, [])

  // Login with tokens (called after OAuth callback)
  const login = useCallback(
    (accessToken: string, refreshToken: string) => {
      localStorage.setItem('access_token', accessToken)
      localStorage.setItem('refresh_token', refreshToken)

      const userData = decodeToken(accessToken)
      if (userData) {
        setUser(userData)
        setError(null)
      } else {
        setError('Invalid token')
      }
    },
    [decodeToken]
  )

  // Logout
  const logout = useCallback(() => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    setUser(null)
    navigate('/login')
  }, [navigate])

  // Check authentication status on mount
  useEffect(() => {
    const checkAuth = async () => {
      const accessToken = localStorage.getItem('access_token')

      if (!accessToken) {
        setLoading(false)
        return
      }

      // Check if access token is expired
      if (isTokenExpired(accessToken)) {
        // Try to refresh
        const refreshed = await refreshAccessToken()
        setLoading(false)

        if (!refreshed) {
          // Redirect to login if refresh failed
          navigate('/login')
        }
      } else {
        // Token is valid, decode and set user
        const userData = decodeToken(accessToken)
        if (userData) {
          setUser(userData)
        } else {
          // Invalid token, try to refresh
          const refreshed = await refreshAccessToken()
          if (!refreshed) {
            navigate('/login')
          }
        }
        setLoading(false)
      }
    }

    checkAuth()
  }, [decodeToken, isTokenExpired, refreshAccessToken, navigate])

  return {
    user,
    loading,
    error,
    login,
    logout,
    refreshAccessToken,
    isAuthenticated: !!user,
  }
}

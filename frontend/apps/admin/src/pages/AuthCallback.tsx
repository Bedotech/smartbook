import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Loader2, AlertCircle } from 'lucide-react'
import { useAuth } from '../hooks/useAuth'

export default function AuthCallback() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    // Extract tokens from URL hash (format: #access_token=...&refresh_token=...&token_type=bearer)
    const hash = window.location.hash.substring(1) // Remove the #
    const params = new URLSearchParams(hash)

    const accessToken = params.get('access_token')
    const refreshToken = params.get('refresh_token')
    const tokenType = params.get('token_type')

    if (!accessToken || !refreshToken) {
      setError('Authentication failed. Missing tokens.')
      return
    }

    if (tokenType !== 'bearer') {
      setError('Invalid token type received.')
      return
    }

    // Store tokens and update auth state
    login(accessToken, refreshToken)

    // Clear URL hash for security
    window.history.replaceState(null, '', window.location.pathname)

    // Redirect to dashboard after short delay
    setTimeout(() => {
      navigate('/', { replace: true })
    }, 500)
  }, [login, navigate])

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
        <div className="max-w-md w-full">
          <div className="bg-white rounded-2xl shadow-xl p-8 text-center">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-red-100 rounded-full mb-4">
              <AlertCircle className="w-8 h-8 text-red-600" />
            </div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">
              Authentication Failed
            </h1>
            <p className="text-gray-600 mb-6">{error}</p>
            <button
              onClick={() => navigate('/login')}
              className="w-full bg-gray-900 text-white rounded-lg px-6 py-3 font-medium hover:bg-gray-800 transition-colors"
            >
              Return to Login
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="text-center">
        <Loader2 className="w-12 h-12 animate-spin text-gray-900 mx-auto mb-4" />
        <h2 className="text-xl font-semibold text-gray-900 mb-2">
          Completing sign in...
        </h2>
        <p className="text-gray-600">
          Please wait while we set up your session
        </p>
      </div>
    </div>
  )
}

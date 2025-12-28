import { Component, ReactNode } from 'react'
import { AlertCircle } from 'lucide-react'
import { Button } from '@smartbook/ui'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: unknown) {
    console.error('ErrorBoundary caught error:', error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
          <div className="max-w-md w-full text-center">
            <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
            <h2 className="text-xl font-bold text-gray-900 mb-2">Something went wrong</h2>
            <p className="text-gray-600 mb-2">
              {this.state.error?.message || 'An unexpected error occurred'}
            </p>
            <p className="text-sm text-gray-500 mb-6">Please try refreshing the page</p>
            <Button onClick={() => window.location.reload()} variant="primary" fullWidth>
              Reload Page
            </Button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Suspense, lazy } from 'react'
import { Loader2 } from 'lucide-react'

// Lazy load pages for code splitting
const CheckInPage = lazy(() => import('./pages/CheckInPage'))
const LeaderFormPage = lazy(() => import('./pages/LeaderFormPage'))
const MemberListPage = lazy(() => import('./pages/MemberListPage'))
const SuccessPage = lazy(() => import('./pages/SuccessPage'))
const NotFoundPage = lazy(() => import('./pages/NotFoundPage'))

function LoadingSpinner() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
    </div>
  )
}

function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<LoadingSpinner />}>
        <Routes>
          <Route path="/s/:token" element={<CheckInPage />} />
          <Route path="/s/:token/leader" element={<LeaderFormPage />} />
          <Route path="/s/:token/members" element={<MemberListPage />} />
          <Route path="/s/:token/success" element={<SuccessPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  )
}

export default App

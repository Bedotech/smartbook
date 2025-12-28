import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Suspense, lazy } from 'react'
import { Loader2 } from 'lucide-react'

const Dashboard = lazy(() => import('./pages/Dashboard'))
const BookingsList = lazy(() => import('./pages/BookingsList'))
const NewBooking = lazy(() => import('./pages/NewBooking'))
const BookingDetail = lazy(() => import('./pages/BookingDetail'))
const TaxReports = lazy(() => import('./pages/TaxReports'))
const Settings = lazy(() => import('./pages/Settings'))

function LoadingSpinner() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <Loader2 className="w-8 h-8 animate-spin text-gray-900" />
    </div>
  )
}

function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<LoadingSpinner />}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/bookings" element={<BookingsList />} />
          <Route path="/bookings/new" element={<NewBooking />} />
          <Route path="/bookings/:id" element={<BookingDetail />} />
          <Route path="/tax/reports" element={<TaxReports />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  )
}

export default App

import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Suspense, lazy } from 'react'
import { Loader2 } from 'lucide-react'
import ProtectedRoute from './components/ProtectedRoute'
import Login from './pages/Login'
import AuthCallback from './pages/AuthCallback'
import { PropertyProvider } from './contexts/PropertyContext'

const Dashboard = lazy(() => import('./pages/Dashboard'))
const BookingsList = lazy(() => import('./pages/BookingsList'))
const NewBooking = lazy(() => import('./pages/NewBooking'))
const BookingDetail = lazy(() => import('./pages/BookingDetail'))
const TaxReports = lazy(() => import('./pages/TaxReports'))
const Settings = lazy(() => import('./pages/Settings'))
const UserManagement = lazy(() => import('./pages/UserManagement'))
const PropertiesList = lazy(() => import('./pages/PropertiesList'))
const CreateProperty = lazy(() => import('./pages/CreateProperty'))
const EditProperty = lazy(() => import('./pages/EditProperty'))
const PropertyDetail = lazy(() => import('./pages/PropertyDetail'))

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
      <PropertyProvider>
        <Suspense fallback={<LoadingSpinner />}>
          <Routes>
          {/* Public routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/auth/callback" element={<AuthCallback />} />

          {/* Protected routes */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/bookings"
            element={
              <ProtectedRoute>
                <BookingsList />
              </ProtectedRoute>
            }
          />
          <Route
            path="/bookings/new"
            element={
              <ProtectedRoute>
                <NewBooking />
              </ProtectedRoute>
            }
          />
          <Route
            path="/bookings/:id"
            element={
              <ProtectedRoute>
                <BookingDetail />
              </ProtectedRoute>
            }
          />
          <Route
            path="/tax/reports"
            element={
              <ProtectedRoute>
                <TaxReports />
              </ProtectedRoute>
            }
          />
          <Route
            path="/settings"
            element={
              <ProtectedRoute>
                <Settings />
              </ProtectedRoute>
            }
          />
          <Route
            path="/users"
            element={
              <ProtectedRoute>
                <UserManagement />
              </ProtectedRoute>
            }
          />
          <Route
            path="/properties"
            element={
              <ProtectedRoute>
                <PropertiesList />
              </ProtectedRoute>
            }
          />
          <Route
            path="/properties/new"
            element={
              <ProtectedRoute>
                <CreateProperty />
              </ProtectedRoute>
            }
          />
          <Route
            path="/properties/:id"
            element={
              <ProtectedRoute>
                <PropertyDetail />
              </ProtectedRoute>
            }
          />
          <Route
            path="/properties/:id/edit"
            element={
              <ProtectedRoute>
                <EditProperty />
              </ProtectedRoute>
            }
          />
        </Routes>
      </Suspense>
      </PropertyProvider>
    </BrowserRouter>
  )
}

export default App

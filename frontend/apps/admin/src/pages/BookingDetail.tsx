import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import {
  ArrowLeft,
  Users,
  Send,
  XCircle,
  Calculator,
  Loader2,
  AlertCircle,
  CheckCircle,
  Copy,
  ExternalLink,
} from 'lucide-react'
import { adminApi } from '@smartbook/api'
import type { Booking, Guest, TaxCalculationResult, BookingProgress } from '@smartbook/types'
import Layout from '../components/Layout'
import { useProperty } from '../contexts/PropertyContext'

export default function BookingDetail() {
  const { id } = useParams<{ id: string }>()
  const { selectedPropertyId } = useProperty()
  const [booking, setBooking] = useState<Booking | null>(null)
  const [guests, setGuests] = useState<Guest[]>([])
  const [progress, setProgress] = useState<BookingProgress | null>(null)
  const [taxResult, setTaxResult] = useState<TaxCalculationResult | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    if (id && selectedPropertyId) {
      loadBookingDetails()
    }
  }, [id, selectedPropertyId])

  const loadBookingDetails = async () => {
    if (!id || !selectedPropertyId) return

    try {
      setLoading(true)
      setError(null)
      const [bookingData, guestsData, progressData] = await Promise.all([
        adminApi.getBooking(selectedPropertyId, id),
        adminApi.getGuests(selectedPropertyId, id),
        adminApi.getBookingProgress(selectedPropertyId, id),
      ])
      setBooking(bookingData)
      setGuests(guestsData)
      setProgress(progressData)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load booking details')
    } finally {
      setLoading(false)
    }
  }

  const handleCalculateTax = async () => {
    if (!id || !selectedPropertyId) return

    try {
      setSubmitting(true)
      const result = await adminApi.calculateTax(selectedPropertyId, id)
      setTaxResult(result)
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to calculate tax')
    } finally {
      setSubmitting(false)
    }
  }

  const handleSubmitROS1000 = async () => {
    if (!id || !selectedPropertyId) return
    if (!confirm('Submit this booking to ROS1000?')) return

    try {
      setSubmitting(true)
      await adminApi.submitROS1000(selectedPropertyId, id)
      alert('Successfully submitted to ROS1000')
      loadBookingDetails()
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to submit to ROS1000')
    } finally {
      setSubmitting(false)
    }
  }

  const handleCancelROS1000 = async () => {
    if (!id || !selectedPropertyId) return
    if (!confirm('Cancel this booking in ROS1000?')) return

    try {
      setSubmitting(true)
      await adminApi.cancelROS1000(selectedPropertyId, id)
      alert('Successfully cancelled in ROS1000')
      loadBookingDetails()
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to cancel ROS1000')
    } finally {
      setSubmitting(false)
    }
  }

  const copyMagicLink = () => {
    if (!booking) return
    const guestPortalUrl = window.location.origin.replace(':3001', ':3000')
    const link = `${guestPortalUrl}/s/${booking.magic_link_token}`
    navigator.clipboard.writeText(link)
    alert('Magic link copied to clipboard!')
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('it-IT', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    })
  }

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString('it-IT')
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200'
      case 'in_progress':
        return 'bg-blue-100 text-blue-800 border-blue-200'
      case 'complete':
        return 'bg-green-100 text-green-800 border-green-200'
      case 'synced':
        return 'bg-purple-100 text-purple-800 border-purple-200'
      case 'error':
        return 'bg-red-100 text-red-800 border-red-200'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  const getRoleLabel = (role: string) => {
    switch (role) {
      case 'leader':
        return 'Group Leader'
      case 'member':
        return 'Member'
      case 'bus_driver':
        return 'Bus Driver'
      case 'tour_guide':
        return 'Tour Guide'
      default:
        return role
    }
  }

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-64">
          <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
        </div>
      </Layout>
    )
  }

  if (error || !booking) {
    return (
      <Layout>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex">
            <AlertCircle className="h-5 w-5 text-red-400" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error loading booking</h3>
              <p className="mt-1 text-sm text-red-700">{error || 'Booking not found'}</p>
              <div className="mt-4">
                <Link
                  to="/bookings"
                  className="text-sm font-medium text-red-600 hover:text-red-500"
                >
                  Back to bookings
                </Link>
              </div>
            </div>
          </div>
        </div>
      </Layout>
    )
  }

  return (
    <Layout>
      {/* Header */}
      <div className="mb-8">
        <Link
          to="/bookings"
          className="inline-flex items-center text-sm text-gray-500 hover:text-gray-700 mb-4"
        >
          <ArrowLeft className="w-4 h-4 mr-1" />
          Back to bookings
        </Link>

        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Booking Details</h2>
            <p className="mt-1 text-sm text-gray-500 font-mono">{booking.id}</p>
          </div>
          <span
            className={`px-4 py-2 text-sm font-semibold rounded-full border ${getStatusColor(
              booking.status
            )}`}
          >
            {booking.status.replace('_', ' ').toUpperCase()}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Booking Info */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Booking Information</h3>
            </div>
            <div className="p-6">
              <dl className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <dt className="text-sm font-medium text-gray-500">Type</dt>
                  <dd className="mt-1 text-sm text-gray-900 capitalize">{booking.booking_type}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Expected Guests</dt>
                  <dd className="mt-1 text-sm text-gray-900">{booking.expected_guests}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Check-in Date</dt>
                  <dd className="mt-1 text-sm text-gray-900">{formatDate(booking.check_in_date)}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Check-out Date</dt>
                  <dd className="mt-1 text-sm text-gray-900">{formatDate(booking.check_out_date)}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Created</dt>
                  <dd className="mt-1 text-sm text-gray-900">{formatDateTime(booking.created_at)}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Last Updated</dt>
                  <dd className="mt-1 text-sm text-gray-900">{formatDateTime(booking.updated_at)}</dd>
                </div>
                {booking.ros1000_receipt_number && (
                  <div className="md:col-span-2">
                    <dt className="text-sm font-medium text-gray-500">ROS1000 Receipt</dt>
                    <dd className="mt-1 text-sm text-gray-900 font-mono">
                      {booking.ros1000_receipt_number}
                    </dd>
                  </div>
                )}
                {booking.notes && (
                  <div className="md:col-span-2">
                    <dt className="text-sm font-medium text-gray-500">Notes</dt>
                    <dd className="mt-1 text-sm text-gray-900">{booking.notes}</dd>
                  </div>
                )}
              </dl>
            </div>
          </div>

          {/* Progress */}
          {progress && (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900">Completion Progress</h3>
              </div>
              <div className="p-6">
                <div className="mb-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-gray-700">
                      {progress.current_guest_count} of {progress.expected_guests} guests entered
                    </span>
                    <span className="text-sm font-medium text-primary-600">
                      {progress.completion_percentage}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-3">
                    <div
                      className="bg-primary-600 h-3 rounded-full transition-all duration-500"
                      style={{ width: `${progress.completion_percentage}%` }}
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="flex items-center">
                    {progress.has_leader ? (
                      <CheckCircle className="w-5 h-5 text-green-500 mr-2" />
                    ) : (
                      <AlertCircle className="w-5 h-5 text-yellow-500 mr-2" />
                    )}
                    <span className="text-sm text-gray-700">
                      {progress.has_leader ? 'Has Leader' : 'No Leader Yet'}
                    </span>
                  </div>
                  <div className="flex items-center">
                    {progress.status === 'complete' ? (
                      <CheckCircle className="w-5 h-5 text-green-500 mr-2" />
                    ) : (
                      <AlertCircle className="w-5 h-5 text-yellow-500 mr-2" />
                    )}
                    <span className="text-sm text-gray-700">
                      {progress.status === 'complete' ? 'Complete' : 'In Progress'}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Guests List */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900">Guests ({guests.length})</h3>
            </div>
            {guests.length === 0 ? (
              <div className="p-8 text-center">
                <Users className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                <p className="text-gray-500">No guests have entered their information yet</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Name
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Role
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Date of Birth
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Citizenship
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Tax Exempt
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {guests.map((guest) => (
                      <tr key={guest.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium text-gray-900">
                            {guest.first_name} {guest.last_name}
                          </div>
                          <div className="text-xs text-gray-500">{guest.sex}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className="text-sm text-gray-900">{getRoleLabel(guest.role)}</span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {formatDate(guest.date_of_birth)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {guest.citizenship_country_code}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          {guest.is_tax_exempt ? (
                            <CheckCircle className="w-5 h-5 text-green-500" />
                          ) : (
                            <XCircle className="w-5 h-5 text-gray-300" />
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Tax Calculation */}
          {taxResult && (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900">Tax Calculation</h3>
              </div>
              <div className="p-6">
                <div className="mb-6 grid grid-cols-3 gap-4">
                  <div>
                    <p className="text-sm text-gray-500">Total Tax</p>
                    <p className="text-2xl font-bold text-gray-900">
                      €{taxResult.total_tax.toFixed(2)}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Taxable Nights</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {taxResult.total_taxable_nights}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Exempt Nights</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {taxResult.total_exempt_nights}
                    </p>
                  </div>
                </div>

                {taxResult.guest_breakdown.length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium text-gray-700 mb-3">Guest Breakdown</h4>
                    <div className="space-y-2">
                      {taxResult.guest_breakdown.map((gb) => (
                        <div
                          key={gb.guest_id}
                          className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                        >
                          <div>
                            <p className="text-sm font-medium text-gray-900">{gb.guest_name}</p>
                            <p className="text-xs text-gray-500">
                              {gb.taxable_nights} taxable / {gb.exempt_nights} exempt nights
                              {gb.exemption_reason && ` - ${gb.exemption_reason}`}
                            </p>
                          </div>
                          <span className="text-sm font-semibold text-gray-900">
                            €{gb.tax_amount.toFixed(2)}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Sidebar Actions */}
        <div className="space-y-6">
          {/* Quick Actions */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Actions</h3>
            </div>
            <div className="p-6 space-y-3">
              <button
                onClick={copyMagicLink}
                className="w-full inline-flex items-center justify-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
              >
                <Copy className="w-4 h-4 mr-2" />
                Copy Magic Link
              </button>

              <button
                onClick={handleCalculateTax}
                disabled={submitting || guests.length === 0}
                className="w-full inline-flex items-center justify-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Calculator className="w-4 h-4 mr-2" />
                Calculate Tax
              </button>

              <button
                onClick={handleSubmitROS1000}
                disabled={submitting || progress?.status !== 'complete'}
                className="w-full inline-flex items-center justify-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {submitting ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <Send className="w-4 h-4 mr-2" />
                )}
                Submit to ROS1000
              </button>

              {booking.ros1000_receipt_number && (
                <button
                  onClick={handleCancelROS1000}
                  disabled={submitting}
                  className="w-full inline-flex items-center justify-center px-4 py-2 border border-red-300 rounded-md shadow-sm text-sm font-medium text-red-700 bg-white hover:bg-red-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <XCircle className="w-4 h-4 mr-2" />
                  Cancel ROS1000
                </button>
              )}
            </div>
          </div>

          {/* Magic Link Info */}
          <div className="bg-primary-50 rounded-lg border border-primary-200 p-6">
            <div className="flex items-start">
              <ExternalLink className="w-5 h-5 text-primary-600 mt-0.5 mr-3" />
              <div>
                <h4 className="text-sm font-medium text-primary-900 mb-1">Guest Check-in Link</h4>
                <p className="text-xs text-primary-700 mb-3">
                  Share this link with guests to collect their information
                </p>
                <div className="bg-white rounded border border-primary-300 p-2 break-all text-xs font-mono text-gray-700">
                  {window.location.origin.replace(':3001', ':3000')}/s/{booking.magic_link_token}
                </div>
                <p className="text-xs text-primary-600 mt-2">
                  Expires: {formatDate(booking.token_expires_at)}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  )
}

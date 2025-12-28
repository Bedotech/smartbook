import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Calendar, Users, Search, Download, Loader2, ArrowRight } from 'lucide-react'
import { adminApi } from '@smartbook/api'
import { Card, CardContent, Badge, Button, Input } from '@smartbook/ui'
import type { Booking, BookingStatus } from '@smartbook/types'
import Layout from '../components/Layout'
import { useProperty } from '../contexts/PropertyContext'

export default function BookingsList() {
  const { selectedPropertyId } = useProperty()
  const [bookings, setBookings] = useState<Booking[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [activeTab, setActiveTab] = useState<'all' | BookingStatus>('all')

  useEffect(() => {
    if (selectedPropertyId) {
      loadBookings()
    } else {
      // No property selected, stop loading
      setLoading(false)
    }
  }, [selectedPropertyId])

  const loadBookings = async () => {
    if (!selectedPropertyId) return

    try {
      setLoading(true)
      const data = await adminApi.getBookings(selectedPropertyId, {})
      setBookings(data)
    } catch (err) {
      console.error('Failed to load bookings:', err)
    } finally {
      setLoading(false)
    }
  }

  const getStatusVariant = (status: string) => {
    switch (status) {
      case 'pending':
        return 'warning'
      case 'in_progress':
        return 'info'
      case 'complete':
        return 'success'
      case 'synced':
        return 'purple'
      case 'error':
        return 'error'
      default:
        return 'default'
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('it-IT', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
    })
  }

  const handleExport = () => {
    const csv = [
      ['ID', 'Type', 'Check-in', 'Check-out', 'Guests', 'Status'].join(','),
      ...filteredBookings.map((b) =>
        [
          b.id,
          b.booking_type,
          b.check_in_date,
          b.check_out_date,
          b.expected_guests,
          b.status,
        ].join(',')
      ),
    ].join('\n')

    const blob = new Blob([csv], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `bookings-${new Date().toISOString()}.csv`
    a.click()
  }

  const filteredBookings = bookings.filter((booking) => {
    const matchesSearch =
      searchTerm === '' ||
      booking.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      booking.booking_type.toLowerCase().includes(searchTerm.toLowerCase())

    const matchesTab = activeTab === 'all' || booking.status === activeTab

    return matchesSearch && matchesTab
  })

  const stats = {
    all: bookings.length,
    pending: bookings.filter((b) => b.status === 'pending').length,
    in_progress: bookings.filter((b) => b.status === 'in_progress').length,
    complete: bookings.filter((b) => b.status === 'complete').length,
    synced: bookings.filter((b) => b.status === 'synced').length,
    error: bookings.filter((b) => b.status === 'error').length,
  }

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-96">
          <div className="text-center">
            <Loader2 className="w-12 h-12 animate-spin text-blue-600 mx-auto mb-4" />
            <p className="text-slate-600 font-medium">Loading bookings...</p>
          </div>
        </div>
      </Layout>
    )
  }

  if (!selectedPropertyId) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-96">
          <Card className="max-w-md text-center">
            <CardContent>
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Calendar className="w-8 h-8 text-blue-600" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">No Property Selected</h3>
              <p className="text-gray-600 mb-6">
                You don't have any properties assigned. Please contact your administrator to assign you to a property.
              </p>
              <Link
                to="/properties"
                className="inline-flex items-center px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
              >
                View Properties
              </Link>
            </CardContent>
          </Card>
        </div>
      </Layout>
    )
  }

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Bookings</h1>
            <p className="mt-2 text-sm text-gray-600">Manage all your property bookings</p>
          </div>
          <Link
            to="/bookings/new"
            className="inline-flex items-center px-4 py-2 bg-gray-900 text-white text-sm font-medium rounded-lg hover:bg-gray-800"
          >
            Create Booking
          </Link>
        </div>

        {/* Filters and Search */}
        <Card>
          <CardContent className="!p-4">
            <div className="flex items-center space-x-3">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                <Input
                  type="text"
                  placeholder="Search bookings by ID or type..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
              <Button variant="outline" onClick={handleExport}>
                <Download className="w-4 h-4 mr-2" />
                Export
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Tabs */}
        <Card>
          <div className="border-b border-gray-200 px-6 pt-4">
            <div className="flex space-x-6">
              <button
                onClick={() => setActiveTab('all')}
                className={`pb-3 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === 'all'
                    ? 'border-gray-900 text-gray-900'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                All
                <span className="ml-2 px-2 py-0.5 text-xs rounded-full bg-gray-100 text-gray-700">
                  {stats.all}
                </span>
              </button>
              <button
                onClick={() => setActiveTab('pending')}
                className={`pb-3 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === 'pending'
                    ? 'border-gray-900 text-gray-900'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                Pending
                <span className="ml-2 px-2 py-0.5 text-xs rounded-full bg-yellow-100 text-yellow-700">
                  {stats.pending}
                </span>
              </button>
              <button
                onClick={() => setActiveTab('in_progress')}
                className={`pb-3 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === 'in_progress'
                    ? 'border-gray-900 text-gray-900'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                In Progress
                <span className="ml-2 px-2 py-0.5 text-xs rounded-full bg-blue-100 text-blue-700">
                  {stats.in_progress}
                </span>
              </button>
              <button
                onClick={() => setActiveTab('complete')}
                className={`pb-3 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === 'complete'
                    ? 'border-gray-900 text-gray-900'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                Complete
                <span className="ml-2 px-2 py-0.5 text-xs rounded-full bg-green-100 text-green-700">
                  {stats.complete}
                </span>
              </button>
              <button
                onClick={() => setActiveTab('synced')}
                className={`pb-3 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === 'synced'
                    ? 'border-gray-900 text-gray-900'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                Synced
                <span className="ml-2 px-2 py-0.5 text-xs rounded-full bg-purple-100 text-purple-700">
                  {stats.synced}
                </span>
              </button>
            </div>
          </div>

          <CardContent>
            {loading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="w-8 h-8 animate-spin text-gray-900" />
              </div>
            ) : filteredBookings.length === 0 ? (
              <div className="text-center py-12">
                <Calendar className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                <p className="text-gray-900 font-medium">No bookings found</p>
                <p className="text-sm text-gray-500 mt-1">
                  {searchTerm
                    ? 'Try adjusting your search terms'
                    : 'Create your first booking to get started'}
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {filteredBookings.map((booking) => (
                  <Link
                    key={booking.id}
                    to={`/bookings/${booking.id}`}
                    className="block p-4 border border-gray-200 rounded-lg hover:border-gray-300 hover:shadow-sm transition-all"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3 mb-2">
                          <p className="font-semibold text-gray-900">
                            {booking.booking_type.charAt(0).toUpperCase() + booking.booking_type.slice(1)}
                          </p>
                          <Badge variant={getStatusVariant(booking.status)}>
                            {booking.status.replace('_', ' ')}
                          </Badge>
                        </div>
                        <div className="flex items-center text-sm text-gray-500 space-x-4">
                          <span className="flex items-center">
                            <Calendar className="w-4 h-4 mr-1" />
                            {formatDate(booking.check_in_date)} - {formatDate(booking.check_out_date)}
                          </span>
                          <span className="flex items-center">
                            <Users className="w-4 h-4 mr-1" />
                            {booking.expected_guests} guests
                          </span>
                          <span className="text-xs text-gray-400 font-mono">{booking.id.slice(0, 8)}</span>
                        </div>
                      </div>
                      <ArrowRight className="w-5 h-5 text-gray-400" />
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </Layout>
  )
}

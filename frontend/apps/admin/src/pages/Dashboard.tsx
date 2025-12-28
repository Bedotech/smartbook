import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Calendar, Users, CheckCircle, AlertCircle, Clock, ArrowRight, Loader2, TrendingUp } from 'lucide-react'
import { adminApi } from '@smartbook/api'
import { Card, CardHeader, CardTitle, CardDescription, CardContent, Badge } from '@smartbook/ui'
import type { DashboardStats, Booking } from '@smartbook/types'
import Layout from '../components/Layout'

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [recentBookings, setRecentBookings] = useState<Booking[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    try {
      setLoading(true)
      setError(null)
      const [dashboardStats, bookings] = await Promise.all([
        adminApi.getDashboardStats(),
        adminApi.getBookings({ limit: 5 }),
      ])
      setStats(dashboardStats)
      setRecentBookings(bookings)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard data')
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

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-96">
          <div className="text-center">
            <Loader2 className="w-12 h-12 animate-spin text-blue-600 mx-auto mb-4" />
            <p className="text-slate-600 font-medium">Loading dashboard...</p>
          </div>
        </div>
      </Layout>
    )
  }

  if (error) {
    return (
      <Layout>
        <Card className="border-red-200 bg-red-50">
          <CardContent>
            <div className="flex items-start space-x-3">
              <AlertCircle className="h-6 w-6 text-red-600 mt-0.5" />
              <div>
                <h3 className="text-lg font-semibold text-red-900">Error loading dashboard</h3>
                <p className="mt-1 text-sm text-red-700">{error}</p>
                <button
                  onClick={loadDashboardData}
                  className="mt-4 px-4 py-2 bg-red-600 text-white text-sm font-medium rounded-lg hover:bg-red-700 transition-colors"
                >
                  Try again
                </button>
              </div>
            </div>
          </CardContent>
        </Card>
      </Layout>
    )
  }

  const statsCards = [
    {
      name: 'Total Bookings',
      value: stats?.total_bookings || 0,
      icon: Calendar,
      color: 'from-blue-500 to-blue-600',
      iconColor: 'text-blue-600',
      bgColor: 'bg-blue-50',
    },
    {
      name: 'Pending',
      value: stats?.pending_bookings || 0,
      icon: Clock,
      color: 'from-amber-500 to-amber-600',
      iconColor: 'text-amber-600',
      bgColor: 'bg-amber-50',
    },
    {
      name: 'Complete',
      value: stats?.complete_bookings || 0,
      icon: CheckCircle,
      color: 'from-emerald-500 to-emerald-600',
      iconColor: 'text-emerald-600',
      bgColor: 'bg-emerald-50',
    },
    {
      name: 'Synced',
      value: stats?.synced_bookings || 0,
      icon: Users,
      color: 'from-purple-500 to-purple-600',
      iconColor: 'text-purple-600',
      bgColor: 'bg-purple-50',
    },
    {
      name: 'Errors',
      value: stats?.error_bookings || 0,
      icon: AlertCircle,
      color: 'from-red-500 to-red-600',
      iconColor: 'text-red-600',
      bgColor: 'bg-red-50',
    },
  ]

  return (
    <Layout>
      <div className="space-y-8">
        {/* Header */}
        <div>
          <h1 className="text-4xl font-bold text-slate-900">Dashboard</h1>
          <p className="mt-3 text-base text-slate-600">
            Welcome back! Here's what's happening with your property today.
          </p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
          {statsCards.map((stat) => {
            const Icon = stat.icon
            return (
              <Card key={stat.name} padding="lg" hover className="relative overflow-hidden">
                <div className={`absolute inset-0 bg-gradient-to-br ${stat.color} opacity-5`}></div>
                <div className="relative">
                  <div className="flex items-center justify-between mb-4">
                    <div className={`p-3 ${stat.bgColor} rounded-lg`}>
                      <Icon className={`w-6 h-6 ${stat.iconColor}`} />
                    </div>
                  </div>
                  <p className="text-sm font-medium text-slate-600 mb-1">{stat.name}</p>
                  <p className={`text-4xl font-bold ${stat.iconColor}`}>{stat.value}</p>
                </div>
              </Card>
            )
          })}
        </div>

        {/* Completion Rate */}
        {stats && stats.total_bookings > 0 && (
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Completion Rate</CardTitle>
                  <CardDescription>Percentage of completed bookings</CardDescription>
                </div>
                <div className="flex items-center space-x-2 bg-emerald-50 px-4 py-3 rounded-lg">
                  <TrendingUp className="w-6 h-6 text-emerald-600" />
                  <span className="text-3xl font-bold text-emerald-600">{stats.completion_rate.toFixed(1)}%</span>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="w-full bg-slate-100 rounded-full h-4">
                <div
                  className="bg-gradient-to-r from-emerald-500 to-emerald-600 h-4 rounded-full transition-all duration-500 shadow-sm"
                  style={{ width: `${stats.completion_rate}%` }}
                />
              </div>
            </CardContent>
          </Card>
        )}

        {/* Recent Bookings */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Recent Bookings</CardTitle>
                <CardDescription>Latest bookings from your property</CardDescription>
              </div>
              <Link
                to="/bookings"
                className="inline-flex items-center text-sm font-semibold text-blue-600 hover:text-blue-700 transition-colors"
              >
                View all
                <ArrowRight className="w-4 h-4 ml-1" />
              </Link>
            </div>
          </CardHeader>
          <CardContent>
            {recentBookings.length === 0 ? (
              <div className="text-center py-16 bg-slate-50 rounded-lg">
                <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Calendar className="w-8 h-8 text-slate-400" />
                </div>
                <p className="text-lg font-semibold text-slate-900">No bookings yet</p>
                <p className="text-sm text-slate-600 mt-2 mb-6">Create your first booking to get started</p>
                <Link
                  to="/bookings/new"
                  className="inline-flex items-center px-6 py-3 bg-blue-600 text-white text-sm font-semibold rounded-lg hover:bg-blue-700 shadow-lg shadow-blue-500/30 transition-all"
                >
                  <Calendar className="w-4 h-4 mr-2" />
                  Create Booking
                </Link>
              </div>
            ) : (
              <div className="space-y-3">
                {recentBookings.map((booking) => (
                  <Link
                    key={booking.id}
                    to={`/bookings/${booking.id}`}
                    className="block p-5 border-2 border-slate-200 rounded-xl hover:border-blue-300 hover:shadow-md hover:bg-blue-50/50 transition-all"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3 mb-3">
                          <p className="text-lg font-bold text-slate-900">
                            {booking.booking_type.charAt(0).toUpperCase() + booking.booking_type.slice(1)}
                          </p>
                          <Badge variant={getStatusVariant(booking.status)}>
                            {booking.status.replace('_', ' ')}
                          </Badge>
                        </div>
                        <div className="flex items-center text-sm text-slate-600 space-x-6">
                          <span className="flex items-center font-medium">
                            <Calendar className="w-4 h-4 mr-2" />
                            {formatDate(booking.check_in_date)}
                          </span>
                          <span className="flex items-center font-medium">
                            <Users className="w-4 h-4 mr-2" />
                            {booking.expected_guests} guests
                          </span>
                        </div>
                      </div>
                      <ArrowRight className="w-6 h-6 text-slate-400" />
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

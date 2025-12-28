import { useParams, useNavigate } from 'react-router-dom'
import { Calendar, Users, ArrowRight, Clock } from 'lucide-react'
import { format, parseISO } from 'date-fns'
import { useBooking } from '../hooks/useBooking'
import { useBookingProgress } from '../hooks/useBookingProgress'
import { LoadingSpinner } from '../components/LoadingSpinner'
import { ErrorDisplay } from '../components/ErrorDisplay'
import { ProgressBar } from '../components/ProgressBar'
import { Card, CardHeader, CardTitle, CardContent, Button } from '@smartbook/ui'

export default function CheckInPage() {
  const { token } = useParams<{ token: string }>()
  const navigate = useNavigate()

  const {
    data: booking,
    isLoading: bookingLoading,
    error: bookingError,
    refetch: refetchBooking,
  } = useBooking(token!)

  const { data: progress, isLoading: progressLoading } = useBookingProgress(token!, !!booking)

  const isLoading = bookingLoading || progressLoading

  if (isLoading) {
    return <LoadingSpinner message="Loading your booking..." />
  }

  if (bookingError || !booking) {
    return (
      <ErrorDisplay
        message={bookingError?.message || 'Invalid or expired magic link'}
        onRetry={refetchBooking}
      />
    )
  }

  const checkInDate = format(parseISO(booking.check_in_date), 'EEEE, MMMM d, yyyy')
  const checkOutDate = format(parseISO(booking.check_out_date), 'EEEE, MMMM d, yyyy')
  const canContinue = booking.status === 'pending' || booking.status === 'in_progress'

  const handleStart = () => {
    if (progress?.has_leader) {
      // Leader already exists, go to member list
      navigate(`/s/${token}/members`)
    } else {
      // Start with leader form
      navigate(`/s/${token}/leader`)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-md mx-auto space-y-6 py-8">
        {/* Header */}
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Welcome to Smartbook</h1>
          <p className="text-gray-600">Complete your group check-in</p>
        </div>

        {/* Booking Info Card */}
        <Card>
          <CardHeader>
            <CardTitle>Your Booking</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-start gap-3">
              <Calendar className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-700">Check-in</p>
                <p className="text-sm text-gray-900">{checkInDate}</p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <Clock className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-700">Check-out</p>
                <p className="text-sm text-gray-900">{checkOutDate}</p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <Users className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-700">Expected Guests</p>
                <p className="text-sm text-gray-900">
                  {booking.expected_guests}{' '}
                  {booking.expected_guests === 1 ? 'guest' : 'guests'}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Progress Card (if started) */}
        {progress && progress.total_entered > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Your Progress</CardTitle>
            </CardHeader>
            <CardContent>
              <ProgressBar
                current={progress.total_entered}
                total={progress.total_expected}
                hasLeader={progress.has_leader}
              />
            </CardContent>
          </Card>
        )}

        {/* Status Card */}
        {booking.status === 'complete' && (
          <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-4">
            <p className="text-sm text-emerald-800 font-medium">
              Check-in completed! You can view your confirmation below.
            </p>
          </div>
        )}

        {booking.status === 'synced' && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-sm text-blue-800 font-medium">
              Check-in synced with authorities. Thank you!
            </p>
          </div>
        )}

        {/* Action Button */}
        {canContinue ? (
          <Button onClick={handleStart} variant="primary" size="lg" fullWidth className="gap-2">
            {progress?.has_leader ? 'Continue Check-In' : 'Start Check-In'}
            <ArrowRight className="w-5 h-5" />
          </Button>
        ) : booking.status === 'complete' || booking.status === 'synced' ? (
          <Button
            onClick={() => navigate(`/s/${token}/success`)}
            variant="primary"
            size="lg"
            fullWidth
          >
            View Confirmation
          </Button>
        ) : null}

        {/* Helper Text */}
        <p className="text-xs text-gray-500 text-center">
          You'll need to provide information for the group leader and all members
        </p>
      </div>
    </div>
  )
}

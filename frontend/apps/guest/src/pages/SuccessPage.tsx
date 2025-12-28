import { useParams } from 'react-router-dom'
import { CheckCircle, Download, Share2 } from 'lucide-react'
import { QRCodeSVG } from 'qrcode.react'
import { Card, CardHeader, CardTitle, CardContent, Button } from '@smartbook/ui'
import { useBooking } from '../hooks'
import { LoadingSpinner } from '../components/LoadingSpinner'
import { ErrorDisplay } from '../components/ErrorDisplay'

export default function SuccessPage() {
  const { token } = useParams<{ token: string }>()
  const { data: booking, isLoading, error } = useBooking(token!)

  // Generate QR code value - includes the full check-in URL
  const qrCodeValue = `${window.location.origin}/s/${token}`

  const handleDownloadQR = () => {
    const svg = document.getElementById('qr-code-svg')
    if (!svg) return

    const svgData = new XMLSerializer().serializeToString(svg)
    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')
    const img = new Image()

    canvas.width = 512
    canvas.height = 512

    img.onload = () => {
      ctx?.drawImage(img, 0, 0)
      canvas.toBlob((blob) => {
        if (!blob) return
        const url = URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.download = `smartbook-checkin-${token}.png`
        link.href = url
        link.click()
        URL.revokeObjectURL(url)
      })
    }

    img.src = 'data:image/svg+xml;base64,' + btoa(svgData)
  }

  const handleShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: 'Smartbook Check-In',
          text: 'Group check-in completed successfully!',
          url: qrCodeValue,
        })
      } catch (err) {
        // User cancelled share or share not supported
        console.log('Share cancelled or failed:', err)
      }
    } else {
      // Fallback: copy to clipboard
      navigator.clipboard.writeText(qrCodeValue)
      alert('Link copied to clipboard!')
    }
  }

  if (isLoading) {
    return <LoadingSpinner message="Loading booking details..." />
  }

  if (error || !booking) {
    return <ErrorDisplay message="Failed to load booking information" />
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50 p-4 flex items-center justify-center">
      <div className="max-w-lg w-full mx-auto space-y-6">
        {/* Success Header */}
        <div className="text-center">
          <div className="inline-flex items-center justify-center w-20 h-20 bg-green-100 rounded-full mb-4">
            <CheckCircle className="w-12 h-12 text-green-600" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Check-In Complete!</h1>
          <p className="text-gray-600">
            Your group check-in has been successfully submitted to the authorities.
          </p>
        </div>

        {/* Booking Info Card */}
        <Card>
          <CardHeader>
            <CardTitle>Booking Information</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex justify-between items-center py-2 border-b border-gray-100">
              <span className="text-sm text-gray-600">Booking Type</span>
              <span className="font-medium text-gray-900 capitalize">{booking.booking_type}</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b border-gray-100">
              <span className="text-sm text-gray-600">Check-In Date</span>
              <span className="font-medium text-gray-900">
                {new Date(booking.check_in_date).toLocaleDateString('it-IT', {
                  day: '2-digit',
                  month: '2-digit',
                  year: 'numeric',
                })}
              </span>
            </div>
            <div className="flex justify-between items-center py-2 border-b border-gray-100">
              <span className="text-sm text-gray-600">Check-Out Date</span>
              <span className="font-medium text-gray-900">
                {new Date(booking.check_out_date).toLocaleDateString('it-IT', {
                  day: '2-digit',
                  month: '2-digit',
                  year: 'numeric',
                })}
              </span>
            </div>
            <div className="flex justify-between items-center py-2">
              <span className="text-sm text-gray-600">Expected Guests</span>
              <span className="font-medium text-gray-900">{booking.expected_guests}</span>
            </div>
          </CardContent>
        </Card>

        {/* QR Code Card */}
        <Card>
          <CardHeader>
            <CardTitle>Your Check-In QR Code</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="bg-white p-6 rounded-lg border-2 border-gray-200 flex items-center justify-center">
              <QRCodeSVG
                id="qr-code-svg"
                value={qrCodeValue}
                size={256}
                level="H"
                includeMargin
                className="w-full h-auto max-w-[256px]"
              />
            </div>
            <p className="text-xs text-gray-500 text-center">
              Scan this QR code to access your check-in details
            </p>

            {/* Action Buttons */}
            <div className="grid grid-cols-2 gap-3 pt-2">
              <Button
                onClick={handleDownloadQR}
                variant="outline"
                size="sm"
                className="gap-2"
                fullWidth
              >
                <Download className="w-4 h-4" />
                Download
              </Button>
              <Button onClick={handleShare} variant="outline" size="sm" className="gap-2" fullWidth>
                <Share2 className="w-4 h-4" />
                Share
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Reference Card */}
        <Card>
          <CardHeader>
            <CardTitle>Booking Reference</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
              <p className="text-sm font-mono text-gray-900 text-center break-all">{token}</p>
            </div>
            <p className="text-xs text-gray-500 text-center mt-3">
              Keep this reference number for your records
            </p>
          </CardContent>
        </Card>

        {/* Footer Info */}
        <div className="text-center text-sm text-gray-600 px-4">
          <p>
            Thank you for using Smartbook. Your data has been securely transmitted to the Italian
            authorities as required by law.
          </p>
        </div>
      </div>
    </div>
  )
}

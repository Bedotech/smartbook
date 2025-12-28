import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft, ArrowRight, Check, Calendar, Users, Home } from 'lucide-react'
import { adminApi } from '@smartbook/api'
import { Card, CardHeader, CardTitle, CardDescription, CardContent, Button, Input } from '@smartbook/ui'
import type { BookingCreateData } from '@smartbook/types'
import Layout from '../components/Layout'

type Step = 1 | 2 | 3

export default function NewBooking() {
  const navigate = useNavigate()
  const [currentStep, setCurrentStep] = useState<Step>(1)
  const [loading, setLoading] = useState(false)
  const [formData, setFormData] = useState<BookingCreateData>({
    booking_type: 'individual',
    check_in_date: '',
    check_out_date: '',
    expected_guests: 1,
    notes: '',
  })

  const handleInputChange = (field: keyof BookingCreateData, value: string | number) => {
    setFormData((prev) => ({ ...prev, [field]: value }))
  }

  const validateStep = (step: Step): boolean => {
    switch (step) {
      case 1:
        return true // booking_type is always valid since we have a default
      case 2:
        return (
          formData.check_in_date !== '' &&
          formData.check_out_date !== '' &&
          new Date(formData.check_in_date) < new Date(formData.check_out_date)
        )
      case 3:
        return formData.expected_guests > 0
      default:
        return false
    }
  }

  const handleNext = () => {
    if (validateStep(currentStep)) {
      setCurrentStep((prev) => Math.min(3, prev + 1) as Step)
    }
  }

  const handleBack = () => {
    setCurrentStep((prev) => Math.max(1, prev - 1) as Step)
  }

  const handleSubmit = async () => {
    if (!validateStep(3)) return

    try {
      setLoading(true)
      const booking = await adminApi.createBooking(formData)
      navigate(`/bookings/${booking.id}`)
    } catch (err) {
      console.error('Failed to create booking:', err)
      alert('Failed to create booking. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const steps = [
    { number: 1, title: 'Booking Type', icon: Home },
    { number: 2, title: 'Dates', icon: Calendar },
    { number: 3, title: 'Guests', icon: Users },
  ]

  return (
    <Layout>
      <div className="max-w-3xl mx-auto space-y-8">
        {/* Header */}
        <div>
          <button
            onClick={() => navigate('/bookings')}
            className="inline-flex items-center text-sm text-gray-600 hover:text-gray-900 mb-4"
          >
            <ArrowLeft className="w-4 h-4 mr-1" />
            Back to bookings
          </button>
          <h1 className="text-3xl font-bold text-gray-900">Create New Booking</h1>
          <p className="mt-2 text-sm text-gray-600">
            Fill in the booking details to create a new reservation
          </p>
        </div>

        {/* Progress Steps */}
        <Card>
          <CardContent className="!p-6">
            <div className="flex items-center justify-between">
              {steps.map((step, index) => {
                const Icon = step.icon
                const isCompleted = currentStep > step.number
                const isActive = currentStep === step.number

                return (
                  <div key={step.number} className="flex items-center flex-1">
                    <div className="flex flex-col items-center flex-1">
                      <div
                        className={`w-10 h-10 rounded-full flex items-center justify-center border-2 transition-colors ${
                          isCompleted
                            ? 'bg-green-600 border-green-600 text-white'
                            : isActive
                            ? 'bg-gray-900 border-gray-900 text-white'
                            : 'bg-white border-gray-300 text-gray-400'
                        }`}
                      >
                        {isCompleted ? <Check className="w-5 h-5" /> : <Icon className="w-5 h-5" />}
                      </div>
                      <span
                        className={`mt-2 text-xs font-medium ${
                          isActive ? 'text-gray-900' : 'text-gray-500'
                        }`}
                      >
                        {step.title}
                      </span>
                    </div>
                    {index < steps.length - 1 && (
                      <div
                        className={`h-0.5 flex-1 mx-2 transition-colors ${
                          currentStep > step.number ? 'bg-green-600' : 'bg-gray-200'
                        }`}
                      />
                    )}
                  </div>
                )
              })}
            </div>
          </CardContent>
        </Card>

        {/* Form Content */}
        <Card>
          <CardHeader>
            <CardTitle>
              {currentStep === 1 && 'Select Booking Type'}
              {currentStep === 2 && 'Choose Dates'}
              {currentStep === 3 && 'Number of Guests'}
            </CardTitle>
            <CardDescription>
              {currentStep === 1 && 'Choose whether this is an individual or group booking'}
              {currentStep === 2 && 'Select check-in and check-out dates'}
              {currentStep === 3 && 'Specify the number of expected guests and add notes'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {/* Step 1: Booking Type */}
            {currentStep === 1 && (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <button
                    onClick={() => handleInputChange('booking_type', 'individual')}
                    className={`p-6 border-2 rounded-lg text-left transition-all ${
                      formData.booking_type === 'individual'
                        ? 'border-gray-900 bg-gray-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <Home className="w-8 h-8 text-gray-700" />
                      {formData.booking_type === 'individual' && (
                        <div className="w-5 h-5 rounded-full bg-gray-900 flex items-center justify-center">
                          <Check className="w-3 h-3 text-white" />
                        </div>
                      )}
                    </div>
                    <h3 className="font-semibold text-gray-900 mb-1">Individual</h3>
                    <p className="text-sm text-gray-600">
                      Single traveler or family booking
                    </p>
                  </button>

                  <button
                    onClick={() => handleInputChange('booking_type', 'group')}
                    className={`p-6 border-2 rounded-lg text-left transition-all ${
                      formData.booking_type === 'group'
                        ? 'border-gray-900 bg-gray-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <Users className="w-8 h-8 text-gray-700" />
                      {formData.booking_type === 'group' && (
                        <div className="w-5 h-5 rounded-full bg-gray-900 flex items-center justify-center">
                          <Check className="w-3 h-3 text-white" />
                        </div>
                      )}
                    </div>
                    <h3 className="font-semibold text-gray-900 mb-1">Group</h3>
                    <p className="text-sm text-gray-600">
                      Multiple guests traveling together
                    </p>
                  </button>
                </div>
              </div>
            )}

            {/* Step 2: Dates */}
            {currentStep === 2 && (
              <div className="space-y-4">
                <Input
                  type="date"
                  label="Check-in Date"
                  value={formData.check_in_date}
                  onChange={(e) => handleInputChange('check_in_date', e.target.value)}
                  required
                />
                <Input
                  type="date"
                  label="Check-out Date"
                  value={formData.check_out_date}
                  onChange={(e) => handleInputChange('check_out_date', e.target.value)}
                  required
                  helperText={
                    formData.check_in_date && formData.check_out_date
                      ? `${Math.ceil(
                          (new Date(formData.check_out_date).getTime() -
                            new Date(formData.check_in_date).getTime()) /
                            (1000 * 60 * 60 * 24)
                        )} nights`
                      : undefined
                  }
                />
              </div>
            )}

            {/* Step 3: Guests */}
            {currentStep === 3 && (
              <div className="space-y-4">
                <Input
                  type="number"
                  label="Number of Guests"
                  value={formData.expected_guests.toString()}
                  onChange={(e) => handleInputChange('expected_guests', parseInt(e.target.value) || 1)}
                  min={1}
                  required
                />
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">
                    Notes (Optional)
                  </label>
                  <textarea
                    value={formData.notes || ''}
                    onChange={(e) => handleInputChange('notes', e.target.value)}
                    rows={4}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-gray-900"
                    placeholder="Add any additional notes about this booking..."
                  />
                </div>

                {/* Summary */}
                <div className="mt-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
                  <h4 className="font-medium text-gray-900 mb-3">Booking Summary</h4>
                  <dl className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <dt className="text-gray-600">Type:</dt>
                      <dd className="font-medium text-gray-900 capitalize">{formData.booking_type}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-gray-600">Check-in:</dt>
                      <dd className="font-medium text-gray-900">
                        {new Date(formData.check_in_date).toLocaleDateString('it-IT')}
                      </dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-gray-600">Check-out:</dt>
                      <dd className="font-medium text-gray-900">
                        {new Date(formData.check_out_date).toLocaleDateString('it-IT')}
                      </dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-gray-600">Guests:</dt>
                      <dd className="font-medium text-gray-900">{formData.expected_guests}</dd>
                    </div>
                  </dl>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Actions */}
        <div className="flex items-center justify-between">
          <Button
            variant="ghost"
            onClick={handleBack}
            disabled={currentStep === 1}
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
          <div className="flex items-center space-x-3">
            <Button
              variant="outline"
              onClick={() => navigate('/bookings')}
            >
              Cancel
            </Button>
            {currentStep < 3 ? (
              <Button
                onClick={handleNext}
                disabled={!validateStep(currentStep)}
              >
                Next
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            ) : (
              <Button
                onClick={handleSubmit}
                disabled={!validateStep(3)}
                loading={loading}
              >
                Create Booking
              </Button>
            )}
          </div>
        </div>
      </div>
    </Layout>
  )
}

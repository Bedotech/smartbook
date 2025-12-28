import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useForm, Controller } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { ArrowLeft, Plus, Check, Users as UsersIcon } from 'lucide-react'
import { memberFormSchema, type MemberFormValues } from '../schemas/memberSchema'
import {
  useBookingProgress,
  useGuests,
  useAddMember,
  useCompleteBooking,
  useMunicipalitySearch,
  useCountrySearch,
} from '../hooks'
import { LoadingSpinner } from '../components/LoadingSpinner'
import { ErrorDisplay } from '../components/ErrorDisplay'
import { ProgressBar } from '../components/ProgressBar'
import { GuestCard } from '../components/GuestCard'
import { AutocompleteInput } from '../components/AutocompleteInput'
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  Button,
  Input,
  Select,
} from '@smartbook/ui'

export default function MemberListPage() {
  const { token } = useParams<{ token: string }>()
  const navigate = useNavigate()
  const [showForm, setShowForm] = useState(false)

  // Data fetching
  const { data: progress, isLoading: progressLoading } = useBookingProgress(token!)
  const { data: guests, isLoading: guestsLoading } = useGuests(token!)
  const { mutate: addMember, isPending: addingMember, error: addError } = useAddMember(token!)
  const {
    mutate: completeBooking,
    isPending: completing,
    error: completeError,
  } = useCompleteBooking(token!)

  // Form state
  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
    control,
  } = useForm<MemberFormValues>({
    resolver: zodResolver(memberFormSchema),
    defaultValues: {
      role: 'member',
    },
  })

  // Municipality/Country search states
  const [birthMunicipalityQuery, setBirthMunicipalityQuery] = useState('')
  const [birthCountryQuery, setBirthCountryQuery] = useState('')
  const [residenceMunicipalityQuery, setResidenceMunicipalityQuery] = useState('')
  const [residenceCountryQuery, setResidenceCountryQuery] = useState('')
  const [citizenshipCountryQuery, setCitizenshipCountryQuery] = useState('')

  const { data: birthMunicipalities, isLoading: birthMunicipalitiesLoading } =
    useMunicipalitySearch(birthMunicipalityQuery, showForm)
  const { data: birthCountries, isLoading: birthCountriesLoading } = useCountrySearch(
    birthCountryQuery,
    showForm
  )
  const { data: residenceMunicipalities, isLoading: residenceMunicipalitiesLoading } =
    useMunicipalitySearch(residenceMunicipalityQuery, showForm)
  const { data: residenceCountries, isLoading: residenceCountriesLoading } = useCountrySearch(
    residenceCountryQuery,
    showForm
  )
  const { data: citizenshipCountries, isLoading: citizenshipCountriesLoading } = useCountrySearch(
    citizenshipCountryQuery,
    showForm
  )

  const isLoading = progressLoading || guestsLoading

  if (isLoading) {
    return <LoadingSpinner message="Loading guests..." />
  }

  if (!progress || !guests) {
    return <ErrorDisplay message="Failed to load booking information" />
  }

  const canComplete = progress.current_guest_count >= progress.expected_guests && progress.has_leader
  const remainingGuests = Math.max(0, progress.expected_guests - progress.current_guest_count)

  const onSubmitMember = (data: MemberFormValues) => {
    addMember(data, {
      onSuccess: () => {
        reset()
        setShowForm(false)
        setBirthMunicipalityQuery('')
        setBirthCountryQuery('')
        setResidenceMunicipalityQuery('')
        setResidenceCountryQuery('')
        setCitizenshipCountryQuery('')
      },
    })
  }

  const handleComplete = () => {
    if (!canComplete) return

    completeBooking(undefined, {
      onSuccess: () => {
        navigate(`/s/${token}/success`)
      },
    })
  }

  return (
    <div className="min-h-screen bg-gray-50 p-4 pb-24">
      <div className="max-w-2xl mx-auto space-y-6 py-6">
        {/* Header */}
        <div>
          <button
            type="button"
            onClick={() => navigate(`/s/${token}`)}
            className="inline-flex items-center text-sm text-gray-600 hover:text-gray-900 mb-4 transition-colors"
          >
            <ArrowLeft className="w-4 h-4 mr-1" />
            Back to booking
          </button>
          <div className="flex items-center gap-3 mb-2">
            <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
              <UsersIcon className="w-6 h-6 text-blue-700" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Group Members</h1>
              <p className="text-sm text-gray-600">
                {remainingGuests > 0
                  ? `${remainingGuests} more ${remainingGuests === 1 ? 'guest' : 'guests'} to add`
                  : 'All guests entered'}
              </p>
            </div>
          </div>
        </div>

        {/* Progress Card */}
        <Card>
          <CardHeader>
            <CardTitle>Progress</CardTitle>
          </CardHeader>
          <CardContent>
            <ProgressBar
              current={progress.current_guest_count}
              total={progress.expected_guests}
              hasLeader={progress.has_leader}
            />
          </CardContent>
        </Card>

        {/* Guest List */}
        <Card>
          <CardHeader>
            <CardTitle>Entered Guests ({guests.length})</CardTitle>
          </CardHeader>
          <CardContent>
            {guests.length === 0 ? (
              <p className="text-sm text-gray-500 text-center py-4">No guests added yet</p>
            ) : (
              <div className="space-y-3">
                {guests.map((guest) => (
                  <GuestCard key={guest.id} guest={guest} />
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Add Member Form */}
        {!showForm && remainingGuests > 0 && (
          <Button
            onClick={() => setShowForm(true)}
            variant="outline"
            size="lg"
            fullWidth
            className="gap-2"
          >
            <Plus className="w-5 h-5" />
            Add Group Member
          </Button>
        )}

        {showForm && (
          <form onSubmit={handleSubmit(onSubmitMember)} className="space-y-6">
            {/* Personal Information */}
            <Card>
              <CardHeader>
                <CardTitle>Member Information</CardTitle>
                <CardDescription>Required fields only - faster check-in</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Input
                    label="First Name"
                    {...register('first_name')}
                    error={errors.first_name?.message}
                    required
                    placeholder="Giovanni"
                  />
                  <Input
                    label="Last Name"
                    {...register('last_name')}
                    error={errors.last_name?.message}
                    required
                    placeholder="Bianchi"
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Select
                    label="Sex"
                    {...register('sex')}
                    error={errors.sex?.message}
                    required
                    options={[
                      { value: '', label: 'Select...' },
                      { value: 'M', label: 'Male' },
                      { value: 'F', label: 'Female' },
                    ]}
                  />
                  <Input
                    label="Date of Birth"
                    type="date"
                    {...register('date_of_birth')}
                    error={errors.date_of_birth?.message}
                    required
                  />
                </div>

                <Select
                  label="Role"
                  {...register('role')}
                  error={errors.role?.message}
                  options={[
                    { value: 'member', label: 'Group Member' },
                    { value: 'bus_driver', label: 'Bus Driver' },
                    { value: 'tour_guide', label: 'Tour Guide' },
                  ]}
                  helperText="Special roles for tour operators"
                />
              </CardContent>
            </Card>

            {/* Optional Details - Collapsible */}
            <details className="group">
              <summary className="cursor-pointer select-none">
                <Card className="group-open:rounded-b-none">
                  <CardContent className="!py-4">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-gray-700">
                        Add optional details (birth place, residence, etc.)
                      </span>
                      <span className="text-xs text-gray-500">Click to expand</span>
                    </div>
                  </CardContent>
                </Card>
              </summary>

              <Card className="rounded-t-none border-t-0 space-y-4">
                <CardContent className="space-y-4 pt-0">
                  {/* Place of Birth */}
                  <div className="space-y-4 pt-4 border-t border-gray-200">
                    <h4 className="text-sm font-medium text-gray-900">Place of Birth</h4>
                    <Controller
                      name="place_of_birth_municipality_code"
                      control={control}
                      render={({ field }) => (
                        <AutocompleteInput
                          label="Municipality"
                          value={birthMunicipalityQuery}
                          onChange={(query, option) => {
                            setBirthMunicipalityQuery(query)
                            if (option) field.onChange(option.value)
                          }}
                          options={
                            birthMunicipalities?.map((m) => ({
                              value: m.istat_code,
                              label: m.name,
                              subtitle: `${m.province_name} - ${m.region_name}`,
                            })) || []
                          }
                          loading={birthMunicipalitiesLoading}
                          placeholder="Start typing..."
                        />
                      )}
                    />

                    <Controller
                      name="place_of_birth_country_code"
                      control={control}
                      render={({ field }) => (
                        <AutocompleteInput
                          label="Country"
                          value={birthCountryQuery}
                          onChange={(query, option) => {
                            setBirthCountryQuery(query)
                            if (option) field.onChange(option.value)
                          }}
                          options={
                            birthCountries?.map((c) => ({
                              value: c.istat_code,
                              label: c.name,
                              subtitle: c.iso_code,
                            })) || []
                          }
                          loading={birthCountriesLoading}
                          placeholder="Start typing..."
                        />
                      )}
                    />
                  </div>

                  {/* Residence */}
                  <div className="space-y-4 pt-4 border-t border-gray-200">
                    <h4 className="text-sm font-medium text-gray-900">Residence</h4>
                    <Controller
                      name="residence_municipality_code"
                      control={control}
                      render={({ field }) => (
                        <AutocompleteInput
                          label="Municipality"
                          value={residenceMunicipalityQuery}
                          onChange={(query, option) => {
                            setResidenceMunicipalityQuery(query)
                            if (option) field.onChange(option.value)
                          }}
                          options={
                            residenceMunicipalities?.map((m) => ({
                              value: m.istat_code,
                              label: m.name,
                              subtitle: `${m.province_name} - ${m.region_name}`,
                            })) || []
                          }
                          loading={residenceMunicipalitiesLoading}
                          placeholder="Start typing..."
                        />
                      )}
                    />

                    <Controller
                      name="residence_country_code"
                      control={control}
                      render={({ field }) => (
                        <AutocompleteInput
                          label="Country"
                          value={residenceCountryQuery}
                          onChange={(query, option) => {
                            setResidenceCountryQuery(query)
                            if (option) field.onChange(option.value)
                          }}
                          options={
                            residenceCountries?.map((c) => ({
                              value: c.istat_code,
                              label: c.name,
                              subtitle: c.iso_code,
                            })) || []
                          }
                          loading={residenceCountriesLoading}
                          placeholder="Start typing..."
                        />
                      )}
                    />

                    <Input
                      label="Address"
                      {...register('residence_address')}
                      error={errors.residence_address?.message}
                      placeholder="Via Roma, 123"
                    />

                    <Input
                      label="ZIP Code"
                      {...register('residence_zip_code')}
                      error={errors.residence_zip_code?.message}
                      placeholder="00100"
                    />
                  </div>

                  {/* Citizenship */}
                  <div className="space-y-4 pt-4 border-t border-gray-200">
                    <h4 className="text-sm font-medium text-gray-900">Citizenship</h4>
                    <Controller
                      name="citizenship_country_code"
                      control={control}
                      render={({ field }) => (
                        <AutocompleteInput
                          label="Citizenship Country"
                          value={citizenshipCountryQuery}
                          onChange={(query, option) => {
                            setCitizenshipCountryQuery(query)
                            if (option) field.onChange(option.value)
                          }}
                          options={
                            citizenshipCountries?.map((c) => ({
                              value: c.istat_code,
                              label: c.name,
                              subtitle: c.iso_code,
                            })) || []
                          }
                          loading={citizenshipCountriesLoading}
                          placeholder="Start typing..."
                        />
                      )}
                    />
                  </div>
                </CardContent>
              </Card>
            </details>

            {/* Form Error */}
            {addError && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <p className="text-sm text-red-800">{addError.message}</p>
              </div>
            )}

            {/* Form Actions */}
            <div className="flex gap-3">
              <Button
                type="button"
                onClick={() => {
                  setShowForm(false)
                  reset()
                }}
                variant="outline"
                fullWidth
                disabled={addingMember}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="primary"
                fullWidth
                loading={addingMember}
                className="gap-2"
              >
                <Plus className="w-5 h-5" />
                Add Member
              </Button>
            </div>
          </form>
        )}

        {/* Complete Error */}
        {completeError && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-sm text-red-800">{completeError.message}</p>
          </div>
        )}

        {/* Complete Button */}
        {canComplete && (
          <div className="sticky bottom-0 bg-gray-50 pt-4 pb-6 -mx-4 px-4 border-t border-gray-200">
            <Button
              onClick={handleComplete}
              variant="primary"
              size="lg"
              fullWidth
              loading={completing}
              className="gap-2"
            >
              <Check className="w-5 h-5" />
              Complete Check-In
            </Button>
          </div>
        )}
      </div>
    </div>
  )
}

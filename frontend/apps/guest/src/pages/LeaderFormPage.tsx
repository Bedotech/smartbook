import { useParams, useNavigate } from 'react-router-dom'
import { useForm, Controller } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { ArrowLeft, ArrowRight, Crown } from 'lucide-react'
import { leaderFormSchema, type LeaderFormValues } from '../schemas/leaderSchema'
import { useAddLeader } from '../hooks/useAddLeader'
import { useMunicipalitySearch } from '../hooks/useMunicipalitySearch'
import { useCountrySearch } from '../hooks/useCountrySearch'
import { useOfflineStore } from '../stores/offlineStore'
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
import { useEffect, useState } from 'react'

export default function LeaderFormPage() {
  const { token } = useParams<{ token: string }>()
  const navigate = useNavigate()
  const { mutate: addLeader, isPending, error: submitError } = useAddLeader(token!)
  const { saveLeaderDraft, getLeaderDraft } = useOfflineStore()

  // Form state
  const {
    register,
    handleSubmit,
    formState: { errors },
    watch,
    control,
  } = useForm<LeaderFormValues>({
    resolver: zodResolver(leaderFormSchema),
    defaultValues: getLeaderDraft(token!) || {},
  })

  // Municipality/Country search states
  const [birthMunicipalityQuery, setBirthMunicipalityQuery] = useState('')
  const [birthCountryQuery, setBirthCountryQuery] = useState('')
  const [residenceMunicipalityQuery, setResidenceMunicipalityQuery] = useState('')
  const [residenceCountryQuery, setResidenceCountryQuery] = useState('')
  const [citizenshipCountryQuery, setCitizenshipCountryQuery] = useState('')

  const { data: birthMunicipalities, isLoading: birthMunicipalitiesLoading } =
    useMunicipalitySearch(birthMunicipalityQuery)
  const { data: birthCountries, isLoading: birthCountriesLoading } =
    useCountrySearch(birthCountryQuery)
  const { data: residenceMunicipalities, isLoading: residenceMunicipalitiesLoading } =
    useMunicipalitySearch(residenceMunicipalityQuery)
  const { data: residenceCountries, isLoading: residenceCountriesLoading } =
    useCountrySearch(residenceCountryQuery)
  const { data: citizenshipCountries, isLoading: citizenshipCountriesLoading } =
    useCountrySearch(citizenshipCountryQuery)

  // Auto-save draft
  const formValues = watch()
  useEffect(() => {
    const timer = setTimeout(() => {
      saveLeaderDraft(token!, formValues)
    }, 1000)
    return () => clearTimeout(timer)
  }, [formValues, token, saveLeaderDraft])

  const onSubmit = (data: LeaderFormValues) => {
    addLeader(data, {
      onSuccess: () => {
        navigate(`/s/${token}/members`)
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
              <Crown className="w-6 h-6 text-blue-700" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Group Leader Information</h1>
              <p className="text-sm text-gray-600">Required for TULPS compliance</p>
            </div>
          </div>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          {/* Personal Information */}
          <Card>
            <CardHeader>
              <CardTitle>Personal Information</CardTitle>
              <CardDescription>Required fields for group leader</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Input
                  label="First Name"
                  {...register('first_name')}
                  error={errors.first_name?.message}
                  required
                  placeholder="Mario"
                />
                <Input
                  label="Last Name"
                  {...register('last_name')}
                  error={errors.last_name?.message}
                  required
                  placeholder="Rossi"
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
            </CardContent>
          </Card>

          {/* Document Information */}
          <Card>
            <CardHeader>
              <CardTitle>Document Information</CardTitle>
              <CardDescription>Valid identification document required</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Select
                label="Document Type"
                {...register('document_type')}
                error={errors.document_type?.message}
                required
                options={[
                  { value: '', label: 'Select document type...' },
                  { value: 'passport', label: 'Passport' },
                  { value: 'id_card', label: 'ID Card' },
                  { value: 'driving_license', label: 'Driving License' },
                  { value: 'other', label: 'Other' },
                ]}
              />

              <Input
                label="Document Number"
                {...register('document_number')}
                error={errors.document_number?.message}
                required
                placeholder="AA1234567"
                className="uppercase"
              />

              <Input
                label="Issuing Authority"
                {...register('document_issuing_authority')}
                error={errors.document_issuing_authority?.message}
                required
                placeholder="Ministry of Interior"
              />

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Input
                  label="Issue Date"
                  type="date"
                  {...register('document_issue_date')}
                  error={errors.document_issue_date?.message}
                  required
                />
                <Input
                  label="Issue Place"
                  {...register('document_issue_place')}
                  error={errors.document_issue_place?.message}
                  required
                  placeholder="Roma"
                />
              </div>
            </CardContent>
          </Card>

          {/* Place of Birth (Optional) */}
          <Card>
            <CardHeader>
              <CardTitle>Place of Birth</CardTitle>
              <CardDescription>Optional - helps with TULPS reporting</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Controller
                name="place_of_birth_municipality_code"
                control={control}
                render={({ field }) => (
                  <AutocompleteInput
                    label="Municipality"
                    value={birthMunicipalityQuery}
                    onChange={(query, option) => {
                      setBirthMunicipalityQuery(query)
                      if (option) {
                        field.onChange(option.value)
                      }
                    }}
                    options={
                      birthMunicipalities?.map((m) => ({
                        value: m.istat_code,
                        label: m.name,
                        subtitle: `${m.province_name} - ${m.region_name}`,
                      })) || []
                    }
                    loading={birthMunicipalitiesLoading}
                    error={errors.place_of_birth_municipality_code?.message}
                    placeholder="Start typing municipality name..."
                    helperText="Italian municipality only"
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
                      if (option) {
                        field.onChange(option.value)
                      }
                    }}
                    options={
                      birthCountries?.map((c) => ({
                        value: c.istat_code,
                        label: c.name,
                        subtitle: c.iso_code,
                      })) || []
                    }
                    loading={birthCountriesLoading}
                    error={errors.place_of_birth_country_code?.message}
                    placeholder="Start typing country name..."
                    helperText="For foreign-born guests"
                  />
                )}
              />
            </CardContent>
          </Card>

          {/* Residence (Optional) */}
          <Card>
            <CardHeader>
              <CardTitle>Residence</CardTitle>
              <CardDescription>Optional - permanent address</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Controller
                name="residence_municipality_code"
                control={control}
                render={({ field }) => (
                  <AutocompleteInput
                    label="Municipality"
                    value={residenceMunicipalityQuery}
                    onChange={(query, option) => {
                      setResidenceMunicipalityQuery(query)
                      if (option) {
                        field.onChange(option.value)
                      }
                    }}
                    options={
                      residenceMunicipalities?.map((m) => ({
                        value: m.istat_code,
                        label: m.name,
                        subtitle: `${m.province_name} - ${m.region_name}`,
                      })) || []
                    }
                    loading={residenceMunicipalitiesLoading}
                    error={errors.residence_municipality_code?.message}
                    placeholder="Start typing municipality name..."
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
                      if (option) {
                        field.onChange(option.value)
                      }
                    }}
                    options={
                      residenceCountries?.map((c) => ({
                        value: c.istat_code,
                        label: c.name,
                        subtitle: c.iso_code,
                      })) || []
                    }
                    loading={residenceCountriesLoading}
                    error={errors.residence_country_code?.message}
                    placeholder="Start typing country name..."
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
            </CardContent>
          </Card>

          {/* Citizenship (Optional) */}
          <Card>
            <CardHeader>
              <CardTitle>Citizenship</CardTitle>
              <CardDescription>Optional</CardDescription>
            </CardHeader>
            <CardContent>
              <Controller
                name="citizenship_country_code"
                control={control}
                render={({ field }) => (
                  <AutocompleteInput
                    label="Citizenship Country"
                    value={citizenshipCountryQuery}
                    onChange={(query, option) => {
                      setCitizenshipCountryQuery(query)
                      if (option) {
                        field.onChange(option.value)
                      }
                    }}
                    options={
                      citizenshipCountries?.map((c) => ({
                        value: c.istat_code,
                        label: c.name,
                        subtitle: c.iso_code,
                      })) || []
                    }
                    loading={citizenshipCountriesLoading}
                    error={errors.citizenship_country_code?.message}
                    placeholder="Start typing country name..."
                  />
                )}
              />
            </CardContent>
          </Card>

          {/* Submit Error */}
          {submitError && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-sm text-red-800">{submitError.message}</p>
            </div>
          )}

          {/* Submit Button */}
          <div className="sticky bottom-0 bg-gray-50 pt-4 pb-6 -mx-4 px-4 border-t border-gray-200">
            <Button
              type="submit"
              variant="primary"
              size="lg"
              fullWidth
              loading={isPending}
              className="gap-2"
            >
              Continue to Members
              <ArrowRight className="w-5 h-5" />
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}

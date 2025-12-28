import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft, Save, Loader2 } from 'lucide-react'
import { adminApi } from '@smartbook/api'
import { Card, CardHeader, CardTitle, CardContent, Button, Input } from '@smartbook/ui'
import type { Property, PropertyUpdate } from '@smartbook/types'
import Layout from '../components/Layout'

export default function EditProperty() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [property, setProperty] = useState<Property | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [formData, setFormData] = useState<PropertyUpdate>({
    name: '',
    facility_code: '',
    email: '',
    phone: '',
    ros1000_username: '',
    ros1000_password: '',
    ros1000_ws_key: '',
  })

  useEffect(() => {
    if (id) {
      loadProperty()
    }
  }, [id])

  const loadProperty = async () => {
    if (!id) return

    try {
      setLoading(true)
      const data = await adminApi.getProperty(id) as any
      setProperty(data)
      setFormData({
        name: data.name,
        facility_code: data.facility_code,
        email: data.email,
        phone: data.phone || '',
        ros1000_username: data.ros1000_username || '',
        ros1000_password: '', // Don't pre-fill password
        ros1000_ws_key: data.ros1000_ws_key || '',
      })
    } catch (err) {
      console.error('Failed to load property:', err)
      alert('Failed to load property')
      navigate('/properties')
    } finally {
      setLoading(false)
    }
  }

  const handleInputChange = (field: keyof PropertyUpdate, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }))
    // Clear error for this field
    if (errors[field]) {
      setErrors((prev) => {
        const newErrors = { ...prev }
        delete newErrors[field]
        return newErrors
      })
    }
  }

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {}

    if (formData.name && !formData.name.trim()) {
      newErrors.name = 'Property name cannot be empty'
    }

    if (formData.facility_code && !formData.facility_code.trim()) {
      newErrors.facility_code = 'Facility code cannot be empty'
    }

    if (formData.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Invalid email format'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!validate() || !id) {
      return
    }

    try {
      setSaving(true)
      // Only send fields that have values
      const submitData: any = {}

      if (formData.name?.trim()) submitData.name = formData.name
      if (formData.facility_code?.trim()) submitData.facility_code = formData.facility_code
      if (formData.email?.trim()) submitData.email = formData.email
      if (formData.phone?.trim()) submitData.phone = formData.phone
      if (formData.ros1000_username?.trim()) submitData.ros1000_username = formData.ros1000_username
      if (formData.ros1000_password?.trim()) submitData.ros1000_password = formData.ros1000_password
      if (formData.ros1000_ws_key?.trim()) submitData.ros1000_ws_key = formData.ros1000_ws_key

      await adminApi.updateProperty(id, submitData)
      navigate(`/properties/${id}`)
    } catch (err: any) {
      const message = err.response?.data?.detail || err.message || 'Failed to update property'
      alert(message)
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-96">
          <Loader2 className="w-8 h-8 animate-spin text-gray-900" />
        </div>
      </Layout>
    )
  }

  if (!property) {
    return null
  }

  return (
    <Layout>
      <div className="max-w-3xl mx-auto space-y-6">
        {/* Header */}
        <div>
          <button
            onClick={() => navigate(`/properties/${id}`)}
            className="inline-flex items-center text-sm text-gray-600 hover:text-gray-900 mb-4"
          >
            <ArrowLeft className="w-4 h-4 mr-1" />
            Back to property details
          </button>
          <h1 className="text-3xl font-bold text-gray-900">Edit Property</h1>
          <p className="mt-2 text-sm text-gray-600">
            Update property information
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit}>
          <Card>
            <CardHeader>
              <CardTitle>Property Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Property Name */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Property Name
                </label>
                <Input
                  type="text"
                  value={formData.name}
                  onChange={(e) => handleInputChange('name', e.target.value)}
                  placeholder="Hotel Milano"
                  className={errors.name ? 'border-red-500' : ''}
                />
                {errors.name && (
                  <p className="mt-1 text-sm text-red-500">{errors.name}</p>
                )}
              </div>

              {/* Facility Code */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Facility Code (CIR)
                </label>
                <Input
                  type="text"
                  value={formData.facility_code}
                  onChange={(e) => handleInputChange('facility_code', e.target.value)}
                  placeholder="CIR-12345"
                  className={errors.facility_code ? 'border-red-500' : ''}
                />
                {errors.facility_code && (
                  <p className="mt-1 text-sm text-red-500">{errors.facility_code}</p>
                )}
                <p className="mt-1 text-xs text-gray-500">
                  Codice Struttura assigned by Lombardy Region
                </p>
              </div>

              {/* Email */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Email
                </label>
                <Input
                  type="email"
                  value={formData.email}
                  onChange={(e) => handleInputChange('email', e.target.value)}
                  placeholder="info@hotelmilano.it"
                  className={errors.email ? 'border-red-500' : ''}
                />
                {errors.email && (
                  <p className="mt-1 text-sm text-red-500">{errors.email}</p>
                )}
              </div>

              {/* Phone */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Phone
                </label>
                <Input
                  type="tel"
                  value={formData.phone}
                  onChange={(e) => handleInputChange('phone', e.target.value)}
                  placeholder="+39 02 1234567"
                />
              </div>
            </CardContent>
          </Card>

          <Card className="mt-6">
            <CardHeader>
              <CardTitle>ROS1000 Credentials</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* ROS1000 Username */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  ROS1000 Username
                </label>
                <Input
                  type="text"
                  value={formData.ros1000_username}
                  onChange={(e) => handleInputChange('ros1000_username', e.target.value)}
                  placeholder="hotel_user"
                />
              </div>

              {/* ROS1000 Password */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  ROS1000 Password
                </label>
                <Input
                  type="password"
                  value={formData.ros1000_password}
                  onChange={(e) => handleInputChange('ros1000_password', e.target.value)}
                  placeholder="Leave blank to keep current password"
                />
                <p className="mt-1 text-xs text-gray-500">
                  Leave blank to keep the current password
                </p>
              </div>

              {/* ROS1000 WS Key */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  ROS1000 Web Service Key
                </label>
                <Input
                  type="text"
                  value={formData.ros1000_ws_key}
                  onChange={(e) => handleInputChange('ros1000_ws_key', e.target.value)}
                  placeholder="Web Service Key from Alloggiati Web"
                />
                <p className="mt-1 text-xs text-gray-500">
                  For Questura bridge integration
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Actions */}
          <div className="flex items-center justify-end space-x-3 mt-6">
            <Button
              type="button"
              variant="outline"
              onClick={() => navigate(`/properties/${id}`)}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={saving}
            >
              {saving ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Save className="w-4 h-4 mr-2" />
                  Save Changes
                </>
              )}
            </Button>
          </div>
        </form>
      </div>
    </Layout>
  )
}

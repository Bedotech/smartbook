import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft, Edit, Power, PowerOff, Users, Mail, Phone, Building2, Key, Loader2, UserPlus, X } from 'lucide-react'
import { adminApi } from '@smartbook/api'
import { Card, CardHeader, CardTitle, CardContent, Badge, Button } from '@smartbook/ui'
import type { Property, PropertyUser } from '@smartbook/types'
import Layout from '../components/Layout'
import AssignUserModal from '../components/AssignUserModal'

export default function PropertyDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [property, setProperty] = useState<Property | null>(null)
  const [users, setUsers] = useState<PropertyUser[]>([])
  const [loading, setLoading] = useState(true)
  const [loadingUsers, setLoadingUsers] = useState(false)
  const [showAssignModal, setShowAssignModal] = useState(false)

  useEffect(() => {
    if (id) {
      loadProperty()
      loadUsers()
    }
  }, [id])

  const loadProperty = async () => {
    if (!id) return

    try {
      setLoading(true)
      const data = await adminApi.getProperty(id) as any
      setProperty(data)
    } catch (err) {
      console.error('Failed to load property:', err)
      alert('Failed to load property')
      navigate('/properties')
    } finally {
      setLoading(false)
    }
  }

  const loadUsers = async () => {
    if (!id) return

    try {
      setLoadingUsers(true)
      const data = await adminApi.getPropertyUsers(id) as any
      setUsers(data)
    } catch (err) {
      console.error('Failed to load users:', err)
    } finally {
      setLoadingUsers(false)
    }
  }

  const handleToggleActive = async () => {
    if (!property || !id) return

    if (!confirm(`Are you sure you want to ${property.is_active ? 'deactivate' : 'activate'} this property?`)) {
      return
    }

    try {
      if (property.is_active) {
        await adminApi.deactivateProperty(id)
      } else {
        await adminApi.activateProperty(id)
      }
      loadProperty()
    } catch (err: any) {
      const message = err.response?.data?.detail || err.message || 'Failed to update property status'
      alert(message)
    }
  }

  const handleRemoveUser = async (userId: string) => {
    if (!id) return

    if (!confirm('Are you sure you want to remove this user from the property?')) {
      return
    }

    try {
      await adminApi.removeUserFromProperty(id, userId)
      loadUsers()
    } catch (err: any) {
      const message = err.response?.data?.detail || err.message || 'Failed to remove user'
      alert(message)
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
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <button
              onClick={() => navigate('/properties')}
              className="inline-flex items-center text-sm text-gray-600 hover:text-gray-900 mb-4"
            >
              <ArrowLeft className="w-4 h-4 mr-1" />
              Back to properties
            </button>
            <div className="flex items-center space-x-3">
              <h1 className="text-3xl font-bold text-gray-900">{property.name}</h1>
              <Badge variant={property.is_active ? 'success' : 'error'}>
                {property.is_active ? 'Active' : 'Inactive'}
              </Badge>
            </div>
            <p className="mt-2 text-sm text-gray-600">Property details and configuration</p>
          </div>
          <div className="flex items-center space-x-3">
            <Button
              variant="outline"
              onClick={handleToggleActive}
            >
              {property.is_active ? (
                <>
                  <PowerOff className="w-4 h-4 mr-2" />
                  Deactivate
                </>
              ) : (
                <>
                  <Power className="w-4 h-4 mr-2" />
                  Activate
                </>
              )}
            </Button>
            <Button onClick={() => navigate(`/properties/${id}/edit`)}>
              <Edit className="w-4 h-4 mr-2" />
              Edit Property
            </Button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Property Information */}
          <Card>
            <CardHeader>
              <CardTitle>Property Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-start space-x-3">
                <Building2 className="w-5 h-5 text-gray-400 mt-0.5" />
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-500">Facility Code</p>
                  <p className="text-sm text-gray-900 font-mono">{property.facility_code}</p>
                </div>
              </div>

              <div className="flex items-start space-x-3">
                <Mail className="w-5 h-5 text-gray-400 mt-0.5" />
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-500">Email</p>
                  <a href={`mailto:${property.email}`} className="text-sm text-blue-600 hover:underline">
                    {property.email}
                  </a>
                </div>
              </div>

              {property.phone && (
                <div className="flex items-start space-x-3">
                  <Phone className="w-5 h-5 text-gray-400 mt-0.5" />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-500">Phone</p>
                    <a href={`tel:${property.phone}`} className="text-sm text-blue-600 hover:underline">
                      {property.phone}
                    </a>
                  </div>
                </div>
              )}

              <div className="pt-4 border-t border-gray-200">
                <p className="text-xs text-gray-500">Property ID</p>
                <p className="text-xs font-mono text-gray-700">{property.id}</p>
              </div>
            </CardContent>
          </Card>

          {/* ROS1000 Configuration */}
          <Card>
            <CardHeader>
              <CardTitle>ROS1000 Configuration</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {property.ros1000_username ? (
                <>
                  <div className="flex items-start space-x-3">
                    <Key className="w-5 h-5 text-gray-400 mt-0.5" />
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-500">Username</p>
                      <p className="text-sm text-gray-900">{property.ros1000_username}</p>
                    </div>
                  </div>

                  <div className="flex items-start space-x-3">
                    <Key className="w-5 h-5 text-gray-400 mt-0.5" />
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-500">Password</p>
                      <p className="text-sm text-gray-900">••••••••</p>
                    </div>
                  </div>

                  {property.ros1000_ws_key && (
                    <div className="flex items-start space-x-3">
                      <Key className="w-5 h-5 text-gray-400 mt-0.5" />
                      <div className="flex-1">
                        <p className="text-sm font-medium text-gray-500">Web Service Key</p>
                        <p className="text-sm text-gray-900 font-mono break-all">{property.ros1000_ws_key}</p>
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <div className="text-center py-8">
                  <Key className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                  <p className="text-sm text-gray-500">No ROS1000 credentials configured</p>
                  <Button
                    variant="outline"
                    className="mt-3"
                    onClick={() => navigate(`/properties/${id}/edit`)}
                  >
                    Add Credentials
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Assigned Users */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Assigned Users</CardTitle>
              <Button
                variant="outline"
                onClick={() => setShowAssignModal(true)}
              >
                <UserPlus className="w-4 h-4 mr-2" />
                Assign User
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {loadingUsers ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
              </div>
            ) : users.length === 0 ? (
              <div className="text-center py-8">
                <Users className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                <p className="text-sm text-gray-500">No users assigned to this property</p>
              </div>
            ) : (
              <div className="space-y-3">
                {users.map((user) => (
                  <div
                    key={user.id}
                    className="flex items-center justify-between p-4 border border-gray-200 rounded-lg"
                  >
                    <div className="flex items-center space-x-3">
                      <div className="w-10 h-10 rounded-full bg-gray-200 flex items-center justify-center">
                        <Users className="w-5 h-5 text-gray-600" />
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-900">{user.name}</p>
                        <p className="text-xs text-gray-500">{user.email}</p>
                        <div className="flex items-center space-x-2 mt-1">
                          <Badge variant={user.role === 'admin' ? 'purple' : 'default'}>
                            {user.role}
                          </Badge>
                          <span className="text-xs text-gray-400">
                            Assigned {new Date(user.assigned_at).toLocaleDateString()}
                          </span>
                        </div>
                      </div>
                    </div>
                    <button
                      onClick={() => handleRemoveUser(user.id)}
                      className="text-red-600 hover:text-red-900"
                      title="Remove user"
                    >
                      <X className="w-5 h-5" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Assign User Modal */}
      {showAssignModal && property && (
        <AssignUserModal
          propertyId={property.id}
          propertyName={property.name}
          onClose={() => setShowAssignModal(false)}
          onSuccess={() => {
            loadUsers()
          }}
        />
      )}
    </Layout>
  )
}

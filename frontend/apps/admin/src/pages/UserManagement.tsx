import { useEffect, useState } from 'react'
import { Users, Shield, Building2, CheckCircle, XCircle, Loader2 } from 'lucide-react'
import Layout from '../components/Layout'
import { apiClient } from '@smartbook/api'

interface User {
  id: string
  email: string
  name: string
  role: string
  is_active: boolean
  oauth_provider: string
  oauth_picture_url?: string
  last_login_at?: string
  created_at: string
}

interface PropertyAssignment {
  user_id: string
  property_ids: string[]
  assigned_count: number
}

export default function UserManagement() {
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedUser, setSelectedUser] = useState<User | null>(null)
  const [userProperties, setUserProperties] = useState<PropertyAssignment | null>(null)

  useEffect(() => {
    loadUsers()
  }, [])

  const loadUsers = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await apiClient.get('/api/admin/users') as any
      setUsers(response)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load users')
    } finally {
      setLoading(false)
    }
  }

  const loadUserProperties = async (userId: string) => {
    try {
      const response = await apiClient.get(`/api/admin/users/${userId}/properties`) as any
      setUserProperties(response)
    } catch (err) {
      console.error('Failed to load user properties:', err)
    }
  }

  const handleUserClick = async (user: User) => {
    setSelectedUser(user)
    await loadUserProperties(user.id)
  }

  const handleToggleActive = async (userId: string, isActive: boolean) => {
    try {
      const endpoint = isActive
        ? `/api/admin/users/${userId}/deactivate`
        : `/api/admin/users/${userId}/activate`

      await apiClient.patch(endpoint)
      await loadUsers()

      // Reload selected user if it was the one being toggled
      if (selectedUser?.id === userId) {
        const updatedUser = users.find(u => u.id === userId)
        if (updatedUser) {
          setSelectedUser({ ...updatedUser, is_active: !isActive })
        }
      }
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to update user status')
    }
  }

  const formatDate = (dateString: string | undefined) => {
    if (!dateString) return 'Never'
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-96">
          <div className="text-center">
            <Loader2 className="w-12 h-12 animate-spin text-blue-600 mx-auto mb-4" />
            <p className="text-slate-600 font-medium">Loading users...</p>
          </div>
        </div>
      </Layout>
    )
  }

  if (error) {
    return (
      <Layout>
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <div className="flex items-start space-x-3">
            <XCircle className="h-6 w-6 text-red-600 mt-0.5" />
            <div>
              <h3 className="text-lg font-semibold text-red-900">Error loading users</h3>
              <p className="mt-1 text-sm text-red-700">{error}</p>
              <button
                onClick={loadUsers}
                className="mt-4 px-4 py-2 bg-red-600 text-white text-sm font-medium rounded-lg hover:bg-red-700 transition-colors"
              >
                Try again
              </button>
            </div>
          </div>
        </div>
      </Layout>
    )
  }

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900">User Management</h1>
          <p className="mt-2 text-gray-600">
            Manage users and their property assignments
          </p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Users</p>
                <p className="mt-2 text-3xl font-bold text-gray-900">{users.length}</p>
              </div>
              <Users className="w-12 h-12 text-blue-600 opacity-20" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Active Users</p>
                <p className="mt-2 text-3xl font-bold text-green-600">
                  {users.filter(u => u.is_active).length}
                </p>
              </div>
              <CheckCircle className="w-12 h-12 text-green-600 opacity-20" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Administrators</p>
                <p className="mt-2 text-3xl font-bold text-purple-600">
                  {users.filter(u => u.role === 'admin').length}
                </p>
              </div>
              <Shield className="w-12 h-12 text-purple-600 opacity-20" />
            </div>
          </div>
        </div>

        {/* Users List */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* List View */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">Users</h2>
            </div>
            <div className="divide-y divide-gray-200 max-h-[600px] overflow-y-auto">
              {users.map((user) => (
                <button
                  key={user.id}
                  onClick={() => handleUserClick(user)}
                  className={`w-full px-6 py-4 hover:bg-gray-50 transition-colors text-left ${
                    selectedUser?.id === user.id ? 'bg-blue-50 border-l-4 border-l-blue-600' : ''
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-center space-x-3">
                      {user.oauth_picture_url ? (
                        <img
                          src={user.oauth_picture_url}
                          alt={user.name}
                          className="w-10 h-10 rounded-full"
                        />
                      ) : (
                        <div className="w-10 h-10 rounded-full bg-gray-200 flex items-center justify-center">
                          <Users className="w-5 h-5 text-gray-600" />
                        </div>
                      )}
                      <div>
                        <p className="font-medium text-gray-900">{user.name}</p>
                        <p className="text-sm text-gray-500">{user.email}</p>
                        <div className="flex items-center gap-2 mt-1">
                          <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                            user.role === 'admin'
                              ? 'bg-purple-100 text-purple-800'
                              : 'bg-gray-100 text-gray-800'
                          }`}>
                            {user.role === 'admin' ? 'Admin' : 'Staff'}
                          </span>
                          {user.is_active ? (
                            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                              Active
                            </span>
                          ) : (
                            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800">
                              Inactive
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Detail View */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">User Details</h2>
            </div>
            <div className="p-6">
              {selectedUser ? (
                <div className="space-y-6">
                  {/* User Info */}
                  <div className="flex items-center space-x-4">
                    {selectedUser.oauth_picture_url ? (
                      <img
                        src={selectedUser.oauth_picture_url}
                        alt={selectedUser.name}
                        className="w-16 h-16 rounded-full"
                      />
                    ) : (
                      <div className="w-16 h-16 rounded-full bg-gray-200 flex items-center justify-center">
                        <Users className="w-8 h-8 text-gray-600" />
                      </div>
                    )}
                    <div>
                      <h3 className="text-xl font-bold text-gray-900">{selectedUser.name}</h3>
                      <p className="text-gray-600">{selectedUser.email}</p>
                    </div>
                  </div>

                  {/* User Metadata */}
                  <div className="grid grid-cols-2 gap-4 pt-4 border-t border-gray-200">
                    <div>
                      <p className="text-sm font-medium text-gray-600">Role</p>
                      <p className="mt-1 text-sm text-gray-900 capitalize">{selectedUser.role}</p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-600">Status</p>
                      <p className="mt-1 text-sm text-gray-900">
                        {selectedUser.is_active ? 'Active' : 'Inactive'}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-600">OAuth Provider</p>
                      <p className="mt-1 text-sm text-gray-900 capitalize">
                        {selectedUser.oauth_provider}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-600">Last Login</p>
                      <p className="mt-1 text-sm text-gray-900">
                        {formatDate(selectedUser.last_login_at)}
                      </p>
                    </div>
                    <div className="col-span-2">
                      <p className="text-sm font-medium text-gray-600">Created</p>
                      <p className="mt-1 text-sm text-gray-900">
                        {formatDate(selectedUser.created_at)}
                      </p>
                    </div>
                  </div>

                  {/* Property Assignments */}
                  <div className="pt-4 border-t border-gray-200">
                    <div className="flex items-center gap-2 mb-3">
                      <Building2 className="w-5 h-5 text-gray-600" />
                      <h4 className="font-semibold text-gray-900">Property Assignments</h4>
                    </div>
                    {userProperties ? (
                      <div className="bg-gray-50 rounded-lg p-4">
                        <p className="text-sm text-gray-600">
                          Assigned to{' '}
                          <span className="font-semibold text-gray-900">
                            {userProperties.assigned_count}
                          </span>{' '}
                          {userProperties.assigned_count === 1 ? 'property' : 'properties'}
                        </p>
                        {userProperties.property_ids.length > 0 && (
                          <div className="mt-2 space-y-1">
                            {userProperties.property_ids.map((propertyId) => (
                              <div
                                key={propertyId}
                                className="text-xs font-mono text-gray-700 bg-white px-2 py-1 rounded"
                              >
                                {propertyId}
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    ) : (
                      <div className="flex items-center justify-center h-20">
                        <Loader2 className="w-5 h-5 animate-spin text-gray-400" />
                      </div>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="pt-4 border-t border-gray-200">
                    <button
                      onClick={() => handleToggleActive(selectedUser.id, selectedUser.is_active)}
                      className={`w-full px-4 py-2 rounded-lg font-medium transition-colors ${
                        selectedUser.is_active
                          ? 'bg-red-600 text-white hover:bg-red-700'
                          : 'bg-green-600 text-white hover:bg-green-700'
                      }`}
                    >
                      {selectedUser.is_active ? 'Deactivate User' : 'Activate User'}
                    </button>
                  </div>
                </div>
              ) : (
                <div className="text-center py-12">
                  <Users className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                  <p className="text-gray-500">Select a user to view details</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </Layout>
  )
}

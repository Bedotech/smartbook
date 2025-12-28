import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Building2, Search, Plus, Edit, Power, PowerOff, Users, Loader2 } from 'lucide-react'
import { adminApi } from '@smartbook/api'
import { Card, CardContent, Badge, Button, Input } from '@smartbook/ui'
import type { Property } from '@smartbook/types'
import Layout from '../components/Layout'

export default function PropertiesList() {
  const navigate = useNavigate()
  const [properties, setProperties] = useState<Property[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [filterActive, setFilterActive] = useState<boolean | undefined>(undefined)

  useEffect(() => {
    loadProperties()
  }, [filterActive])

  const loadProperties = async () => {
    try {
      setLoading(true)
      const params: any = {}
      if (searchTerm) params.search = searchTerm
      if (filterActive !== undefined) params.is_active = filterActive

      const data = await adminApi.getProperties(params) as any
      setProperties(data)
    } catch (err) {
      console.error('Failed to load properties:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = () => {
    loadProperties()
  }

  const handleToggleActive = async (property: Property) => {
    if (!confirm(`Are you sure you want to ${property.is_active ? 'deactivate' : 'activate'} "${property.name}"?`)) {
      return
    }

    try {
      if (property.is_active) {
        await adminApi.deactivateProperty(property.id)
      } else {
        await adminApi.activateProperty(property.id)
      }
      loadProperties()
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to update property status')
    }
  }

  const filteredProperties = properties.filter((property) => {
    if (!searchTerm) return true
    const search = searchTerm.toLowerCase()
    return (
      property.name.toLowerCase().includes(search) ||
      property.facility_code.toLowerCase().includes(search) ||
      property.email.toLowerCase().includes(search)
    )
  })

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Properties</h1>
            <p className="mt-2 text-sm text-gray-600">Manage all properties in the system</p>
          </div>
          <Link
            to="/properties/new"
            className="inline-flex items-center px-4 py-2 bg-gray-900 text-white text-sm font-medium rounded-lg hover:bg-gray-800"
          >
            <Plus className="w-4 h-4 mr-2" />
            Create Property
          </Link>
        </div>

        {/* Filters */}
        <Card>
          <CardContent className="!p-4">
            <div className="flex items-center space-x-3">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                <Input
                  type="text"
                  placeholder="Search by name, facility code, or email..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                  className="pl-10"
                />
              </div>
              <Button variant="outline" onClick={handleSearch}>
                Search
              </Button>
            </div>
            <div className="flex items-center space-x-3 mt-3">
              <span className="text-sm font-medium text-gray-700">Status:</span>
              <button
                onClick={() => setFilterActive(undefined)}
                className={`px-3 py-1 text-sm rounded ${
                  filterActive === undefined
                    ? 'bg-gray-900 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                All
              </button>
              <button
                onClick={() => setFilterActive(true)}
                className={`px-3 py-1 text-sm rounded ${
                  filterActive === true
                    ? 'bg-green-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                Active
              </button>
              <button
                onClick={() => setFilterActive(false)}
                className={`px-3 py-1 text-sm rounded ${
                  filterActive === false
                    ? 'bg-red-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                Inactive
              </button>
            </div>
          </CardContent>
        </Card>

        {/* Properties List */}
        <Card>
          <CardContent>
            {loading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="w-8 h-8 animate-spin text-gray-900" />
              </div>
            ) : filteredProperties.length === 0 ? (
              <div className="text-center py-12">
                <Building2 className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                <p className="text-gray-900 font-medium">No properties found</p>
                <p className="text-sm text-gray-500 mt-1">
                  {searchTerm
                    ? 'Try adjusting your search terms'
                    : 'Create your first property to get started'}
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Property
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Facility Code
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Contact
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Status
                      </th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {filteredProperties.map((property) => (
                      <tr key={property.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center">
                            <Building2 className="w-5 h-5 text-gray-400 mr-3" />
                            <div>
                              <div className="text-sm font-medium text-gray-900">{property.name}</div>
                              <div className="text-xs text-gray-500">{property.id.slice(0, 8)}</div>
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-900 font-mono">{property.facility_code}</div>
                        </td>
                        <td className="px-6 py-4">
                          <div className="text-sm text-gray-900">{property.email}</div>
                          {property.phone && (
                            <div className="text-xs text-gray-500">{property.phone}</div>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <Badge variant={property.is_active ? 'success' : 'error'}>
                            {property.is_active ? 'Active' : 'Inactive'}
                          </Badge>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                          <div className="flex items-center justify-end space-x-2">
                            <button
                              onClick={() => navigate(`/properties/${property.id}`)}
                              className="text-gray-600 hover:text-gray-900"
                              title="View Details"
                            >
                              <Users className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => navigate(`/properties/${property.id}/edit`)}
                              className="text-blue-600 hover:text-blue-900"
                              title="Edit"
                            >
                              <Edit className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => handleToggleActive(property)}
                              className={property.is_active ? 'text-red-600 hover:text-red-900' : 'text-green-600 hover:text-green-900'}
                              title={property.is_active ? 'Deactivate' : 'Activate'}
                            >
                              {property.is_active ? (
                                <PowerOff className="w-4 h-4" />
                              ) : (
                                <Power className="w-4 h-4" />
                              )}
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </Layout>
  )
}

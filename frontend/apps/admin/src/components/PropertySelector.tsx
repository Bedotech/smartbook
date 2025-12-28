import { Building2, ChevronDown } from 'lucide-react'
import { useProperty } from '../contexts/PropertyContext'

export default function PropertySelector() {
  const { selectedPropertyId, setSelectedPropertyId, properties, loading } = useProperty()

  if (loading) {
    return (
      <div className="flex items-center gap-2 px-3 py-2 bg-gray-100 rounded-lg animate-pulse">
        <Building2 className="w-4 h-4 text-gray-400" />
        <div className="h-4 w-32 bg-gray-200 rounded"></div>
      </div>
    )
  }

  if (properties.length === 0) {
    return (
      <div className="flex items-center gap-2 px-3 py-2 bg-yellow-50 text-yellow-800 rounded-lg text-sm">
        <Building2 className="w-4 h-4" />
        <span>No properties assigned</span>
      </div>
    )
  }

  // Single property - show as label
  if (properties.length === 1) {
    return (
      <div className="flex items-center gap-2 px-3 py-2 bg-gray-50 rounded-lg">
        <Building2 className="w-4 h-4 text-gray-600" />
        <span className="text-sm font-medium text-gray-900">{properties[0].name}</span>
      </div>
    )
  }

  // Multiple properties - show as dropdown
  return (
    <div className="relative">
      <div className="flex items-center gap-2">
        <Building2 className="w-4 h-4 text-gray-600" />
        <select
          value={selectedPropertyId || ''}
          onChange={(e) => setSelectedPropertyId(e.target.value)}
          className="appearance-none bg-white border border-gray-300 rounded-lg pl-2 pr-8 py-2 text-sm font-medium text-gray-900 hover:border-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-transparent cursor-pointer"
        >
          {properties.map((property) => (
            <option key={property.id} value={property.id}>
              {property.name}
            </option>
          ))}
        </select>
        <ChevronDown className="w-4 h-4 text-gray-400 pointer-events-none absolute right-2" />
      </div>
    </div>
  )
}

import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { useAuth } from '../hooks/useAuth'

interface Property {
  id: string
  name: string
}

interface PropertyContextType {
  selectedPropertyId: string | null
  setSelectedPropertyId: (id: string) => void
  properties: Property[]
  loading: boolean
}

const PropertyContext = createContext<PropertyContextType | undefined>(undefined)

interface PropertyProviderProps {
  children: ReactNode
}

export function PropertyProvider({ children }: PropertyProviderProps) {
  const { user, isAuthenticated } = useAuth()
  const [selectedPropertyId, setSelectedPropertyId] = useState<string | null>(null)
  const [properties, setProperties] = useState<Property[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!isAuthenticated || !user) {
      setProperties([])
      setSelectedPropertyId(null)
      setLoading(false)
      return
    }

    // For now, we only have property IDs from JWT
    // In a real app, we'd fetch property details from API
    const userProperties: Property[] = user.property_ids.map((id) => ({
      id,
      name: `Property ${id.substring(0, 8)}`, // Placeholder - will be replaced with real names
    }))

    setProperties(userProperties)

    // Auto-select first property if none selected
    if (userProperties.length > 0 && !selectedPropertyId) {
      const savedPropertyId = localStorage.getItem('selected_property_id')

      // Check if saved property is still valid
      if (savedPropertyId && userProperties.some((p) => p.id === savedPropertyId)) {
        setSelectedPropertyId(savedPropertyId)
      } else {
        setSelectedPropertyId(userProperties[0].id)
      }
    }

    setLoading(false)
  }, [user, isAuthenticated, selectedPropertyId])

  // Save selected property to localStorage
  useEffect(() => {
    if (selectedPropertyId) {
      localStorage.setItem('selected_property_id', selectedPropertyId)
    }
  }, [selectedPropertyId])

  const value: PropertyContextType = {
    selectedPropertyId,
    setSelectedPropertyId,
    properties,
    loading,
  }

  return <PropertyContext.Provider value={value}>{children}</PropertyContext.Provider>
}

export function useProperty() {
  const context = useContext(PropertyContext)
  if (context === undefined) {
    throw new Error('useProperty must be used within a PropertyProvider')
  }
  return context
}

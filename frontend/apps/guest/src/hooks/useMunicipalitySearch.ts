import { useQuery } from '@tanstack/react-query'
import { guestApi } from '@smartbook/api'
import type { Municipality } from '@smartbook/types'
import { useDebouncedValue } from './useDebouncedValue'

export function useMunicipalitySearch(query: string, enabled = true) {
  const debouncedQuery = useDebouncedValue(query, 300)

  return useQuery<Municipality[], Error>({
    queryKey: ['municipalities', debouncedQuery],
    queryFn: () => guestApi.searchMunicipalities(debouncedQuery, 10),
    enabled: enabled && debouncedQuery.length >= 2,
    staleTime: 10 * 60 * 1000, // 10 minutes - municipalities rarely change
  })
}

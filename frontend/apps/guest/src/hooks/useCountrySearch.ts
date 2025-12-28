import { useQuery } from '@tanstack/react-query'
import { guestApi } from '@smartbook/api'
import type { Country } from '@smartbook/types'
import { useDebouncedValue } from './useDebouncedValue'

export function useCountrySearch(query: string, enabled = true) {
  const debouncedQuery = useDebouncedValue(query, 300)

  return useQuery<Country[], Error>({
    queryKey: ['countries', debouncedQuery],
    queryFn: () => guestApi.searchCountries(debouncedQuery, 10),
    enabled: enabled && debouncedQuery.length >= 2,
    staleTime: 10 * 60 * 1000, // 10 minutes
  })
}

import { useQuery } from '@tanstack/react-query'
import { guestApi } from '@smartbook/api'
import type { Property } from '@smartbook/types'

export function useProperty(token: string) {
  return useQuery<Property, Error>({
    queryKey: ['property', token],
    queryFn: () => guestApi.getProperty(token),
    staleTime: 60 * 60 * 1000, // 1 hour (property info rarely changes)
    retry: 3,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  })
}

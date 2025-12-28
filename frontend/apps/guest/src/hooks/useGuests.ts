import { useQuery } from '@tanstack/react-query'
import { guestApi } from '@smartbook/api'
import type { Guest } from '@smartbook/types'

export function useGuests(token: string, enabled = true) {
  return useQuery<Guest[], Error>({
    queryKey: ['booking', token, 'guests'],
    queryFn: () => guestApi.getGuests(token),
    enabled,
    staleTime: 1 * 60 * 1000, // 1 minute
  })
}

import { useQuery } from '@tanstack/react-query'
import { guestApi } from '@smartbook/api'
import type { BookingProgress } from '@smartbook/types'

export function useBookingProgress(token: string, enabled = true) {
  return useQuery<BookingProgress, Error>({
    queryKey: ['booking', token, 'progress'],
    queryFn: () => guestApi.getProgress(token),
    enabled,
    refetchInterval: 5000, // Poll every 5 seconds when active
    staleTime: 0, // Always fresh
    retry: 2,
  })
}

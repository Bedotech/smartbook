import { useQuery } from '@tanstack/react-query'
import { guestApi } from '@smartbook/api'
import type { Booking } from '@smartbook/types'

export function useBooking(token: string) {
  return useQuery<Booking, Error>({
    queryKey: ['booking', token],
    queryFn: () => guestApi.getBooking(token),
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 3,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  })
}

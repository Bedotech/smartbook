import { useMutation, useQueryClient } from '@tanstack/react-query'
import { guestApi } from '@smartbook/api'
import type { Booking } from '@smartbook/types'

export function useCompleteBooking(token: string) {
  const queryClient = useQueryClient()

  return useMutation<Booking, Error, void>({
    mutationFn: () => guestApi.completeBooking(token),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['booking', token] })
    },
    retry: 1,
  })
}

import { useMutation, useQueryClient } from '@tanstack/react-query'
import { guestApi } from '@smartbook/api'
import type { MemberFormData, Guest } from '@smartbook/types'

export function useAddMember(token: string) {
  const queryClient = useQueryClient()

  return useMutation<Guest, Error, MemberFormData>({
    mutationFn: (data) => guestApi.addMember(token, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['booking', token, 'progress'] })
      queryClient.invalidateQueries({ queryKey: ['booking', token, 'guests'] })
    },
    retry: 2,
  })
}

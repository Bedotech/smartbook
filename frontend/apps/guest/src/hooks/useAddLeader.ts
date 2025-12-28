import { useMutation, useQueryClient } from '@tanstack/react-query'
import { guestApi } from '@smartbook/api'
import type { LeaderFormData, Guest } from '@smartbook/types'
import { useOfflineStore } from '../stores/offlineStore'

export function useAddLeader(token: string) {
  const queryClient = useQueryClient()
  const { clearLeaderDraft } = useOfflineStore()

  return useMutation<Guest, Error, LeaderFormData>({
    mutationFn: (data) => guestApi.addLeader(token, data),
    onSuccess: () => {
      // Invalidate all related queries
      queryClient.invalidateQueries({ queryKey: ['booking', token, 'progress'] })
      queryClient.invalidateQueries({ queryKey: ['booking', token, 'guests'] })
      // Clear offline draft
      clearLeaderDraft(token)
    },
    retry: 2,
  })
}

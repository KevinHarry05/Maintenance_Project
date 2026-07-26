'use client'

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { notificationService } from '@/services/notificationService'

const notificationKeys = {
  all: ['notifications'] as const,
}

export function useNotifications() {
  return useQuery({
    queryKey: notificationKeys.all,
    queryFn: notificationService.getNotifications,
  })
}

export function useMarkNotificationAsRead() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => notificationService.markAsRead(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: notificationKeys.all })
    },
  })
}

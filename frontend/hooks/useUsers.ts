'use client'

import { useQuery } from '@tanstack/react-query'
import { userService } from '@/services/userService'

const userKeys = {
  workers: ['users', 'workers'] as const,
}

export function useWorkers() {
  return useQuery({
    queryKey: userKeys.workers,
    queryFn: userService.getWorkers,
  })
}

'use client'

import { useEffect } from 'react'
import { createNotificationSocket } from '@/lib/websocket'
import type { NotificationEvent } from '@/types/notification'

type UseWebSocketOptions = {
  enabled?: boolean
  onMessage: (event: NotificationEvent) => void
}

export function useWebSocket({ enabled = true, onMessage }: UseWebSocketOptions) {
  useEffect(() => {
    if (!enabled) return

    const socket = createNotificationSocket(onMessage)

    return () => {
      socket.close()
    }
  }, [enabled, onMessage])
}

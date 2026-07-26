import { API_ROUTES } from '@/routes/apiRoutes'
import type { NotificationEvent } from '@/types/notification'

export function createNotificationSocket(
  onEvent: (event: NotificationEvent) => void,
): WebSocket {
  const apiUrl =
    process.env.NEXT_PUBLIC_API_URL ||
    (typeof window !== 'undefined' ? window.location.origin : 'http://127.0.0.1:8000')
  const wsProtocol = apiUrl.startsWith('https') ? 'wss' : 'ws'
  const wsHost = apiUrl.replace(/^https?:\/\//, '')
  const token = typeof window !== 'undefined' ? localStorage.getItem('sbms_access_token') : null

  const wsUrl = `${wsProtocol}://${wsHost}${API_ROUTES.WS_NOTIFICATIONS}${token ? `?token=${token}` : ''}`
  const socket = new WebSocket(wsUrl)

  socket.onmessage = (event) => {
    try {
      const payload = JSON.parse(event.data) as NotificationEvent
      onEvent(payload)
    } catch {
      // Ignore malformed event payloads.
    }
  }

  return socket
}

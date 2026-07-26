import { apiGet, apiPut } from '@/lib/api'
import { API_ROUTES } from '@/routes/apiRoutes'
import type { Notification } from '@/types/notification'

export const notificationService = {
  getNotifications: () => apiGet<Notification[]>(API_ROUTES.NOTIFICATIONS),

  markAsRead: (id: string) =>
    apiPut<Notification, Record<string, never>>(API_ROUTES.NOTIFICATION_MARK_READ(id), {}),
}

export interface Notification {
  id: string
  user_id?: string
  complaint_id?: string | null
  title: string
  message: string
  notification_type?: string
  is_read: boolean
  created_at?: string
}

export interface NotificationEvent {
  type: string
  payload: Notification
}

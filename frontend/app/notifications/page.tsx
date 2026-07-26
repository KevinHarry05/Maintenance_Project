import { NotificationList } from '@/components/notifications/NotificationList'

export default function NotificationsPage() {
  return (
    <div className="mx-auto max-w-4xl space-y-6 py-8">
      <h1 className="text-3xl font-bold text-foreground">Notifications</h1>
      <NotificationList />
    </div>
  )
}

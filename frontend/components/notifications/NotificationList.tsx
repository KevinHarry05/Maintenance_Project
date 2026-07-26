'use client'

import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useMarkNotificationAsRead, useNotifications } from '@/hooks/useNotifications'

export function NotificationList() {
  const { data, isLoading } = useNotifications()
  const markRead = useMarkNotificationAsRead()

  if (isLoading) return <p>Loading notifications...</p>

  return (
    <div className="space-y-3">
      {data?.map((item) => (
        <Card key={item.id} className="p-4">
          <p className="font-semibold">{item.title}</p>
          <p className="text-sm text-muted-foreground">{item.message}</p>
          {!item.is_read ? (
            <Button size="sm" variant="outline" className="mt-3" onClick={() => markRead.mutate(item.id)}>
              Mark as read
            </Button>
          ) : null}
        </Card>
      ))}
    </div>
  )
}

'use client'

import { Bell } from 'lucide-react'
import { useNotifications } from '@/hooks/useNotifications'

export function NotificationBell() {
  const { data } = useNotifications()
  const unread = data?.filter((item) => !item.is_read).length || 0

  return (
    <div className="relative inline-flex">
      <Bell className="h-5 w-5" />
      {unread > 0 ? (
        <span className="absolute -right-2 -top-2 rounded-full bg-red-500 px-1.5 text-xs text-white">
          {unread}
        </span>
      ) : null}
    </div>
  )
}

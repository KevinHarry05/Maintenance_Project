'use client';

import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Bell, CheckCircle2, AlertCircle, Info } from 'lucide-react';
import { useNotifications, useMarkNotificationAsRead } from '@/hooks/useNotifications';

function NotificationIcon({ type }: { type?: string }) {
  if (type === 'resolved') return (
    <div className="w-10 h-10 bg-green-500/20 rounded-full flex items-center justify-center">
      <CheckCircle2 className="w-6 h-6 text-green-500" />
    </div>
  );
  if (type === 'assigned') return (
    <div className="w-10 h-10 bg-purple-500/20 rounded-full flex items-center justify-center">
      <AlertCircle className="w-6 h-6 text-purple-500" />
    </div>
  );
  if (type === 'info') return (
    <div className="w-10 h-10 bg-accent/20 rounded-full flex items-center justify-center">
      <Info className="w-6 h-6 text-accent" />
    </div>
  );
  return (
    <div className="w-10 h-10 bg-blue-500/20 rounded-full flex items-center justify-center">
      <Bell className="w-6 h-6 text-blue-500" />
    </div>
  );
}

export default function AdminNotificationsPage() {
  const { data: notifications = [], isLoading } = useNotifications();
  const markRead = useMarkNotificationAsRead();

  const unreadCount = notifications.filter((n) => !n.is_read).length;

  const handleMarkAll = () => {
    notifications.filter((n) => !n.is_read).forEach((n) => markRead.mutate(n.id));
  };

  return (
    <div className="space-y-8 max-w-4xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Notifications</h1>
          <p className="text-muted-foreground">System notifications and alerts</p>
        </div>
        {unreadCount > 0 && (
          <Button variant="outline" className="border-border hover:bg-card text-foreground" onClick={handleMarkAll}>
            Mark all as read
          </Button>
        )}
      </div>

      {isLoading ? (
        <p className="text-muted-foreground">Loading notifications…</p>
      ) : notifications.length > 0 ? (
        <div className="space-y-3">
          {notifications.map((n) => (
            <Card
              key={n.id}
              className={`border-border p-4 transition-colors ${!n.is_read ? 'bg-primary/5 hover:bg-primary/10' : 'bg-card hover:bg-card/80'}`}
            >
              <div className="flex items-start gap-4">
                <div className="flex-shrink-0 mt-1">
                  <NotificationIcon type={n.notification_type} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <h3 className="font-semibold text-foreground">{n.title}</h3>
                      <p className="text-muted-foreground text-sm mt-1">{n.message}</p>
                      {n.created_at && (
                        <p className="text-xs text-muted-foreground mt-2">
                          {new Date(n.created_at).toLocaleString()}
                        </p>
                      )}
                    </div>
                    {!n.is_read && <div className="w-2 h-2 bg-primary rounded-full flex-shrink-0 mt-2" />}
                  </div>
                </div>
                {!n.is_read && (
                  <Button
                    size="sm"
                    variant="ghost"
                    className="text-muted-foreground hover:text-primary hover:bg-primary/10"
                    onClick={() => markRead.mutate(n.id)}
                  >
                    Mark read
                  </Button>
                )}
              </div>
            </Card>
          ))}
        </div>
      ) : (
        <Card className="bg-card border-border p-12 text-center">
          <Bell className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-foreground mb-2">No notifications</h3>
          <p className="text-muted-foreground">System alerts and notifications will appear here.</p>
        </Card>
      )}
    </div>
  );
}

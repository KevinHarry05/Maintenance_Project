'use client';

import { Card } from '@/components/ui/card';
import { Users } from 'lucide-react';
import { useWorkers } from '@/hooks/useUsers';

export default function StaffManagementPage() {
  const { data: workers = [], isLoading } = useWorkers();

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Worker Management</h1>
          <p className="text-muted-foreground">View active maintenance workers</p>
        </div>
      </div>

      {isLoading ? (
        <p className="text-muted-foreground">Loading workers...</p>
      ) : workers.length === 0 ? (
        <Card className="bg-card border-border p-6 text-muted-foreground">
          No workers found. Register users with the worker role to assign complaints.
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {workers.map((worker) => (
            <Card key={worker.id} className="bg-card border-border p-6">
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-primary/20 rounded-full flex items-center justify-center">
                  <Users className="w-6 h-6 text-primary" />
                </div>
                <div>
                  <h3 className="font-semibold text-foreground">{worker.name}</h3>
                  <p className="text-xs text-muted-foreground">Maintenance Worker</p>
                </div>
              </div>
            </div>

            <div className="space-y-2 mb-4 pb-4 border-b border-border">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Role</span>
                <span className="text-foreground capitalize">{worker.role}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Email</span>
                <span className="text-foreground text-xs">{worker.email}</span>
              </div>
            </div>
          </Card>
          ))}
        </div>
      )}
    </div>
  );
}

'use client';

import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts';
import { CheckCircle2, Clock, Wrench } from 'lucide-react';
import Link from 'next/link';
import { useAuthContext } from '@/context/AuthContext';
import { useAssignedComplaints, useUploadResolution } from '@/hooks/useComplaints';
import { useState } from 'react';

function getLastSevenDaysCompletionData(complaints: { status: string; created_at?: string }[]) {
  const now = new Date();
  const days = Array.from({ length: 7 }, (_, i) => {
    const d = new Date(now);
    d.setDate(now.getDate() - (6 - i));
    d.setHours(0, 0, 0, 0);
    return {
      key: `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`,
      day: d.toLocaleString('en-US', { weekday: 'short' }),
      completed: 0,
    };
  });

  const dayMap = new Map(days.map((d) => [d.key, d]));

  complaints.forEach((complaint) => {
    if (complaint.status !== 'resolved' || !complaint.created_at) return;
    const created = new Date(complaint.created_at);
    if (Number.isNaN(created.getTime())) return;
    const key = `${created.getFullYear()}-${String(created.getMonth() + 1).padStart(2, '0')}-${String(created.getDate()).padStart(2, '0')}`;
    const bucket = dayMap.get(key);
    if (!bucket) return;
    bucket.completed += 1;
  });

  return days;
}

export default function StaffDashboard() {
  const { user } = useAuthContext();
  const { data: complaints = [], isLoading } = useAssignedComplaints();
  const uploadResolution = useUploadResolution();
  const [updatingId, setUpdatingId] = useState<string | null>(null);
  const completionData = getLastSevenDaysCompletionData(complaints);

  const inProgressCount = complaints.filter((c) => c.status === 'in_progress').length;
  const resolvedCount = complaints.filter((c) => c.status === 'resolved').length;

  const handleMarkResolved = async (id: string) => {
    setUpdatingId(id);
    try {
      await uploadResolution.mutateAsync({ id, file: null });
    } finally {
      setUpdatingId(null);
    }
  };

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Worker Dashboard</h1>
          <p className="text-muted-foreground">Manage tasks assigned to {user?.full_name ?? 'Worker'}</p>
        </div>
        <Link href="/dashboard/worker/complaints">
          <Button className="bg-primary hover:bg-primary-dark text-primary-foreground gap-2">
            <Wrench className="w-5 h-5" />
            View All Tasks
          </Button>
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="bg-card border-border p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-muted-foreground text-sm font-medium">Assigned Tasks</p>
              <p className="text-3xl font-bold text-foreground mt-2">{isLoading ? '…' : complaints.length}</p>
            </div>
            <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center">
              <Wrench className="w-6 h-6 text-primary" />
            </div>
          </div>
        </Card>

        <Card className="bg-card border-border p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-muted-foreground text-sm font-medium">In Progress</p>
              <p className="text-3xl font-bold text-foreground mt-2">{isLoading ? '…' : inProgressCount}</p>
            </div>
            <div className="w-12 h-12 bg-accent/10 rounded-lg flex items-center justify-center">
              <Clock className="w-6 h-6 text-accent" />
            </div>
          </div>
        </Card>

        <Card className="bg-card border-border p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-muted-foreground text-sm font-medium">Resolved</p>
              <p className="text-3xl font-bold text-foreground mt-2">{isLoading ? '…' : resolvedCount}</p>
            </div>
            <div className="w-12 h-12 bg-green-500/10 rounded-lg flex items-center justify-center">
              <CheckCircle2 className="w-6 h-6 text-green-500" />
            </div>
          </div>
        </Card>
      </div>

      <Card className="bg-card border-border p-6">
        <h2 className="text-lg font-semibold text-foreground mb-6">Completion Rate - Last 7 Days</h2>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={completionData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis dataKey="day" stroke="#9CA3AF" />
            <YAxis stroke="#9CA3AF" />
            <Tooltip contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #4B5563' }} />
            <Line type="monotone" dataKey="completed" stroke="#3B82F6" strokeWidth={2} dot={{ fill: '#3B82F6' }} />
          </LineChart>
        </ResponsiveContainer>
      </Card>

      <Card className="bg-card border-border overflow-hidden">
        <div className="p-6 border-b border-border">
          <h2 className="text-lg font-semibold text-foreground">Currently Assigned Tasks</h2>
        </div>
        <div className="overflow-x-auto">
          {isLoading ? (
            <p className="p-6 text-muted-foreground">Loading tasks…</p>
          ) : complaints.length === 0 ? (
            <p className="p-6 text-muted-foreground">No tasks assigned yet.</p>
          ) : (
            <table className="w-full">
              <thead className="bg-card/50 border-b border-border">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-muted-foreground">ID</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-muted-foreground">Title</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-muted-foreground">Priority</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-muted-foreground">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-muted-foreground">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {complaints.map((c) => (
                  <tr key={c.id} className="hover:bg-card/50 transition-colors">
                    <td className="px-6 py-4 text-sm font-mono text-primary">{c.id.slice(0, 8)}…</td>
                    <td className="px-6 py-4 text-sm text-foreground">{c.title}</td>
                    <td className="px-6 py-4 text-sm">
                      <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                        c.priority_level === 'Critical' ? 'bg-red-500/20 text-red-400' :
                        c.priority_level === 'High' ? 'bg-orange-500/20 text-orange-400' :
                        c.priority_level === 'Medium' ? 'bg-yellow-500/20 text-yellow-400' :
                        'bg-green-500/20 text-green-400'
                      }`}>
                        {c.priority_level}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-muted-foreground capitalize">{c.status}</td>
                    <td className="px-6 py-4 text-sm">
                      {c.status !== 'resolved' && (
                        <Button
                          variant="outline"
                          size="sm"
                          disabled={updatingId === c.id}
                          onClick={() => handleMarkResolved(c.id)}
                          className="border-border hover:bg-card text-foreground text-xs"
                        >
                          {updatingId === c.id ? 'Saving…' : 'Mark Resolved'}
                        </Button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </Card>
    </div>
  );
}

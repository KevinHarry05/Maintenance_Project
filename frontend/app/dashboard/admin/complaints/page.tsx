'use client';

import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Search, Filter } from 'lucide-react';
import { useState } from 'react';
import { useAllComplaints, useAdminResolve, useAssignComplaint } from '@/hooks/useComplaints';
import { useWorkers } from '@/hooks/useUsers';

export default function AdminComplaintsPage() {
  const { data: complaints = [], isLoading } = useAllComplaints();
  const { data: workers = [] } = useWorkers();
  const adminResolve = useAdminResolve();
  const assignComplaint = useAssignComplaint();
  const [searchTerm, setSearchTerm] = useState('');
  const [updatingId, setUpdatingId] = useState<string | null>(null);
  const [selectedWorkerByComplaint, setSelectedWorkerByComplaint] = useState<Record<string, string>>({});

  const filtered = complaints.filter((c) =>
    c.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    c.id.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleResolve = async (id: string) => {
    setUpdatingId(id);
    try {
      await adminResolve.mutateAsync(id);
    } finally {
      setUpdatingId(null);
    }
  };

  const handleAssign = async (complaintId: string) => {
    const workerId = selectedWorkerByComplaint[complaintId];
    if (!workerId) return;

    setUpdatingId(complaintId);
    try {
      await assignComplaint.mutateAsync({ id: complaintId, payload: { assignee_id: workerId } });
    } finally {
      setUpdatingId(null);
    }
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-foreground">All Complaints</h1>
        <p className="text-muted-foreground">Manage all campus infrastructure complaints</p>
      </div>

      <div className="flex gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-muted-foreground" />
          <Input
            type="text"
            placeholder="Search complaints..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10 bg-input border-border text-foreground placeholder:text-muted-foreground h-11"
          />
        </div>
        <Button variant="outline" className="border-border hover:bg-card text-foreground gap-2">
          <Filter className="w-4 h-4" />
          Filters
        </Button>
      </div>

      <Card className="bg-card border-border overflow-hidden">
        <div className="overflow-x-auto">
          {isLoading ? (
            <p className="p-6 text-muted-foreground">Loading complaints…</p>
          ) : (
            <table className="w-full">
              <thead className="bg-card/50 border-b border-border">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-muted-foreground">ID</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-muted-foreground">Title</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-muted-foreground">Priority</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-muted-foreground">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-muted-foreground">Assigned To</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-muted-foreground">Assign Worker</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-muted-foreground">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {filtered.map((c) => (
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
                    <td className="px-6 py-4 text-sm">
                      <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                        c.status === 'resolved' ? 'bg-green-500/20 text-green-400' :
                        c.status === 'escalated' ? 'bg-red-500/20 text-red-400' :
                        c.status === 'in_progress' ? 'bg-blue-500/20 text-blue-400' :
                        c.status === 'assigned' ? 'bg-purple-500/20 text-purple-400' :
                        'bg-gray-500/20 text-gray-400'
                      }`}>
                        {c.status.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-muted-foreground">
                      {c.assigned_to ? (
                        <span className="font-mono text-xs">{c.assigned_to.slice(0, 8)}…</span>
                      ) : (
                        <span className="text-yellow-500">Unassigned</span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-sm">
                      <div className="flex items-center gap-2">
                        <select
                          className="px-2 py-1 bg-input border border-border rounded-md text-xs text-foreground"
                          value={selectedWorkerByComplaint[c.id] ?? ''}
                          onChange={(e) =>
                            setSelectedWorkerByComplaint((prev) => ({ ...prev, [c.id]: e.target.value }))
                          }
                        >
                          <option value="">Select worker</option>
                          {workers.map((worker) => (
                            <option key={worker.id} value={worker.id}>
                              {worker.name} ({worker.role})
                            </option>
                          ))}
                        </select>
                        <Button
                          size="sm"
                          variant="outline"
                          className="border-border hover:bg-card text-foreground text-xs"
                          disabled={!selectedWorkerByComplaint[c.id] || updatingId === c.id}
                          onClick={() => handleAssign(c.id)}
                        >
                          {updatingId === c.id ? 'Assigning…' : 'Assign'}
                        </Button>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm">
                      {(c.status !== 'resolved') && (
                        <Button
                          size="sm"
                          variant="outline"
                          className={`border-border hover:bg-card text-foreground text-xs ${
                            c.status === 'escalated' ? 'border-red-400 text-red-500 hover:bg-red-50' : ''
                          }`}
                          disabled={updatingId === c.id}
                          onClick={() => handleResolve(c.id)}
                        >
                          {updatingId === c.id ? 'Saving…' : c.status === 'escalated' ? 'Close Escalation' : 'Resolve'}
                        </Button>
                      )}
                    </td>
                  </tr>
                ))}
                {filtered.length === 0 && (
                  <tr>
                    <td className="px-6 py-6 text-sm text-muted-foreground" colSpan={7}>No complaints found.</td>
                  </tr>
                )}
              </tbody>
            </table>
          )}
        </div>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-card/50 border-border p-4">
          <p className="text-muted-foreground text-xs mb-1">Total</p>
          <p className="text-2xl font-bold text-foreground">{complaints.length}</p>
        </Card>
        <Card className="bg-card/50 border-border p-4">
          <p className="text-muted-foreground text-xs mb-1">Critical Priority</p>
          <p className="text-2xl font-bold text-red-500">{complaints.filter((c) => c.priority_level === 'Critical').length}</p>
        </Card>
        <Card className="bg-card/50 border-border p-4">
          <p className="text-muted-foreground text-xs mb-1">In Progress</p>
          <p className="text-2xl font-bold text-blue-500">{complaints.filter((c) => c.status === 'in_progress').length}</p>
        </Card>
        <Card className="bg-card/50 border-border p-4">
          <p className="text-muted-foreground text-xs mb-1">Resolved</p>
          <p className="text-2xl font-bold text-green-500">{complaints.filter((c) => c.status === 'resolved').length}</p>
        </Card>
      </div>
    </div>
  );
}

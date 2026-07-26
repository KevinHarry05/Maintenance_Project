'use client';

import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Search, Filter, Plus, AlertCircle } from 'lucide-react';
import Link from 'next/link';
import { useState } from 'react';
import { useCancelEscalation, useEscalateComplaint, useMyComplaints } from '@/hooks/useComplaints';

export default function MyComplaintsPage() {
  const { data: complaints = [], isLoading } = useMyComplaints();
  const escalateComplaint = useEscalateComplaint();
  const cancelEscalation = useCancelEscalation();
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [updatingId, setUpdatingId] = useState<string | null>(null);

  const handleEscalate = async (id: string) => {
    setUpdatingId(id);
    try {
      await escalateComplaint.mutateAsync(id);
    } finally {
      setUpdatingId(null);
    }
  };

  const handleCancelEscalation = async (id: string) => {
    setUpdatingId(id);
    try {
      await cancelEscalation.mutateAsync(id);
    } finally {
      setUpdatingId(null);
    }
  };

  const filtered = complaints.filter((c) => {
    const matchesSearch =
      c.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.id.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = filterStatus === 'all' || c.status === filterStatus;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">My Complaints</h1>
          <p className="text-muted-foreground">Track all complaints you have raised</p>
        </div>
        <Link href="/dashboard/student/report">
          <Button className="bg-primary hover:bg-primary-dark text-primary-foreground gap-2">
            <Plus className="w-5 h-5" />
            New Complaint
          </Button>
        </Link>
      </div>

      <div className="flex flex-col md:flex-row gap-4">
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
        <div className="flex gap-2">
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="px-4 py-2 bg-input border border-border rounded-md text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
          >
            <option value="all">All Status</option>
            <option value="pending">Pending</option>
            <option value="assigned">Assigned</option>
            <option value="in_progress">In Progress</option>
            <option value="resolved">Resolved</option>
          </select>
          <Button variant="outline" className="border-border hover:bg-card text-foreground gap-2">
            <Filter className="w-4 h-4" />
            More Filters
          </Button>
        </div>
      </div>

      {isLoading ? (
        <p className="text-muted-foreground">Loading complaints…</p>
      ) : filtered.length > 0 ? (
        <div className="space-y-4">
          {filtered.map((c) => (
            <Card key={c.id} className="bg-card border-border p-6 hover:border-primary/50 transition-colors cursor-pointer">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="font-mono text-sm text-primary font-semibold">{c.id.slice(0, 8).toUpperCase()}</span>
                    <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                      c.status === 'resolved' ? 'bg-green-500/20 text-green-400' :
                      c.status === 'in_progress' ? 'bg-blue-500/20 text-blue-400' :
                      c.status === 'assigned' ? 'bg-purple-500/20 text-purple-400' :
                      'bg-gray-500/20 text-gray-400'
                    }`}>
                      {c.status.replace('_', ' ')}
                    </span>
                    <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                      c.priority_level === 'Critical' ? 'bg-red-500/20 text-red-400' :
                      c.priority_level === 'High' ? 'bg-orange-500/20 text-orange-400' :
                      c.priority_level === 'Medium' ? 'bg-yellow-500/20 text-yellow-400' :
                      'bg-green-500/20 text-green-400'
                    }`}>
                      {c.priority_level}
                    </span>
                  </div>
                  <h3 className="text-lg font-semibold text-foreground mb-2">{c.title}</h3>
                  <p className="text-muted-foreground text-sm mb-3">{c.description}</p>
                  <div className="flex items-center gap-6 text-sm">
                    <span className="text-muted-foreground">
                      <strong className="text-foreground">Reported:</strong>{' '}
                      {new Date(c.created_at).toLocaleDateString()}
                    </span>
                  </div>

                  <div className="mt-4 flex gap-2">
                    {c.status === 'resolved' && (
                      <Button
                        size="sm"
                        variant="outline"
                        className="border-red-400 text-red-500 hover:bg-red-50"
                        disabled={updatingId === c.id}
                        onClick={() => handleEscalate(c.id)}
                      >
                        {updatingId === c.id ? 'Escalating…' : 'Escalate Issue'}
                      </Button>
                    )}
                    {c.status === 'escalated' && (
                      <Button
                        size="sm"
                        variant="outline"
                        className="border-green-500 text-green-600 hover:bg-green-50"
                        disabled={updatingId === c.id}
                        onClick={() => handleCancelEscalation(c.id)}
                      >
                        {updatingId === c.id ? 'Updating…' : 'Cancel Escalation'}
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            </Card>
          ))}
        </div>
      ) : (
        <Card className="bg-card border-border p-12 text-center">
          <AlertCircle className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-foreground mb-2">No complaints found</h3>
          <p className="text-muted-foreground mb-4">Try adjusting your search or filters</p>
          <Link href="/dashboard/student/report">
            <Button className="bg-primary hover:bg-primary-dark text-primary-foreground">
              Report a New Issue
            </Button>
          </Link>
        </Card>
      )}
    </div>
  );
}

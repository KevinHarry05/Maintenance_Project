'use client';

import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { AlertCircle, CheckCircle2, Clock, Plus } from 'lucide-react';
import Link from 'next/link';
import { useMemo, useState } from 'react';
import { useAuthContext } from '@/context/AuthContext';
import { useMyComplaints, useEscalateComplaint, useCancelEscalation } from '@/hooks/useComplaints';

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000'

export default function StudentDashboard() {
  const { user } = useAuthContext();
  const { data: complaints = [], isLoading } = useMyComplaints();
  const escalate = useEscalateComplaint();
  const cancelEscalation = useCancelEscalation();
  const [escalatingId, setEscalatingId] = useState<string | null>(null);

  const totalComplaints = complaints.length;
  const activeComplaints = complaints.filter((c) => c.status !== 'resolved').length;
  const resolvedComplaints = complaints.filter((c) => c.status === 'resolved').length;

  const chartData = useMemo(() => {
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'];
    const now = new Date();
    return months.map((month, idx) => ({
      month,
      complaints: complaints.filter((c) => {
        if (!c.created_at) return false;
        const d = new Date(c.created_at);
        const monthIndex = (now.getMonth() - 5 + idx + 12) % 12;
        return d.getMonth() === monthIndex;
      }).length,
    }));
  }, [complaints]);

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Dashboard</h1>
          <p className="text-muted-foreground">Welcome back, {user?.full_name ?? 'Student'}</p>
        </div>
        <Link href="/dashboard/student/report">
          <Button className="bg-primary hover:bg-blue-700 text-white gap-2 shadow-md">
            <Plus className="w-5 h-5" />
            Report Issue
          </Button>
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="bg-white border-blue-100 p-6 hover:border-primary transition-colors shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-muted-foreground text-sm font-medium">Total Complaints</p>
              <p className="text-3xl font-bold text-primary mt-2">{isLoading ? '…' : totalComplaints}</p>
            </div>
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
              <AlertCircle className="w-6 h-6 text-primary" />
            </div>
          </div>
        </Card>

        <Card className="bg-white border-blue-100 p-6 hover:border-primary transition-colors shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-muted-foreground text-sm font-medium">Active Complaints</p>
              <p className="text-3xl font-bold text-accent mt-2">{isLoading ? '…' : activeComplaints}</p>
            </div>
            <div className="w-12 h-12 bg-cyan-100 rounded-lg flex items-center justify-center">
              <Clock className="w-6 h-6 text-accent" />
            </div>
          </div>
        </Card>

        <Card className="bg-white border-blue-100 p-6 hover:border-primary transition-colors shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-muted-foreground text-sm font-medium">Resolved Issues</p>
              <p className="text-3xl font-bold text-green-600 mt-2">{isLoading ? '…' : resolvedComplaints}</p>
            </div>
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
              <CheckCircle2 className="w-6 h-6 text-green-600" />
            </div>
          </div>
        </Card>
      </div>

      <Card className="bg-white border-blue-100 p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-foreground mb-6">Complaints Trend (Last 6 Months)</h2>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#E0E7FF" />
            <XAxis dataKey="month" stroke="#6B7280" />
            <YAxis stroke="#6B7280" />
            <Tooltip contentStyle={{ backgroundColor: '#FFFFFF', border: '1px solid #E0E7FF' }} />
            <Bar dataKey="complaints" fill="#1E90FF" radius={[8, 8, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </Card>

      <Card className="bg-white border-blue-100 overflow-hidden shadow-sm">
        <div className="p-6 border-b border-blue-100 bg-blue-50/50">
          <h2 className="text-lg font-semibold text-foreground">Recent Complaints</h2>
        </div>
        <div className="overflow-x-auto">
          {isLoading ? (
            <p className="p-6 text-muted-foreground">Loading complaints…</p>
          ) : complaints.length === 0 ? (
            <p className="p-6 text-muted-foreground">No complaints submitted yet.</p>
          ) : (
            <table className="w-full">
              <thead className="bg-blue-50/50 border-b border-blue-100">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-muted-foreground uppercase">ID</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-muted-foreground uppercase">Title</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-muted-foreground uppercase">Priority</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-muted-foreground uppercase">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-muted-foreground uppercase">Action</th>
                </tr>
              </thead>
              <tbody>
                {complaints.slice(0, 5).map((c) => (
                  <tr key={c.id} className="border-b border-blue-50 hover:bg-blue-50/30 transition-colors">
                    <td className="px-6 py-4 text-sm font-mono text-muted-foreground">{c.id.slice(0, 8)}…</td>
                    <td className="px-6 py-4 text-sm text-foreground font-medium">{c.title}</td>
                    <td className="px-6 py-4 text-sm text-foreground">{c.priority_level}</td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 text-xs font-medium rounded-full capitalize ${
                        c.status === 'resolved' ? 'bg-green-100 text-green-700' :
                        c.status === 'escalated' ? 'bg-red-100 text-red-700' :
                        'bg-blue-100 text-blue-700'
                      }`}>
                        {c.status}
                      </span>
                      {c.resolution_file_path && (
                        <a
                          href={`${BACKEND_URL}/${c.resolution_file_path}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="block mt-1 text-xs text-blue-500 hover:underline"
                        >
                          📷 View resolution
                        </a>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      {c.status === 'resolved' && (
                        <Button
                          size="sm"
                          variant="outline"
                          className="text-xs border-orange-300 text-orange-600 hover:bg-orange-50"
                          disabled={escalatingId === c.id}
                          onClick={async () => {
                            if (!confirm('Are you unsatisfied with the resolution? Escalate to admin?')) return;
                            setEscalatingId(c.id);
                            try { await escalate.mutateAsync(c.id); }
                            finally { setEscalatingId(null); }
                          }}
                        >
                          {escalatingId === c.id ? 'Escalating…' : 'Escalate'}
                        </Button>
                      )}
                      {c.status === 'escalated' && (
                        <Button
                          size="sm"
                          variant="outline"
                          className="text-xs border-gray-300 text-gray-600 hover:bg-gray-50"
                          disabled={escalatingId === c.id}
                          onClick={async () => {
                            if (!confirm('Cancel escalation and mark as resolved?')) return;
                            setEscalatingId(c.id);
                            try { await cancelEscalation.mutateAsync(c.id); }
                            finally { setEscalatingId(null); }
                          }}
                        >
                          {escalatingId === c.id ? 'Cancelling…' : 'Cancel Escalation'}
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
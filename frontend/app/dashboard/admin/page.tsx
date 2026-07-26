'use client';

import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { AlertCircle, CheckCircle2, Clock, Building2, Users } from 'lucide-react';
import Link from 'next/link';
import { useAllComplaints } from '@/hooks/useComplaints';
import { useBuildings } from '@/hooks/useBuildings';

const COLORS = ['#10B981', '#3B82F6', '#F59E0B', '#A855F7'];

function getLastSixMonthsTrend(complaints: { status: string; created_at?: string }[]) {
  const now = new Date();
  const months = Array.from({ length: 6 }, (_, i) => {
    const d = new Date(now.getFullYear(), now.getMonth() - (5 - i), 1);
    return {
      key: `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`,
      month: d.toLocaleString('en-US', { month: 'short' }),
      total: 0,
      resolved: 0,
    };
  });

  const monthMap = new Map(months.map((m) => [m.key, m]));

  complaints.forEach((complaint) => {
    if (!complaint.created_at) return;
    const created = new Date(complaint.created_at);
    if (Number.isNaN(created.getTime())) return;
    const key = `${created.getFullYear()}-${String(created.getMonth() + 1).padStart(2, '0')}`;
    const bucket = monthMap.get(key);
    if (!bucket) return;
    bucket.total += 1;
    if (complaint.status === 'resolved') {
      bucket.resolved += 1;
    }
  });

  return months;
}

export default function AdminDashboard() {
  const { data: complaints = [] } = useAllComplaints();
  const { data: buildings = [] } = useBuildings();
  const complaintTrend = getLastSixMonthsTrend(complaints);

  const total = complaints.length;
  const pending = complaints.filter((c) => c.status === 'pending').length;
  const inProgress = complaints.filter((c) => c.status === 'in_progress').length;
  const resolved = complaints.filter((c) => c.status === 'resolved').length;
  const assigned = complaints.filter((c) => c.status === 'assigned').length;
  const escalated = complaints.filter((c) => c.status === 'escalated').length;

  const statusDistribution = [
    { name: 'Resolved', value: resolved, color: '#10B981' },
    { name: 'In Progress', value: inProgress, color: '#3B82F6' },
    { name: 'Pending', value: pending, color: '#F59E0B' },
    { name: 'Assigned', value: assigned, color: '#A855F7' },
    { name: 'Escalated', value: escalated, color: '#EF4444' },
  ];

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Admin Dashboard</h1>
          <p className="text-muted-foreground">System overview and management</p>
        </div>
        <div className="flex gap-3">
          <Link href="/dashboard/admin/buildings">
            <Button variant="outline" className="border-border hover:bg-card text-foreground gap-2">
              <Building2 className="w-5 h-5" />
              Manage Buildings
            </Button>
          </Link>
          <Link href="/dashboard/admin/complaints">
            <Button className="bg-primary hover:bg-primary-dark text-primary-foreground gap-2">
              <AlertCircle className="w-5 h-5" />
              All Complaints
            </Button>
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card className="bg-card border-border p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-muted-foreground text-sm font-medium">Total Complaints</p>
              <p className="text-3xl font-bold text-foreground mt-2">{total}</p>
            </div>
            <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center">
              <AlertCircle className="w-6 h-6 text-primary" />
            </div>
          </div>
        </Card>

        <Card className="bg-card border-border p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-muted-foreground text-sm font-medium">Pending Issues</p>
              <p className="text-3xl font-bold text-foreground mt-2">{pending}</p>
            </div>
            <div className="w-12 h-12 bg-yellow-500/10 rounded-lg flex items-center justify-center">
              <Clock className="w-6 h-6 text-yellow-500" />
            </div>
          </div>
        </Card>

        <Card className="bg-card border-border p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-muted-foreground text-sm font-medium">Resolved</p>
              <p className="text-3xl font-bold text-foreground mt-2">{resolved}</p>
            </div>
            <div className="w-12 h-12 bg-green-500/10 rounded-lg flex items-center justify-center">
              <CheckCircle2 className="w-6 h-6 text-green-500" />
            </div>
          </div>
        </Card>

        <Card className="bg-card border-border p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-muted-foreground text-sm font-medium">Buildings</p>
              <p className="text-3xl font-bold text-foreground mt-2">{buildings.length}</p>
            </div>
            <div className="w-12 h-12 bg-blue-500/10 rounded-lg flex items-center justify-center">
              <Users className="w-6 h-6 text-blue-500" />
            </div>
          </div>
        </Card>

        {escalated > 0 && (
          <Card className="bg-red-500/10 border-red-500/30 p-6 md:col-span-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-red-400 text-sm font-medium">Escalated — Needs Review</p>
                <p className="text-3xl font-bold text-red-400 mt-2">{escalated}</p>
              </div>
              <div className="w-12 h-12 bg-red-500/20 rounded-lg flex items-center justify-center">
                <AlertCircle className="w-6 h-6 text-red-400" />
              </div>
            </div>
          </Card>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="bg-card border-border p-6 lg:col-span-2">
          <h2 className="text-lg font-semibold text-foreground mb-6">Complaint Trend</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={complaintTrend}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="month" stroke="#9CA3AF" />
              <YAxis stroke="#9CA3AF" />
              <Tooltip contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #4B5563' }} />
              <Bar dataKey="total" fill="#3B82F6" name="Total" />
              <Bar dataKey="resolved" fill="#10B981" name="Resolved" />
            </BarChart>
          </ResponsiveContainer>
        </Card>

        <Card className="bg-card border-border p-6">
          <h2 className="text-lg font-semibold text-foreground mb-6">Status Distribution</h2>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie data={statusDistribution} cx="50%" cy="50%" innerRadius={50} outerRadius={90} paddingAngle={2} dataKey="value">
                {statusDistribution.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #4B5563' }} />
            </PieChart>
          </ResponsiveContainer>
          <div className="mt-4 space-y-2">
            {statusDistribution.map((s) => (
              <div key={s.name} className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full" style={{ backgroundColor: s.color }} />
                  <span className="text-muted-foreground">{s.name}</span>
                </div>
                <span className="font-semibold text-foreground">{s.value}</span>
              </div>
            ))}
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="bg-card border-border p-6 hover:border-primary/50 transition-colors cursor-pointer">
          <h3 className="font-semibold text-foreground mb-2">Buildings</h3>
          <p className="text-2xl font-bold text-primary">{buildings.length}</p>
          <p className="text-xs text-muted-foreground mt-2">Active on campus</p>
          <Link href="/dashboard/admin/buildings">
            <Button size="sm" variant="ghost" className="mt-4 text-primary hover:bg-primary/10 w-full">Manage →</Button>
          </Link>
        </Card>

        <Card className="bg-card border-border p-6 hover:border-primary/50 transition-colors cursor-pointer">
          <h3 className="font-semibold text-foreground mb-2">Worker Teams</h3>
          <p className="text-2xl font-bold text-accent">—</p>
          <p className="text-xs text-muted-foreground mt-2">Departments</p>
          <Link href="/dashboard/admin/staff">
            <Button size="sm" variant="ghost" className="mt-4 text-accent hover:bg-accent/10 w-full">Manage →</Button>
          </Link>
        </Card>

        <Card className="bg-card border-border p-6 hover:border-primary/50 transition-colors cursor-pointer">
          <h3 className="font-semibold text-foreground mb-2">In Progress</h3>
          <p className="text-2xl font-bold text-blue-500">{inProgress}</p>
          <p className="text-xs text-muted-foreground mt-2">Being handled</p>
          <Link href="/dashboard/admin/complaints">
            <Button size="sm" variant="ghost" className="mt-4 text-blue-500 hover:bg-blue-500/10 w-full">Review →</Button>
          </Link>
        </Card>

        <Card className="bg-card border-border p-6 hover:border-primary/50 transition-colors cursor-pointer">
          <h3 className="font-semibold text-foreground mb-2">Assigned</h3>
          <p className="text-2xl font-bold text-purple-500">{assigned}</p>
          <p className="text-xs text-muted-foreground mt-2">Awaiting work</p>
          <Link href="/dashboard/admin/complaints">
            <Button size="sm" variant="ghost" className="mt-4 text-purple-500 hover:bg-purple-500/10 w-full">View →</Button>
          </Link>
        </Card>
      </div>
    </div>
  );
}

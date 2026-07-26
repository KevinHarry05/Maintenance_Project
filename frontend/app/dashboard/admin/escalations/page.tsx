'use client';

import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { AlertCircle, CheckCircle2 } from 'lucide-react';
import { useState } from 'react';
import { useAllComplaints, useAdminResolve } from '@/hooks/useComplaints';

export default function EscalationsPage() {
  const { data: complaints = [], isLoading } = useAllComplaints();
  const adminResolve = useAdminResolve();
  const [closingId, setClosingId] = useState<string | null>(null);

  const escalations = complaints.filter((c) => c.status === 'escalated');

  const handleClose = async (id: string) => {
    if (!confirm('Mark this escalation as resolved?')) return;
    setClosingId(id);
    try {
      await adminResolve.mutateAsync(id);
    } finally {
      setClosingId(null);
    }
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Escalations</h1>
        <p className="text-muted-foreground">Critical issues requiring immediate attention</p>
      </div>

      {isLoading ? (
        <p className="text-muted-foreground">Loading escalations…</p>
      ) : escalations.length > 0 ? (
        <div className="space-y-4">
          {escalations.map((esc) => (
            <Card key={esc.id} className="bg-red-500/5 border border-red-500/20 p-6">
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-4">
                  <AlertCircle className="w-6 h-6 text-red-500 flex-shrink-0 mt-1" />
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-sm font-mono text-red-500">{esc.id.slice(0, 8)}…</span>
                      <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${
                        esc.priority_level === 'Critical' ? 'bg-red-500/20 text-red-400' :
                        esc.priority_level === 'High' ? 'bg-orange-500/20 text-orange-400' :
                        esc.priority_level === 'Medium' ? 'bg-yellow-500/20 text-yellow-400' :
                        'bg-green-500/20 text-green-400'
                      }`}>
                        {esc.priority_level}
                      </span>
                    </div>
                    <h3 className="font-semibold text-foreground">{esc.title}</h3>
                    <p className="text-sm text-muted-foreground mt-1">{esc.description}</p>
                    <p className="text-xs text-muted-foreground mt-2">
                      Category: <span className="capitalize">{esc.category ?? 'N/A'}</span>
                      {esc.assigned_to && (
                        <span className="ml-4">Assigned to: <span className="font-mono">{esc.assigned_to.slice(0, 8)}…</span></span>
                      )}
                    </p>
                  </div>
                </div>
                <Button
                  variant="outline"
                  className="border-red-500/50 hover:bg-red-500/10 text-red-500"
                  disabled={closingId === esc.id}
                  onClick={() => handleClose(esc.id)}
                >
                  {closingId === esc.id ? 'Closing…' : 'Close Escalation'}
                </Button>
              </div>
            </Card>
          ))}
        </div>
      ) : (
        <Card className="bg-card border-border p-12 text-center">
          <CheckCircle2 className="w-12 h-12 text-green-500 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-foreground mb-2">No escalations</h3>
          <p className="text-muted-foreground">All complaints are being handled within SLA.</p>
        </Card>
      )}
    </div>
  );
}

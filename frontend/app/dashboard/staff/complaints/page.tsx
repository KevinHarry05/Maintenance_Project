'use client';

import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useRef, useState } from 'react';
import { useAssignedComplaints, useUploadResolution } from '@/hooks/useComplaints';

export default function StaffComplaintsPage() {
  const { data: tasks = [], isLoading } = useAssignedComplaints();
  const uploadResolution = useUploadResolution();
  const [resolvingId, setResolvingId] = useState<string | null>(null);
  const [resolutionFile, setResolutionFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleResolve = async (id: string) => {
    await uploadResolution.mutateAsync({ id, file: resolutionFile });
    setResolvingId(null);
    setResolutionFile(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-foreground">My Tasks</h1>
        <p className="text-muted-foreground">Manage tasks assigned to you</p>
      </div>

      {isLoading ? (
        <p className="text-muted-foreground">Loading tasks…</p>
      ) : (
        <div className="space-y-4">
          {tasks.map((task) => {
            const progress =
              task.status === 'resolved' ? 100 :
              task.status === 'in_progress' ? 60 : 0;
            const isResolving = resolvingId === task.id;
            return (
              <Card key={task.id} className="bg-card border-border p-6">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-sm font-mono text-primary">{task.id.slice(0, 8)}…</span>
                      <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                        task.priority_level === 'Critical' ? 'bg-red-500/20 text-red-400' :
                        task.priority_level === 'High' ? 'bg-orange-500/20 text-orange-400' :
                        task.priority_level === 'Medium' ? 'bg-yellow-500/20 text-yellow-400' :
                        'bg-green-500/20 text-green-400'
                      }`}>
                        {task.priority_level}
                      </span>
                    </div>
                    <h3 className="text-lg font-semibold text-foreground">{task.title}</h3>
                    <p className="text-sm text-muted-foreground capitalize">{task.status.replace('_', ' ')}</p>
                    <p className="text-sm text-muted-foreground mt-1">{task.description}</p>
                  </div>
                  {task.status !== 'resolved' && !isResolving && (
                    <Button
                      variant="outline"
                      className="border-border hover:bg-card text-foreground"
                      onClick={() => setResolvingId(task.id)}
                    >
                      Mark Resolved
                    </Button>
                  )}
                </div>

                {/* Inline resolve form */}
                {isResolving && (
                  <div className="mt-4 p-4 rounded-lg border border-border bg-card/50 space-y-3">
                    <p className="text-sm font-medium text-foreground">Resolve this task</p>
                    <div>
                      <label className="text-xs text-muted-foreground block mb-1">
                        Attach resolution image (optional)
                      </label>
                      <input
                        ref={fileInputRef}
                        type="file"
                        accept="image/*,.pdf"
                        className="text-sm text-muted-foreground file:mr-3 file:py-1 file:px-3 file:rounded file:border-0 file:text-xs file:bg-primary/10 file:text-primary hover:file:bg-primary/20"
                        onChange={(e) => setResolutionFile(e.target.files?.[0] ?? null)}
                      />
                    </div>
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        className="bg-green-600 hover:bg-green-700 text-white"
                        disabled={uploadResolution.isPending}
                        onClick={() => handleResolve(task.id)}
                      >
                        {uploadResolution.isPending ? 'Resolving…' : 'Confirm Resolved'}
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => {
                          setResolvingId(null);
                          setResolutionFile(null);
                          if (fileInputRef.current) fileInputRef.current.value = '';
                        }}
                      >
                        Cancel
                      </Button>
                    </div>
                  </div>
                )}

                {task.status === 'resolved' && task.resolution_file_path && (
                  <div className="mt-2">
                    <a
                      href={`${process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000'}/${task.resolution_file_path}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs text-primary hover:underline"
                    >
                      📷 View resolution image
                    </a>
                  </div>
                )}

                <div className="space-y-2 mt-4">
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Progress</span>
                    <span className="font-semibold text-foreground">{progress}%</span>
                  </div>
                  <div className="w-full bg-card/50 rounded-full h-2 overflow-hidden">
                    <div className="bg-primary h-full transition-all" style={{ width: `${progress}%` }} />
                  </div>
                </div>
              </Card>
            );
          })}
          {tasks.length === 0 && (
            <Card className="bg-card border-border p-6 text-center text-muted-foreground">
              No active tasks assigned to you. If a complaint was assigned to another worker,
              ask admin to reassign it from the Admin Complaints page.
            </Card>
          )}
        </div>
      )}
    </div>
  );
}

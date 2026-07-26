'use client';

import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Upload, ArrowRight } from 'lucide-react';
import { useState } from 'react';
import Link from 'next/link';
import { useCreateComplaint } from '@/hooks/useComplaints';
import { useBuildings } from '@/hooks/useBuildings';
import type { Complaint } from '@/types/complaint';

export default function ReportComplaintPage() {
  const createComplaint = useCreateComplaint();
  const { data: buildings = [], isLoading: isLoadingBuildings, refetch: refetchBuildings } = useBuildings();

  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [buildingId, setBuildingId] = useState('');
  const [floorNumber, setFloorNumber] = useState('');
  const [roomNumber, setRoomNumber] = useState('');
  const [category, setCategory] = useState('');
  const [image, setImage] = useState<File | null>(null);
  const [error, setError] = useState('');
  const [submitted, setSubmitted] = useState<Complaint | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      // The backend validates the building ID against its current database.
      // Refresh before submission in case the API was restarted while this page
      // remained open and the selected option now belongs to an old database.
      const { data: currentBuildings = [] } = await refetchBuildings();
      if (!currentBuildings.some((building) => building.id === buildingId)) {
        setBuildingId('');
        setError('The building list was updated. Please select a building again.');
        return;
      }

      const result = await createComplaint.mutateAsync({
        title,
        description,
        building_id: buildingId,
        floor_number: floorNumber,
        room_number: roomNumber,
        category: category || undefined,
        image,
      });
      setSubmitted(result);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to submit complaint');
    }
  };

  const handleReset = () => {
    setSubmitted(null);
    setTitle('');
    setDescription('');
    setBuildingId('');
    setFloorNumber('');
    setRoomNumber('');
    setCategory('');
    setImage(null);
    setError('');
  };

  if (submitted) {
    return (
      <div className="space-y-8">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Complaint Submitted</h1>
          <p className="text-muted-foreground">Your complaint has been successfully submitted</p>
        </div>

        <Card className="bg-card border-border p-12 text-center space-y-6">
          <div className="w-16 h-16 bg-green-500/20 rounded-lg flex items-center justify-center mx-auto">
            <svg className="w-8 h-8 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <div>
            <h2 className="text-2xl font-bold text-foreground mb-2">Thank you!</h2>
            <p className="text-muted-foreground mb-4">
              Your complaint has been received. Reference ID:{' '}
              <span className="text-primary font-mono">{submitted.id.slice(0, 8).toUpperCase()}</span>
            </p>
            <p className="text-muted-foreground">
              You will receive updates via notifications as our team works to resolve your issue.
            </p>
          </div>
          <div className="flex gap-4 justify-center pt-4">
            <Button onClick={handleReset} className="bg-primary hover:bg-primary-dark text-primary-foreground">
              Report Another Issue
            </Button>
            <Link href="/dashboard/student/complaints">
              <Button variant="outline" className="border-border hover:bg-card text-foreground">
                View My Complaints
              </Button>
            </Link>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-8 max-w-3xl">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Report an Issue</h1>
        <p className="text-muted-foreground">Help us improve campus infrastructure</p>
      </div>

      <Card className="bg-card border-border p-8 space-y-6">
        {error && (
          <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 text-red-400 text-sm">{error}</div>
        )}
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-semibold text-foreground mb-2">
              Issue Title <span className="text-red-500">*</span>
            </label>
            <Input
              type="text"
              placeholder="e.g., Broken AC Unit, Water Leak"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="bg-input border-border text-foreground placeholder:text-muted-foreground h-11"
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-semibold text-foreground mb-2">
                Building <span className="text-red-500">*</span>
              </label>
              <select
                value={buildingId}
                onChange={(e) => setBuildingId(e.target.value)}
                className="w-full px-4 py-2 bg-input border border-border rounded-md text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                required
              >
                <option value="">Select building</option>
                {buildings.map((b) => (
                  <option key={b.id} value={b.id}>{b.name}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-semibold text-foreground mb-2">
                Category
              </label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full px-4 py-2 bg-input border border-border rounded-md text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
              >
                <option value="">Select category</option>
                <option value="electrical">Electrical</option>
                <option value="plumbing">Plumbing</option>
                <option value="hvac">HVAC/Cooling</option>
                <option value="structural">Structural</option>
                <option value="it">IT/Network</option>
                <option value="other">Other</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-semibold text-foreground mb-2">Floor Number <span className="text-red-500">*</span></label>
              <Input value={floorNumber} onChange={(e) => setFloorNumber(e.target.value)} placeholder="e.g., 2" required />
            </div>
            <div>
              <label className="block text-sm font-semibold text-foreground mb-2">Room Number <span className="text-red-500">*</span></label>
              <Input value={roomNumber} onChange={(e) => setRoomNumber(e.target.value)} placeholder="e.g., 203" required />
            </div>
          </div>

          <div>
            <label className="block text-sm font-semibold text-foreground mb-2">
              Description <span className="text-red-500">*</span>
            </label>
            <textarea
              placeholder="Describe the issue in detail. Where is it located? What's the problem?"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={6}
              className="w-full px-4 py-3 bg-input border border-border rounded-md text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary resize-none"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-foreground mb-2">
              Upload Image (Optional)
            </label>
            <label className="border-2 border-dashed border-border rounded-lg p-8 text-center hover:border-primary/50 transition-colors cursor-pointer flex flex-col items-center gap-2">
              <Upload className="w-8 h-8 text-muted-foreground" />
              <p className="text-sm text-foreground font-medium">
                {image ? image.name : 'Drop image here or click to browse'}
              </p>
              <p className="text-xs text-muted-foreground">PNG, JPG, GIF up to 10MB</p>
              <input
                type="file"
                accept="image/*"
                className="hidden"
                onChange={(e) => setImage(e.target.files?.[0] || null)}
              />
            </label>
          </div>

          <div className="flex items-start bg-primary/10 border border-primary/20 rounded-lg p-4">
            <input type="checkbox" className="w-5 h-5 border-border rounded bg-input mt-0.5" required />
            <span className="ml-3 text-sm text-muted-foreground">
              I confirm that the information provided is accurate and truthful
            </span>
          </div>

          <div className="flex gap-4">
            <Button
              type="submit"
              disabled={createComplaint.isPending || isLoadingBuildings || !buildingId || !floorNumber || !roomNumber}
              className="bg-primary hover:bg-primary-dark text-primary-foreground gap-2 flex-1"
            >
              {createComplaint.isPending ? 'Submitting...' : 'Submit Complaint'}
              <ArrowRight className="w-5 h-5" />
            </Button>
            <Button
              type="button"
              variant="outline"
              className="border-border hover:bg-card text-foreground"
              onClick={handleReset}
            >
              Clear
            </Button>
          </div>
        </form>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="bg-card/50 border-border p-6">
          <div className="text-2xl font-bold text-primary mb-2">24/7</div>
          <p className="text-sm text-muted-foreground">Report issues anytime, any day</p>
        </Card>
        <Card className="bg-card/50 border-border p-6">
          <div className="text-2xl font-bold text-accent mb-2">Real-time</div>
          <p className="text-sm text-muted-foreground">Track your complaint status instantly</p>
        </Card>
        <Card className="bg-card/50 border-border p-6">
          <div className="text-2xl font-bold text-green-500 mb-2">AI-Powered</div>
          <p className="text-sm text-muted-foreground">Automatic categorization &amp; assignment</p>
        </Card>
      </div>
    </div>
  );
}

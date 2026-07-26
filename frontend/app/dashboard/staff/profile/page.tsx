'use client';

import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { User, Save } from 'lucide-react';

export default function StaffProfilePage() {
  return (
    <div className="space-y-8 max-w-2xl">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Worker Profile</h1>
        <p className="text-muted-foreground">Manage your account</p>
      </div>

      <Card className="bg-card border-border p-8">
        <div className="flex items-center gap-6 pb-8 border-b border-border mb-8">
          <div className="w-20 h-20 bg-primary/20 rounded-full flex items-center justify-center">
            <User className="w-10 h-10 text-primary" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-foreground">Raj Kumar</h2>
            <p className="text-muted-foreground">Maintenance Worker • Team Lead</p>
          </div>
        </div>

        <div className="space-y-6">
          <div>
            <label className="block text-sm font-semibold text-foreground mb-2">Full Name</label>
            <Input
              defaultValue="Raj Kumar"
              className="bg-input border-border text-foreground h-11"
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-foreground mb-2">Email Address</label>
            <Input
              type="email"
              defaultValue="raj.kumar@college.edu"
              className="bg-input border-border text-foreground h-11"
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-foreground mb-2">Department</label>
            <Input
              disabled
              defaultValue="Electrical & HVAC"
              className="bg-card border-border text-muted-foreground h-11"
            />
          </div>

          <div className="flex gap-3 pt-6">
            <Button className="bg-primary hover:bg-primary-dark text-primary-foreground gap-2">
              <Save className="w-5 h-5" />
              Save Changes
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
}

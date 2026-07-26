'use client';

import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { User, Save } from 'lucide-react';
import { useState } from 'react';

type ProfileData = {
  fullName: string;
  email: string;
  phone: string;
  location: string;
  role: string;
};

const defaultProfile: ProfileData = {
  fullName: 'John Doe',
  email: 'john.doe@college.edu',
  phone: '+91 98765 43210',
  location: 'Block A, Room 201',
  role: 'student',
};

function getInitialProfile(): ProfileData {
  if (typeof window === 'undefined') {
    return defaultProfile;
  }

  try {
    const rawUser = localStorage.getItem('sbms_user');
    if (!rawUser) return defaultProfile;

    const parsed = JSON.parse(rawUser);
    const normalizedRole = parsed?.role;

    return {
      ...defaultProfile,
      fullName: parsed?.fullName || defaultProfile.fullName,
      email: parsed?.email || defaultProfile.email,
      role: normalizedRole || defaultProfile.role,
    };
  } catch {
    return defaultProfile;
  }
}

export default function ProfilePage() {
  const [profile, setProfile] = useState<ProfileData>(getInitialProfile);

  return (
    <div className="space-y-8 max-w-2xl">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-foreground">My Profile</h1>
        <p className="text-muted-foreground">Manage your account information</p>
      </div>

      {/* Profile Card */}
      <Card className="bg-card border-border p-8">
        {/* Avatar Section */}
        <div className="flex items-center gap-6 pb-8 border-b border-border mb-8">
          <div className="w-20 h-20 bg-primary/20 rounded-full flex items-center justify-center">
            <User className="w-10 h-10 text-primary" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-foreground">{profile.fullName}</h2>
            <p className="text-muted-foreground">{profile.role.charAt(0).toUpperCase() + profile.role.slice(1)} • Active</p>
            <Button size="sm" className="mt-2 bg-primary hover:bg-primary-dark text-primary-foreground">
              Change Avatar
            </Button>
          </div>
        </div>

        {/* Form Fields */}
        <div className="space-y-6">
          <div>
            <label className="block text-sm font-semibold text-foreground mb-2">Full Name</label>
            <Input
              value={profile.fullName}
              onChange={(e) => setProfile((prev) => ({ ...prev, fullName: e.target.value }))}
              className="bg-input border-border text-foreground h-11"
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-foreground mb-2">Email Address</label>
            <Input
              type="email"
              value={profile.email}
              onChange={(e) => setProfile((prev) => ({ ...prev, email: e.target.value }))}
              className="bg-input border-border text-foreground h-11"
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-foreground mb-2">Phone Number</label>
            <Input
              type="tel"
              value={profile.phone}
              onChange={(e) => setProfile((prev) => ({ ...prev, phone: e.target.value }))}
              className="bg-input border-border text-foreground h-11"
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-foreground mb-2">Location</label>
            <Input
              value={profile.location}
              onChange={(e) => setProfile((prev) => ({ ...prev, location: e.target.value }))}
              className="bg-input border-border text-foreground h-11"
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-foreground mb-2">Role</label>
            <Input
              disabled
              value={profile.role.charAt(0).toUpperCase() + profile.role.slice(1)}
              className="bg-card border-border text-muted-foreground h-11"
            />
          </div>

          <div className="flex gap-3 pt-6">
            <Button className="bg-primary hover:bg-primary-dark text-primary-foreground gap-2">
              <Save className="w-5 h-5" />
              Save Changes
            </Button>
            <Button variant="outline" className="border-border hover:bg-card text-foreground">
              Cancel
            </Button>
          </div>
        </div>
      </Card>

      {/* Danger Zone */}
      <Card className="bg-red-500/5 border border-red-500/20 p-6">
        <h3 className="text-lg font-semibold text-red-500 mb-2">Danger Zone</h3>
        <p className="text-muted-foreground text-sm mb-4">
          These actions cannot be undone. Please be careful.
        </p>
        <Button variant="outline" className="border-red-500/50 hover:bg-red-500/10 text-red-500">
          Reset Password
        </Button>
      </Card>
    </div>
  );
}

'use client';

import Image from 'next/image';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Building2, ArrowRight } from 'lucide-react';
import { useState } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { getDashboardByRole } from '@/utils/roleUtils';
import type { UserRole } from '@/types/user';

export default function RegisterPage() {
  const router = useRouter();
  const { register } = useAuth();
  const [formData, setFormData] = useState({
    fullName: '',
    email: '',
    password: '',
    confirmPassword: '',
    role: 'student' as UserRole,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();

    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    if (formData.password.length < 8 || !/[A-Z]/.test(formData.password) || !/[a-z]/.test(formData.password) || !/\d/.test(formData.password)) {
      setError('Password must be at least 8 characters and include uppercase, lowercase, and a number.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      await register({
        full_name: formData.fullName,
        email: formData.email,
        password: formData.password,
        role: formData.role,
      });
      router.push(getDashboardByRole(formData.role));
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-blue-50 flex">
      {/* Left Side - Branding */}
      <div className="hidden lg:flex lg:w-1/2 bg-white flex-col justify-between p-8 shadow-lg">
        <div className="flex items-center space-x-3">
          <div className="w-12 h-12 bg-primary rounded-lg flex items-center justify-center shadow-md">
            <Building2 className="w-8 h-8 text-white" />
          </div>
          <div>
            <span className="text-2xl font-bold text-primary block">SBMS</span>
            <span className="text-xs text-muted-foreground">St. Joseph&apos;s</span>
          </div>
        </div>
        
        <div>
          <div className="relative h-80 rounded-xl overflow-hidden border-2 border-blue-100 mb-8 shadow-lg">
            <Image
              src="/college-auditorium.jpg"
              alt="Campus Auditorium"
              fill
              className="object-cover"
              priority
            />
          </div>
          <h2 className="text-4xl font-bold text-foreground mb-4">Join Our Community</h2>
          <p className="text-lg text-muted-foreground leading-relaxed">
            Help us maintain campus infrastructure by reporting issues and collaborating with the maintenance team.
          </p>
        </div>

        <div className="text-muted-foreground text-sm">
          © 2026 SBMS. All rights reserved.
        </div>
      </div>

      {/* Right Side - Registration Form */}
      <div className="w-full lg:w-1/2 flex flex-col justify-center px-4 sm:px-6 lg:px-12">
        <div className="max-w-md w-full mx-auto">
          <div className="mb-8">
            <h1 className="text-3xl sm:text-4xl font-bold text-foreground mb-2">Create Account</h1>
            <p className="text-muted-foreground">Join SBMS and help improve campus infrastructure</p>
          </div>

          <Card className="bg-white border-blue-100 p-8 space-y-6 shadow-lg">
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-3 rounded-lg">
                {error}
              </div>
            )}
            <form onSubmit={handleRegister} className="space-y-5">
              <div>
                <label className="block text-sm font-semibold text-foreground mb-2">
                  Full Name
                </label>
                <Input
                  type="text"
                  name="fullName"
                  placeholder="John Doe"
                  value={formData.fullName}
                  onChange={handleChange}
                  className="bg-blue-50 border-blue-200 text-foreground placeholder:text-muted-foreground focus:border-primary focus:ring-primary"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-foreground mb-2">
                  Email Address
                </label>
                <Input
                  type="email"
                  name="email"
                  placeholder="name@college.edu"
                  value={formData.email}
                  onChange={handleChange}
                  className="bg-blue-50 border-blue-200 text-foreground placeholder:text-muted-foreground focus:border-primary focus:ring-primary"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-foreground mb-2">
                  Role
                </label>
                <select
                  name="role"
                  value={formData.role}
                  onChange={handleChange}
                  className="w-full px-4 py-2 bg-blue-50 border border-blue-200 rounded-md text-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary"
                >
                  <option value="student">Student</option>
                  <option value="worker">Maintenance Worker</option>
                  <option value="admin">Administrator</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-semibold text-foreground mb-2">
                  Password
                </label>
                <Input
                  type="password"
                  name="password"
                  placeholder="••••••••"
                  value={formData.password}
                  onChange={handleChange}
                  className="bg-blue-50 border-blue-200 text-foreground placeholder:text-muted-foreground focus:border-primary focus:ring-primary"
                  required
                />
                <p className="mt-1 text-xs text-muted-foreground">Min 8 characters, include uppercase, lowercase and a number.</p>
              </div>

              <div>
                <label className="block text-sm font-semibold text-foreground mb-2">
                  Confirm Password
                </label>
                <Input
                  type="password"
                  name="confirmPassword"
                  placeholder="••••••••"
                  value={formData.confirmPassword}
                  onChange={handleChange}
                  className="bg-blue-50 border-blue-200 text-foreground placeholder:text-muted-foreground focus:border-primary focus:ring-primary"
                  required
                />
              </div>

              <div className="flex items-start">
                <input
                  type="checkbox"
                  className="w-4 h-4 border-blue-200 rounded bg-blue-50 accent-primary mt-1"
                  required
                />
                <span className="ml-2 text-sm text-muted-foreground font-medium">
                  I agree to the{' '}
                  <Link href="#" className="text-primary hover:text-blue-700 transition-colors">
                    Terms of Service
                  </Link>
                  {' '}and{' '}
                  <Link href="#" className="text-primary hover:text-blue-700 transition-colors">
                    Privacy Policy
                  </Link>
                </span>
              </div>

              <Button
                type="submit"
                disabled={loading}
                className="w-full bg-primary hover:bg-blue-700 text-white py-6 text-base font-semibold gap-2 shadow-lg"
              >
                {loading ? 'Creating account...' : 'Create Account'}
                <ArrowRight className="w-5 h-5" />
              </Button>
            </form>

            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-blue-100"></div>
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-white text-muted-foreground font-medium">Or sign up with</span>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <Button variant="outline" className="border-blue-200 hover:bg-blue-50 text-foreground font-medium">
                Google
              </Button>
              <Button variant="outline" className="border-blue-200 hover:bg-blue-50 text-foreground font-medium">
                Microsoft
              </Button>
            </div>
          </Card>

          <p className="text-center text-muted-foreground mt-8 text-base">
            Already have an account?{' '}
            <Link href="/login" className="text-primary hover:text-blue-700 font-bold transition-colors">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}

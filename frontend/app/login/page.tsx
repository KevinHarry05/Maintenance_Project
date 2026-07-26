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

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      await login({ email, password });
      // AuthContext.login fetches the user via /auth/me after storing token
      // Read role from localStorage-like pattern via refreshUser — user is set in context
      // We redirect based on role; since login calls refreshUser, we check after a tick
      const token = localStorage.getItem('sbms_access_token');
      if (token) {
        // Determine role from stored user or default to student
        try {
          const rawUser = localStorage.getItem('sbms_user');
          const parsed = rawUser ? JSON.parse(rawUser) : null;
          const role = parsed?.role ?? 'student';
          router.push(getDashboardByRole(role));
        } catch {
          router.push('/dashboard/student');
        }
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-blue-50 flex">
      {/* Left Side - Branding */}
      <div className="hidden lg:flex lg:w-1/2 bg-white flex-col justify-between p-8 shadow-lg">
        <div className="flex items-center space-x-3">
          <div className="w-12 h-12 bg-primary rounded-lg flex items-center justify-center shadow-lg">
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
              src="/college-modern.jpg"
              alt="Campus"
              fill
              className="object-cover"
              priority
            />
          </div>
          <h2 className="text-4xl font-bold text-foreground mb-4">Smart Campus Management</h2>
          <p className="text-lg text-muted-foreground leading-relaxed">
            Report, track, and resolve campus infrastructure issues with our intelligent management system. Join thousands of users improving their campus today.
          </p>
        </div>

        <div className="text-muted-foreground text-sm">
          © 2026 SBMS. All rights reserved.
        </div>
      </div>

      {/* Right Side - Login Form */}
      <div className="w-full lg:w-1/2 flex flex-col justify-center px-4 sm:px-6 lg:px-12">
        <div className="max-w-md w-full mx-auto">
          <div className="mb-8">
            <h1 className="text-4xl font-bold text-foreground mb-2">Welcome Back</h1>
            <p className="text-muted-foreground text-lg">Sign in to your account to continue</p>
          </div>

          <Card className="bg-white border-blue-100 p-8 space-y-6 shadow-lg">
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-3 rounded-lg">
                {error}
              </div>
            )}
            <form onSubmit={handleLogin} className="space-y-5">
              <div>
                <label className="block text-sm font-semibold text-foreground mb-2">
                  Email Address
                </label>
                <Input
                  type="email"
                  placeholder="name@college.edu"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="bg-blue-50 border-blue-200 text-foreground placeholder:text-muted-foreground focus:border-primary focus:ring-primary"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-foreground mb-2">
                  Password
                </label>
                <Input
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="bg-blue-50 border-blue-200 text-foreground placeholder:text-muted-foreground focus:border-primary focus:ring-primary"
                  required
                />
              </div>

              <div className="flex items-center justify-between pt-2">
                <label className="flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    className="w-4 h-4 border-blue-200 rounded bg-blue-50 accent-primary"
                  />
                  <span className="ml-2 text-sm text-muted-foreground font-medium">Remember me</span>
                </label>
                <Link href="#" className="text-sm text-primary font-semibold hover:text-blue-700 transition-colors">
                  Forgot password?
                </Link>
              </div>

              <Button
                type="submit"
                disabled={loading}
                className="w-full bg-primary hover:bg-blue-700 text-white py-6 text-base font-semibold gap-2 shadow-lg"
              >
                {loading ? 'Signing in...' : 'Sign In'}
                <ArrowRight className="w-5 h-5" />
              </Button>
            </form>

            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-blue-100"></div>
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-white text-muted-foreground font-medium">Or continue with</span>
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
            Don&apos;t have an account?{' '}
            <Link href="/register" className="text-primary hover:text-blue-700 font-bold transition-colors">
              Create one
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}

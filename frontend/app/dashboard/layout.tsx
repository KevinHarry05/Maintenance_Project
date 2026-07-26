'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import {
  Building2,
  LayoutDashboard,
  ClipboardList,
  AlertCircle,
  Bell,
  User,
  LogOut,
  Menu,
  X,
} from 'lucide-react';
import { useState, useEffect } from 'react';
import { useAuthContext } from '@/context/AuthContext';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const router = useRouter();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { user, loading, logout } = useAuthContext();

  useEffect(() => {
    if (!loading && !user) {
      router.replace('/login');
    }
  }, [user, loading, router]);

  const handleLogout = async () => {
    await logout();
    router.replace('/login');
  };

  // Determine role: prefer user.role from auth context, fall back to URL segment
  const roleFromPath = pathname.split('/')[2] as string;
  const userRole = user?.role ?? (
    (roleFromPath === 'admin' || roleFromPath === 'worker' || roleFromPath === 'student')
      ? roleFromPath
      : 'student'
  );

  const menuItems = {
    student: [
      { icon: LayoutDashboard, label: 'Dashboard', href: '/dashboard/student' },
      { icon: AlertCircle, label: 'Report Complaint', href: '/dashboard/student/report' },
      { icon: ClipboardList, label: 'My Complaints', href: '/dashboard/student/complaints' },
      { icon: Bell, label: 'Notifications', href: '/dashboard/student/notifications' },
      { icon: User, label: 'Profile', href: '/dashboard/student/profile' },
    ],
    worker: [
      { icon: LayoutDashboard, label: 'Dashboard', href: '/dashboard/worker' },
      { icon: ClipboardList, label: 'Assigned Complaints', href: '/dashboard/worker/complaints' },
      { icon: Bell, label: 'Notifications', href: '/dashboard/worker/notifications' },
    ],
    admin: [
      { icon: LayoutDashboard, label: 'Dashboard', href: '/dashboard/admin' },
      { icon: Building2, label: 'Buildings', href: '/dashboard/admin/buildings' },
      { icon: ClipboardList, label: 'All Complaints', href: '/dashboard/admin/complaints' },
      { icon: AlertCircle, label: 'Escalations', href: '/dashboard/admin/escalations' },
      { icon: User, label: 'Worker Management', href: '/dashboard/admin/staff' },
      { icon: Bell, label: 'Notifications', href: '/dashboard/admin/notifications' },
    ],
  };

  const currentMenuItems = menuItems[userRole as keyof typeof menuItems] ?? menuItems.student;
  const displayName = user?.full_name ?? 'User';
  const displayEmail = user?.email ?? '';

  if (loading) {
    return (
      <div className="min-h-screen bg-blue-50 flex items-center justify-center">
        <p className="text-muted-foreground">Loading...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-blue-50">
      <div className="lg:hidden fixed top-0 w-full bg-white border-b border-blue-100 z-40 px-4 py-3 flex items-center justify-between shadow-sm">
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
            <Building2 className="w-5 h-5 text-white" />
          </div>
          <span className="font-bold text-primary text-lg">SBMS</span>
        </div>
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="p-2 hover:bg-blue-50 rounded-lg transition-colors"
        >
          {sidebarOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
        </button>
      </div>

      <aside
        className={`
        fixed left-0 top-0 h-screen w-60 bg-white border-r border-blue-100 z-30 sbms-surface
        transition-transform duration-300 lg:translate-x-0
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
        pt-16 lg:pt-0 flex flex-col shadow-lg
      `}
      >
        <div className="hidden lg:flex items-center space-x-3 px-6 py-6 border-b border-blue-100">
          <div className="w-10 h-10 bg-primary rounded-lg flex items-center justify-center shadow-md">
            <Building2 className="w-6 h-6 text-white" />
          </div>
          <div>
            <span className="text-lg font-bold text-primary block">SBMS</span>
            <span className="text-xs text-muted-foreground">St. Joseph&apos;s</span>
          </div>
        </div>

        <nav className="flex-1 px-3 py-6 space-y-1 overflow-y-auto">
          {currentMenuItems.map((item) => {
            const Icon = item.icon;
            return (
              <Link key={item.href} href={item.href}>
                <button className="w-full flex items-center space-x-3 px-4 py-2.5 rounded-lg text-muted-foreground hover:text-primary hover:bg-blue-50 transition-colors text-left text-sm font-medium">
                  <Icon className="w-5 h-5 flex-shrink-0" />
                  <span>{item.label}</span>
                </button>
              </Link>
            );
          })}
        </nav>

        <div className="border-t border-blue-100 px-4 py-4 space-y-3 bg-blue-50/50">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-primary/10 rounded-full flex items-center justify-center border border-blue-200">
              <User className="w-6 h-6 text-primary" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-foreground truncate">{displayName}</p>
              <p className="text-xs text-muted-foreground truncate">{displayEmail}</p>
            </div>
          </div>
          <Button onClick={handleLogout} className="w-full bg-primary hover:bg-blue-700 text-white justify-start gap-2">
            <LogOut className="w-4 h-4" />
            Logout
          </Button>
        </div>
      </aside>

      <main className="lg:ml-60 pt-16 lg:pt-0">
        <div className="sticky top-0 bg-white border-b border-blue-100 px-6 py-4 z-20 shadow-sm sbms-surface">
          <div className="flex items-center justify-between">
            <div className="flex-1"></div>
            <div className="flex items-center gap-4">
              <button className="p-2 hover:bg-blue-50 rounded-lg transition-colors relative">
                <Bell className="w-5 h-5 text-muted-foreground" />
                <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
              </button>
            </div>
          </div>
        </div>

        <div className="px-6 py-8 sbms-enter">{children}</div>
      </main>

      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-20 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </div>
  );
}

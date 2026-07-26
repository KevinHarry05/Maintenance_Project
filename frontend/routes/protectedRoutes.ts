import type { UserRole } from '@/types/user'

export const DASHBOARD_BY_ROLE: Record<UserRole, string> = {
  student: '/dashboard/student',
  worker: '/dashboard/worker',
  admin: '/dashboard/admin',
}

export const PROTECTED_ROUTES = [
  '/dashboard/student',
  '/dashboard/worker',
  '/dashboard/admin',
] as const

export function canAccessRoleRoute(route: string, role: UserRole): boolean {
  const allowedRoot = DASHBOARD_BY_ROLE[role]
  return route.startsWith(allowedRoot)
}

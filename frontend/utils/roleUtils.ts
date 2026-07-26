import type { UserRole } from '@/types/user'
import { DASHBOARD_BY_ROLE } from '@/routes/protectedRoutes'

export function getDashboardByRole(role: UserRole): string {
  return DASHBOARD_BY_ROLE[role]
}

export function isValidRole(role: string): role is UserRole {
  return role === 'student' || role === 'worker' || role === 'admin'
}

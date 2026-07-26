import type { UserRole } from '@/types/user'

export function getAccessToken() {
  if (typeof window === 'undefined') return null
  return localStorage.getItem('sbms_access_token')
}

export function setAccessToken(token: string) {
  if (typeof window === 'undefined') return
  localStorage.setItem('sbms_access_token', token)
}

export function clearAuthStorage() {
  if (typeof window === 'undefined') return
  localStorage.removeItem('sbms_access_token')
  localStorage.removeItem('sbms_user')
}

export function normalizeRole(role: string): UserRole {
  if (role === 'staff') return 'worker'
  if (role === 'admin') return 'admin'
  if (role === 'worker') return 'worker'
  return 'student'
}

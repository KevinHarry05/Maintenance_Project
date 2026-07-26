'use client'

import { useEffect } from 'react'
import { usePathname, useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { getDashboardByRole } from '@/utils/roleUtils'
import type { UserRole } from '@/types/user'

export function RoleGuard({
  allowedRoles,
  children,
}: {
  allowedRoles: UserRole[]
  children: React.ReactNode
}) {
  const { user, loading } = useAuth()
  const router = useRouter()
  const pathname = usePathname()

  useEffect(() => {
    if (loading) return

    if (!user) {
      router.replace('/login')
      return
    }

    if (!allowedRoles.includes(user.role)) {
      router.replace(getDashboardByRole(user.role))
    }
  }, [allowedRoles, loading, pathname, router, user])

  if (loading || !user || !allowedRoles.includes(user.role)) {
    return null
  }

  return <>{children}</>
}

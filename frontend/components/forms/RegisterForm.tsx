'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useAuth } from '@/hooks/useAuth'
import type { UserRole } from '@/types/user'
import { getDashboardByRole } from '@/utils/roleUtils'

export function RegisterForm() {
  const router = useRouter()
  const { register, user } = useAuth()
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [role, setRole] = useState<UserRole>('student')

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    await register({ full_name: fullName, email, password, role })
    router.push(getDashboardByRole(user?.role || role))
  }

  return (
    <form onSubmit={onSubmit} className="space-y-4">
      <Input value={fullName} onChange={(e) => setFullName(e.target.value)} placeholder="Full name" required />
      <Input value={email} onChange={(e) => setEmail(e.target.value)} type="email" placeholder="name@college.edu" required />
      <Input value={password} onChange={(e) => setPassword(e.target.value)} type="password" placeholder="••••••••" required />
      <select className="w-full rounded-md border border-blue-200 bg-white px-3 py-2" value={role} onChange={(e) => setRole(e.target.value as UserRole)}>
        <option value="student">Student</option>
        <option value="worker">Worker</option>
        <option value="admin">Admin</option>
      </select>
      <Button type="submit" className="w-full">Create account</Button>
    </form>
  )
}

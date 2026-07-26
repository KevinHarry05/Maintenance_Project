'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useAuth } from '@/hooks/useAuth'
import { getDashboardByRole } from '@/utils/roleUtils'

export function LoginForm() {
  const router = useRouter()
  const { login, user } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      await login({ email, password })
      const role = user?.role || 'student'
      router.push(getDashboardByRole(role))
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={onSubmit} className="space-y-4">
      <Input value={email} onChange={(e) => setEmail(e.target.value)} type="email" placeholder="name@college.edu" required />
      <Input value={password} onChange={(e) => setPassword(e.target.value)} type="password" placeholder="••••••••" required />
      <Button type="submit" disabled={loading} className="w-full">
        {loading ? 'Signing in...' : 'Sign In'}
      </Button>
    </form>
  )
}

'use client'

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import { authService } from '@/services/authService'
import type { LoginPayload, RegisterPayload, User } from '@/types/user'

type AuthContextValue = {
  user: User | null
  isAuthenticated: boolean
  loading: boolean
  login: (payload: LoginPayload) => Promise<void>
  register: (payload: RegisterPayload) => Promise<void>
  logout: () => Promise<void>
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  const refreshUser = useCallback(async () => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('sbms_access_token') : null

    if (!token) {
      setUser(null)
      setLoading(false)
      return
    }

    try {
      const me = await authService.me()
      setUser(me)
      // Persist user to localStorage so dashboard layout and login redirect can read role
      if (typeof window !== 'undefined') {
        localStorage.setItem('sbms_user', JSON.stringify({ role: me.role, email: me.email, fullName: me.full_name }))
      }
    } catch {
      setUser(null)
      if (typeof window !== 'undefined') {
        localStorage.removeItem('sbms_access_token')
        localStorage.removeItem('sbms_user')
      }
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void refreshUser()
  }, [refreshUser])

  const login = useCallback(async (payload: LoginPayload) => {
    const tokens = await authService.login(payload)
    if (typeof window !== 'undefined') {
      localStorage.setItem('sbms_access_token', tokens.access_token)
    }
    await refreshUser()
  }, [refreshUser])

  const register = useCallback(async (payload: RegisterPayload) => {
    await authService.register(payload)
    await login({ email: payload.email, password: payload.password })
  }, [login])

  const logout = useCallback(async () => {
    try {
      await authService.logout()
    } finally {
      if (typeof window !== 'undefined') {
        localStorage.removeItem('sbms_access_token')
        localStorage.removeItem('sbms_user')
      }
      setUser(null)
    }
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isAuthenticated: !!user,
      loading,
      login,
      register,
      logout,
      refreshUser,
    }),
    [user, loading, login, register, logout, refreshUser],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuthContext() {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuthContext must be used inside AuthProvider')
  }
  return ctx
}

export type UserRole = 'student' | 'worker' | 'admin'

export interface User {
  id: string
  full_name: string
  email: string
  role: UserRole
  is_active?: boolean
  created_at?: string
}

export interface AuthTokens {
  access_token: string
  token_type: 'bearer'
}

export interface LoginPayload {
  email: string
  password: string
}

export interface RegisterPayload {
  full_name: string
  email: string
  password: string
  role: UserRole
}

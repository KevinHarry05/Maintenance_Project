import { apiGet, apiPost } from '@/lib/api'
import { axiosInstance } from '@/lib/axiosInstance'
import { API_ROUTES } from '@/routes/apiRoutes'
import type { AuthTokens, LoginPayload, RegisterPayload, User } from '@/types/user'

export const authService = {
  register: (payload: RegisterPayload) =>
    apiPost<User, { full_name: string; email: string; password: string; role: string }>(
      API_ROUTES.AUTH_REGISTER,
      { full_name: payload.full_name, email: payload.email, password: payload.password, role: payload.role },
    ),

  login: async (payload: LoginPayload): Promise<AuthTokens> => {
    // Backend uses OAuth2PasswordRequestForm: expects form-encoded username + password
    const form = new URLSearchParams()
    form.append('username', payload.email)
    form.append('password', payload.password)
    const response = await axiosInstance.post<AuthTokens>(API_ROUTES.AUTH_LOGIN, form, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
    return response.data
  },

  me: async (): Promise<User> => {
    // Backend returns { id, name, email, role } — map name → full_name
    const data = await apiGet<{ id: string; name: string; full_name?: string; email: string; role: string }>(
      API_ROUTES.AUTH_ME,
    )
    return { ...data, full_name: data.full_name ?? data.name } as User
  },

  logout: () => apiPost<{ success: boolean }, Record<string, never>>(API_ROUTES.AUTH_LOGOUT, {}),
}

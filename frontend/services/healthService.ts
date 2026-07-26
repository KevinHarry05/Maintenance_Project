import { apiGet } from '@/lib/api'
import { API_ROUTES } from '@/routes/apiRoutes'

export interface HealthResponse {
  status: string
  version?: string
}

export const healthService = {
  getHealth: () => apiGet<HealthResponse>(API_ROUTES.HEALTH),
}

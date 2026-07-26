import { apiGet } from '@/lib/api'
import { API_ROUTES } from '@/routes/apiRoutes'

export interface WorkerUser {
  id: string
  name: string
  email: string
  role: 'worker'
}

export const userService = {
  getWorkers: () => apiGet<WorkerUser[]>(API_ROUTES.USERS_WORKERS),
}

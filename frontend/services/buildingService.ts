import { apiDelete, apiGet, apiPost, apiPut } from '@/lib/api'
import { API_ROUTES } from '@/routes/apiRoutes'
import type { Building, BuildingPayload } from '@/types/building'

export const buildingService = {
  getBuildings: () => apiGet<Building[]>(API_ROUTES.BUILDINGS),

  createBuilding: (payload: BuildingPayload) => apiPost<Building, BuildingPayload>(API_ROUTES.BUILDINGS, payload),

  updateBuilding: (id: string, payload: Partial<BuildingPayload>) =>
    apiPut<Building, Partial<BuildingPayload>>(`${API_ROUTES.BUILDINGS}/${id}`, payload),

  deleteBuilding: (id: string) => apiDelete<{ message: string }>(`${API_ROUTES.BUILDINGS}/${id}`),
}

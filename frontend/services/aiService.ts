import { apiPost } from '@/lib/api'
import { API_ROUTES } from '@/routes/apiRoutes'

export interface AIPredictPayload {
  title: string
  description: string
}

export interface AIPredictResult {
  category: string
  priority: 'Low' | 'Medium' | 'High' | 'Critical'
  confidence?: number
}

export const aiService = {
  predict: (payload: AIPredictPayload) => apiPost<AIPredictResult, AIPredictPayload>(API_ROUTES.AI_PREDICT, payload),
}

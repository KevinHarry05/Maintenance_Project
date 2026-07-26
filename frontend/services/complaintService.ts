import { apiGet, apiPut } from '@/lib/api'
import { axiosInstance } from '@/lib/axiosInstance'
import { API_ROUTES } from '@/routes/apiRoutes'
import type {
  AssignComplaintPayload,
  Complaint,
  CreateComplaintPayload,
  UpdateComplaintStatusPayload,
} from '@/types/complaint'

function toComplaintFormData(payload: CreateComplaintPayload) {
  const formData = new FormData()
  formData.append('title', payload.title)
  formData.append('description', payload.description)
  formData.append('building_id', payload.building_id)
  formData.append('floor_number', payload.floor_number)
  formData.append('room_number', payload.room_number)
  if (payload.category) formData.append('category', payload.category)
  if (payload.image) formData.append('file', payload.image)
  return formData
}

export const complaintService = {
  createComplaint: async (payload: CreateComplaintPayload) => {
    const formData = toComplaintFormData(payload)
    const response = await axiosInstance.post<Complaint>(API_ROUTES.COMPLAINT_CREATE, formData)
    return response.data
  },

  getMyComplaints: () => apiGet<Complaint[]>(API_ROUTES.COMPLAINT_MY),

  getAllComplaints: () => apiGet<Complaint[]>(API_ROUTES.COMPLAINT_ALL),

  getAssignedComplaints: () => apiGet<Complaint[]>(API_ROUTES.COMPLAINT_ASSIGNED),

  assignComplaint: (id: string, payload: AssignComplaintPayload) =>
    apiPut<{ message: string }, AssignComplaintPayload>(API_ROUTES.COMPLAINT_ASSIGN(id), payload),

  updateComplaintStatus: (id: string, payload: UpdateComplaintStatusPayload) =>
    apiPut<{ message: string }, UpdateComplaintStatusPayload>(API_ROUTES.COMPLAINT_STATUS(id), payload),

  escalateComplaint: (id: string) =>
    axiosInstance.post<{ message: string }>(API_ROUTES.COMPLAINT_ESCALATE(id)).then((r) => r.data),

  cancelEscalation: (id: string) =>
    axiosInstance.post<{ message: string }>(API_ROUTES.COMPLAINT_CANCEL_ESCALATION(id)).then((r) => r.data),

  uploadResolution: async (id: string, file?: File | null) => {
    const formData = new FormData()
    if (file) formData.append('file', file)
    const response = await axiosInstance.post<{ message: string }>(
      API_ROUTES.COMPLAINT_UPLOAD_RESOLUTION(id),
      formData
    )
    return response.data
  },

  adminResolve: (id: string) =>
    axiosInstance.post<{ message: string }>(API_ROUTES.COMPLAINT_ADMIN_RESOLVE(id)).then((r) => r.data),
}

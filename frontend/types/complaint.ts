export type ComplaintPriority = 'Low' | 'Medium' | 'High' | 'Critical'
export type ComplaintStatus = string

export interface Complaint {
  id: string
  title: string
  description: string
  category?: string | null
  file_path?: string | null
  resolution_file_path?: string | null
  status: ComplaintStatus
  priority_score: number
  priority_level: ComplaintPriority
  building_id: string
  floor_number: string
  room_number: string
  user_id: string
  assigned_to?: string | null
  created_at?: string
  worker_remarks?: string | null
  admin_remarks?: string | null
  admin_verified: boolean
  feedback_rating?: number | null
  feedback_comment?: string | null
}

export interface CreateComplaintPayload {
  title: string
  description: string
  building_id: string
  floor_number: string
  room_number: string
  category?: string
  image?: File | null
}

export interface AssignComplaintPayload {
  assignee_id: string
}

export interface UpdateComplaintStatusPayload {
  status: string
}

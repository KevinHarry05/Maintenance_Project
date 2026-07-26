export const API_ROUTES = {
  AUTH_REGISTER: '/auth/register',
  AUTH_LOGIN: '/auth/login',
  AUTH_ME: '/auth/me',
  AUTH_LOGOUT: '/auth/logout',

  USERS_WORKERS: '/users/workers',

  BUILDINGS: '/buildings',

  COMPLAINT_CREATE: '/complaints',
  COMPLAINT_MY: '/complaints/my',
  COMPLAINT_ALL: '/complaints/all',
  COMPLAINT_ASSIGNED: '/complaints/assigned',
  COMPLAINT_ASSIGN: (id: string) => `/complaints/${id}/assign`,
  COMPLAINT_STATUS: (id: string) => `/complaints/${id}/status`,
  COMPLAINT_ESCALATE: (id: string) => `/complaints/${id}/escalate`,
  COMPLAINT_CANCEL_ESCALATION: (id: string) => `/complaints/${id}/cancel-escalation`,
  COMPLAINT_UPLOAD_RESOLUTION: (id: string) => `/complaints/${id}/upload-resolution`,
  COMPLAINT_ADMIN_RESOLVE: (id: string) => `/complaints/${id}/admin-resolve`,

  NOTIFICATIONS: '/notifications',
  NOTIFICATION_MARK_READ: (id: string) => `/notifications/${id}/read`,

  AI_PREDICT: '/ai/predict',
  HEALTH: '/health',

  WS_NOTIFICATIONS: '/ws',
} as const

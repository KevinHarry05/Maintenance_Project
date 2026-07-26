export interface APIResponse<T> {
  success: boolean
  message: string
  data: T
}

export interface APIErrorResponse {
  detail?: string
  message?: string
  error?: string
}

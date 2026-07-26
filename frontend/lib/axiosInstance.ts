import axios, { AxiosError } from 'axios'
import type { APIErrorResponse } from '@/types/apiResponse'

const envBaseUrl = process.env.NEXT_PUBLIC_API_URL?.trim()
const baseURL = envBaseUrl || (process.env.NODE_ENV === 'production' ? '' : 'http://localhost:8000')

export const axiosInstance = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
})

axiosInstance.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('sbms_access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
  }

  return config
})

axiosInstance.interceptors.response.use(
  (response) => {
    // Backend wraps all JSON responses in { success, data, message, request_id }.
    // Unwrap here so callers receive the inner data directly.
    const body = response.data as Record<string, unknown>
    if (
      body !== null &&
      typeof body === 'object' &&
      'success' in body &&
      'data' in body &&
      body.success === true
    ) {
      response.data = body.data
    }
    return response
  },
  (error: AxiosError<APIErrorResponse>) => {
    const status = error.response?.status
    const detail =
      error.response?.data?.detail ||
      error.response?.data?.message ||
      error.response?.data?.error ||
      error.message

    if (status === 401 && typeof window !== 'undefined') {
      localStorage.removeItem('sbms_access_token')
      localStorage.removeItem('sbms_user')
    }

    if (status === 401) {
      return Promise.reject(new Error(detail || 'Unauthorized'))
    }

    if (status === 403) {
      return Promise.reject(new Error(detail || 'Forbidden'))
    }

    if (status && status >= 500) {
      return Promise.reject(new Error(detail || 'Server error occurred'))
    }

    return Promise.reject(new Error(detail || 'Request failed'))
  },
)

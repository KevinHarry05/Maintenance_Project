import { axiosInstance } from '@/lib/axiosInstance'

export async function apiGet<T>(url: string) {
  const response = await axiosInstance.get<T>(url)
  return response.data
}

export async function apiPost<TResponse, TPayload>(url: string, payload: TPayload) {
  const response = await axiosInstance.post<TResponse>(url, payload)
  return response.data
}

export async function apiPut<TResponse, TPayload>(url: string, payload: TPayload) {
  const response = await axiosInstance.put<TResponse>(url, payload)
  return response.data
}

export async function apiDelete<TResponse>(url: string) {
  const response = await axiosInstance.delete<TResponse>(url)
  return response.data
}

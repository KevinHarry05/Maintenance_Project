export function toMultipartFormData(
  payload: Record<string, string | number | File | Blob | null | undefined>,
) {
  const formData = new FormData()

  Object.entries(payload).forEach(([key, value]) => {
    if (value === null || value === undefined) return
    if (value instanceof Blob) {
      formData.append(key, value)
      return
    }
    formData.append(key, String(value))
  })

  return formData
}

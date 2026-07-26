export interface Building {
  id: string
  name: string
  block: string
  floor_count: number
  created_at?: string
}

export interface BuildingPayload {
  name: string
  block: string
  floor_count: number
}

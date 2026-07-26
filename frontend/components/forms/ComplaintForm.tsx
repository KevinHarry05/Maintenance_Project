'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { useCreateComplaint } from '@/hooks/useComplaints'
import { useBuildings } from '@/hooks/useBuildings'

export function ComplaintForm() {
  const createComplaint = useCreateComplaint()
  const { data: buildings = [] } = useBuildings()
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [buildingId, setBuildingId] = useState('')
  const [floorNumber, setFloorNumber] = useState('')
  const [roomNumber, setRoomNumber] = useState('')
  const [image, setImage] = useState<File | null>(null)

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    await createComplaint.mutateAsync({ title, description, building_id: buildingId, floor_number: floorNumber, room_number: roomNumber, image })
    setTitle('')
    setDescription('')
    setBuildingId('')
    setFloorNumber('')
    setRoomNumber('')
    setImage(null)
  }

  return (
    <form onSubmit={onSubmit} className="space-y-4">
      <Input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Complaint title" required />
      <select
        value={buildingId}
        onChange={(e) => setBuildingId(e.target.value)}
        className="w-full px-3 py-2 border border-border rounded-md bg-input text-foreground"
        required
      >
        <option value="">Select building</option>
        {buildings.map((b) => (
          <option key={b.id} value={b.id}>{b.name}</option>
        ))}
      </select>
      <Input value={floorNumber} onChange={(e) => setFloorNumber(e.target.value)} placeholder="Floor number" required />
      <Input value={roomNumber} onChange={(e) => setRoomNumber(e.target.value)} placeholder="Room number" required />
      <Textarea value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Describe the issue" required />
      <Input type="file" accept="image/*" onChange={(e) => setImage(e.target.files?.[0] || null)} />
      <Button type="submit" disabled={createComplaint.isPending}>
        {createComplaint.isPending ? 'Submitting...' : 'Submit Complaint'}
      </Button>
    </form>
  )
}

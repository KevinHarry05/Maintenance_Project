'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useCreateBuilding } from '@/hooks/useBuildings'

export function BuildingForm() {
  const createBuilding = useCreateBuilding()
  const [name, setName] = useState('')
  const [block, setBlock] = useState('')
  const [floorCount, setFloorCount] = useState('')

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    await createBuilding.mutateAsync({ name, block, floor_count: Number(floorCount) })
    setName('')
    setBlock('')
    setFloorCount('')
  }

  return (
    <form onSubmit={onSubmit} className="space-y-4">
      <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Building name" required />
      <Input value={block} onChange={(e) => setBlock(e.target.value)} placeholder="Block (e.g. A, B)" required />
      <Input type="number" value={floorCount} onChange={(e) => setFloorCount(e.target.value)} placeholder="Number of floors" required />
      <Button type="submit" disabled={createBuilding.isPending}>
        {createBuilding.isPending ? 'Saving...' : 'Save Building'}
      </Button>
    </form>
  )
}

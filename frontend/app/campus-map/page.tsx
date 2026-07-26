import { CampusMap } from '@/components/map/CampusMap'

export default function CampusMapPage() {
  return (
    <div className="space-y-4">
      <h1 className="text-3xl font-bold text-foreground">Campus Map</h1>
      <CampusMap />
    </div>
  )
}

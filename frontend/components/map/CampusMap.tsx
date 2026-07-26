import { Card } from '@/components/ui/card'

export function CampusMap() {
  return (
    <Card className="p-6">
      <h2 className="text-lg font-semibold text-foreground">Campus Map</h2>
      <p className="mt-2 text-sm text-muted-foreground">
        Interactive campus map will be rendered here. Connect this component to map tiles or GIS data.
      </p>
    </Card>
  )
}

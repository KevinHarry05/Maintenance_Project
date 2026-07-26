import { Card } from '@/components/ui/card'

export function StatsCard({
  title,
  value,
  description,
}: {
  title: string
  value: string | number
  description?: string
}) {
  return (
    <Card className="border-blue-100 bg-white p-6">
      <p className="text-sm text-muted-foreground">{title}</p>
      <p className="mt-2 text-3xl font-bold text-foreground">{value}</p>
      {description ? <p className="mt-2 text-xs text-muted-foreground">{description}</p> : null}
    </Card>
  )
}

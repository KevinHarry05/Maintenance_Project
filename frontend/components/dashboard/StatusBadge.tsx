import { Badge } from '@/components/ui/badge'

export function StatusBadge({ status }: { status: string }) {
  const color =
    status === 'Resolved'
      ? 'bg-green-100 text-green-700'
      : status === 'In Progress'
        ? 'bg-blue-100 text-blue-700'
        : status === 'Assigned'
          ? 'bg-purple-100 text-purple-700'
          : 'bg-gray-100 text-gray-700'

  return <Badge className={color}>{status}</Badge>
}

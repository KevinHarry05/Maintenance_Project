import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { StatusBadge } from '@/components/dashboard/StatusBadge'
import type { Complaint } from '@/types/complaint'

export function ComplaintTable({ complaints }: { complaints: Complaint[] }) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>ID</TableHead>
          <TableHead>Title</TableHead>
          <TableHead>Priority</TableHead>
          <TableHead>Status</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {complaints.map((complaint) => (
          <TableRow key={complaint.id}>
            <TableCell>{complaint.id.slice(0, 8)}</TableCell>
            <TableCell>{complaint.title}</TableCell>
            <TableCell>{complaint.priority_level}</TableCell>
            <TableCell>
              <StatusBadge status={complaint.status} />
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}

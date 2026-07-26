import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog'
import type { Complaint } from '@/types/complaint'

export function ComplaintDetailModal({
  complaint,
  open,
  onOpenChange,
}: {
  complaint: Complaint | null
  open: boolean
  onOpenChange: (open: boolean) => void
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{complaint?.title || 'Complaint Details'}</DialogTitle>
          <DialogDescription>{complaint?.description || 'No details available.'}</DialogDescription>
        </DialogHeader>
      </DialogContent>
    </Dialog>
  )
}

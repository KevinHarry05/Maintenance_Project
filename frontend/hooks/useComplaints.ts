'use client'

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { complaintService } from '@/services/complaintService'
import type {
  AssignComplaintPayload,
  CreateComplaintPayload,
  UpdateComplaintStatusPayload,
} from '@/types/complaint'

export const complaintKeys = {
  all: ['complaints'] as const,
  my: ['complaints', 'my'] as const,
  assigned: ['complaints', 'assigned'] as const,
}

export function useMyComplaints() {
  return useQuery({
    queryKey: complaintKeys.my,
    queryFn: complaintService.getMyComplaints,
  })
}

export function useAllComplaints() {
  return useQuery({
    queryKey: complaintKeys.all,
    queryFn: complaintService.getAllComplaints,
  })
}

export function useAssignedComplaints() {
  return useQuery({
    queryKey: complaintKeys.assigned,
    queryFn: complaintService.getAssignedComplaints,
  })
}

export function useCreateComplaint() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (payload: CreateComplaintPayload) => complaintService.createComplaint(payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: complaintKeys.my })
      void queryClient.invalidateQueries({ queryKey: complaintKeys.all })
    },
  })
}

export function useAssignComplaint() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: AssignComplaintPayload }) =>
      complaintService.assignComplaint(id, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: complaintKeys.all })
      void queryClient.invalidateQueries({ queryKey: complaintKeys.assigned })
    },
  })
}

export function useUpdateComplaintStatus() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: UpdateComplaintStatusPayload }) =>
      complaintService.updateComplaintStatus(id, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: complaintKeys.my })
      void queryClient.invalidateQueries({ queryKey: complaintKeys.all })
      void queryClient.invalidateQueries({ queryKey: complaintKeys.assigned })
    },
  })
}

export function useEscalateComplaint() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => complaintService.escalateComplaint(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: complaintKeys.my })
      void queryClient.invalidateQueries({ queryKey: complaintKeys.all })
    },
  })
}

export function useCancelEscalation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => complaintService.cancelEscalation(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: complaintKeys.my })
      void queryClient.invalidateQueries({ queryKey: complaintKeys.all })
    },
  })
}

export function useUploadResolution() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, file }: { id: string; file?: File | null }) =>
      complaintService.uploadResolution(id, file),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: complaintKeys.my })
      void queryClient.invalidateQueries({ queryKey: complaintKeys.all })
      void queryClient.invalidateQueries({ queryKey: complaintKeys.assigned })
    },
  })
}

export function useAdminResolve() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => complaintService.adminResolve(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: complaintKeys.all })
      void queryClient.invalidateQueries({ queryKey: complaintKeys.assigned })
      void queryClient.invalidateQueries({ queryKey: complaintKeys.my })
    },
  })
}

'use client'

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { buildingService } from '@/services/buildingService'
import type { BuildingPayload } from '@/types/building'

const buildingKeys = {
  all: ['buildings'] as const,
}

export function useBuildings() {
  return useQuery({
    queryKey: buildingKeys.all,
    queryFn: buildingService.getBuildings,
    // Building IDs are database-backed. Always refresh them when this selector
    // mounts so a restarted or reseeded backend cannot leave a stale ID selected.
    refetchOnMount: 'always',
  })
}

export function useCreateBuilding() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (payload: BuildingPayload) => buildingService.createBuilding(payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: buildingKeys.all })
    },
  })
}

export function useUpdateBuilding() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: Partial<BuildingPayload> }) =>
      buildingService.updateBuilding(id, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: buildingKeys.all })
    },
  })
}

export function useDeleteBuilding() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => buildingService.deleteBuilding(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: buildingKeys.all })
    },
  })
}

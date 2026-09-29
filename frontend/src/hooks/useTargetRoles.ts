import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { targetRoleService } from '@/services/targetRoleService'
import { useAuthStore } from '@/store/authStore'
import type { CreateTargetRolePayload } from '@/types'
import { getApiErrorMessage } from '@/utils/errors'

// ── Student's roles ───────────────────────────────────────────────────────────
export function useTargetRoles() {
  const user = useAuthStore((s) => s.user)
  return useQuery({
    queryKey: ['target-roles', user?.id],
    queryFn: targetRoleService.list,
    staleTime: 1000 * 60,
    enabled: !!user?.id,
  })
}

export function usePrimaryRole() {
  const user = useAuthStore((s) => s.user)
  return useQuery({
    queryKey: ['target-roles', user?.id, 'primary'],
    queryFn: targetRoleService.getPrimary,
    staleTime: 1000 * 60,
    retry: false,           // don't retry on 404 (no primary set)
    enabled: !!user?.id,
  })
}

// ── Catalogue ─────────────────────────────────────────────────────────────────
export function useRoleCatalogue(params?: { domain?: string; q?: string }) {
  return useQuery({
    queryKey: ['role-catalogue', params],
    queryFn: () => targetRoleService.getCatalogue(params),
    staleTime: 1000 * 60 * 10,   // catalogue rarely changes
  })
}

// ── Skill gap ─────────────────────────────────────────────────────────────────
export function useSkillGap(roleId?: string) {
  const user = useAuthStore((s) => s.user)
  return useQuery({
    queryKey: ['skill-gap', user?.id, roleId ?? 'primary'],
    queryFn: () => targetRoleService.getSkillGap(roleId),
    staleTime: 1000 * 60 * 5,
    retry: false,
    enabled: !!user?.id,
  })
}

// ── Mutations ─────────────────────────────────────────────────────────────────
export function useCreateTargetRole() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: CreateTargetRolePayload) => targetRoleService.create(data),
    onSuccess: (role) => {
      qc.invalidateQueries({ queryKey: ['target-roles'] })
      qc.invalidateQueries({ queryKey: ['profile'] })
      toast.success(`"${role.role_name}" added!`)
    },
    onError: (err) => toast.error(getApiErrorMessage(err, 'Failed to add role.')),
  })
}

export function useUpdateTargetRole() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<CreateTargetRolePayload> }) =>
      targetRoleService.update(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['target-roles'] })
      toast.success('Role updated.')
    },
    onError: (err) => toast.error(getApiErrorMessage(err, 'Failed to update role.')),
  })
}

export function useDeleteTargetRole() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => targetRoleService.delete(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['target-roles'] })
      qc.invalidateQueries({ queryKey: ['skill-gap'] })
      qc.invalidateQueries({ queryKey: ['profile'] })
      toast.success('Role removed.')
    },
    onError: (err) => toast.error(getApiErrorMessage(err, 'Failed to delete role.')),
  })
}

export function useSetPrimaryRole() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => targetRoleService.setPrimary(id),
    onSuccess: (role) => {
      qc.invalidateQueries({ queryKey: ['target-roles'] })
      qc.invalidateQueries({ queryKey: ['skill-gap'] })
      toast.success(`"${role.role_name}" is now your primary role.`)
    },
    onError: (err) => toast.error(getApiErrorMessage(err, 'Failed to set primary role.')),
  })
}

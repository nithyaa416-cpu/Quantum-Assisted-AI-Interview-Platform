import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useEffect, useRef } from 'react'
import toast from 'react-hot-toast'
import { resumeService } from '@/services/resumeService'
import { useAuthStore } from '@/store/authStore'
import type { ParsedDataUpdate, TargetRole } from '@/types'

// ── List ──────────────────────────────────────────────────────────────────────
export function useResumes() {
  const user = useAuthStore((s) => s.user)
  return useQuery({
    queryKey: ['resumes', user?.id],
    queryFn: resumeService.list,
    staleTime: 1000 * 30,
    enabled: !!user?.id,
  })
}

// ── Detail ────────────────────────────────────────────────────────────────────
export function useResumeDetail(id: string | null) {
  const user = useAuthStore((s) => s.user)
  return useQuery({
    queryKey: ['resume', user?.id, id],
    queryFn: () => resumeService.getDetail(id!),
    enabled: !!id && !!user?.id,
    staleTime: 1000 * 30,
  })
}

// ── Status polling — auto-stops when completed/failed ─────────────────────────
export function useResumeStatus(id: string | null) {
  const user = useAuthStore((s) => s.user)
  const qc = useQueryClient()
  return useQuery({
    queryKey: ['resume-status', user?.id, id],
    queryFn: () => resumeService.getStatus(id!),
    enabled: !!id && !!user?.id,
    refetchInterval: (query) => {
      const s = query.state.data?.parse_status
      if (!s || s === 'completed' || s === 'failed') return false
      return 2000   // poll every 2s while pending/processing
    },
    // When status becomes completed, invalidate detail + list
    select: (data) => {
      if (data.parse_status === 'completed' || data.parse_status === 'failed') {
        qc.invalidateQueries({ queryKey: ['resume'] })
        qc.invalidateQueries({ queryKey: ['resumes'] })
      }
      return data
    },
  })
}

import { getApiErrorMessage } from '@/utils/errors'

// ── Upload ────────────────────────────────────────────────────────────────────
export function useUploadResume() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (file: File) => resumeService.upload(file),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['resumes'] })
      toast.success('Resume uploaded successfully!')
    },
    onError: (err: unknown) => {
      toast.error(getApiErrorMessage(err, 'Upload failed. Please try again.'))
    },
  })
}

// ── Update parsed data ────────────────────────────────────────────────────────
export function useUpdateResumeData(id: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: ParsedDataUpdate) => resumeService.updateParsedData(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['resume', id] })
      qc.invalidateQueries({ queryKey: ['resumes'] })
      toast.success('Changes saved!')
    },
    onError: () => {
      toast.error('Failed to save changes.')
    },
  })
}

// ── Delete ────────────────────────────────────────────────────────────────────
export function useDeleteResume() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => resumeService.delete(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['resumes'] })
      toast.success('Resume deleted.')
    },
    onError: () => {
      toast.error('Failed to delete resume.')
    },
  })
}

// ── Re-parse ──────────────────────────────────────────────────────────────────
export function useReParse() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => resumeService.triggerParse(id),
    onSuccess: (_d, id) => {
      qc.invalidateQueries({ queryKey: ['resume-status', id] })
      qc.invalidateQueries({ queryKey: ['resumes'] })
      toast.success('Re-parsing started.')
    },
  })
}

// ── Target roles ──────────────────────────────────────────────────────────────
export function useTargetRoles() {
  const user = useAuthStore((s) => s.user)
  return useQuery({
    queryKey: ['target-roles', user?.id],
    queryFn: resumeService.listTargetRoles,
    staleTime: 1000 * 60,
    enabled: !!user?.id,
  })
}

export function useCreateTargetRole() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: Omit<TargetRole, 'id' | 'created_at'>) =>
      resumeService.createTargetRole(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['target-roles'] })
      toast.success('Target role added.')
    },
  })
}

export function useDeleteTargetRole() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => resumeService.deleteTargetRole(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['target-roles'] })
      toast.success('Target role removed.')
    },
  })
}

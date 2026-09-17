import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useEffect, useRef } from 'react'
import toast from 'react-hot-toast'
import { resumeService } from '@/services/resumeService'
import type { ParsedDataUpdate, TargetRole } from '@/types'

// ── List ──────────────────────────────────────────────────────────────────────
export function useResumes() {
  return useQuery({
    queryKey: ['resumes'],
    queryFn: resumeService.list,
    staleTime: 1000 * 30,
  })
}

// ── Detail ────────────────────────────────────────────────────────────────────
export function useResumeDetail(id: string | null) {
  return useQuery({
    queryKey: ['resume', id],
    queryFn: () => resumeService.getDetail(id!),
    enabled: !!id,
    staleTime: 1000 * 30,
  })
}

// ── Status polling — auto-stops when completed/failed ─────────────────────────
export function useResumeStatus(id: string | null) {
  const qc = useQueryClient()
  return useQuery({
    queryKey: ['resume-status', id],
    queryFn: () => resumeService.getStatus(id!),
    enabled: !!id,
    refetchInterval: (query) => {
      const s = query.state.data?.parse_status
      if (!s || s === 'completed' || s === 'failed') return false
      return 2000   // poll every 2s while pending/processing
    },
    // When status becomes completed, invalidate detail + list
    select: (data) => {
      if (data.parse_status === 'completed' || data.parse_status === 'failed') {
        qc.invalidateQueries({ queryKey: ['resume', id] })
        qc.invalidateQueries({ queryKey: ['resumes'] })
      }
      return data
    },
  })
}

// ── Upload ────────────────────────────────────────────────────────────────────
export function useUploadResume() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (file: File) => resumeService.upload(file),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['resumes'] })
      toast.success('Resume uploaded! Parsing started…')
    },
    onError: () => {
      toast.error('Upload failed. Please try again.')
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
  return useQuery({
    queryKey: ['target-roles'],
    queryFn: resumeService.listTargetRoles,
    staleTime: 1000 * 60,
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

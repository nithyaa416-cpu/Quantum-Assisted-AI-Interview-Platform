import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { interviewService } from '@/services/interviewService'
import { useAuthStore } from '@/store/authStore'
import type { StartInterviewPayload } from '@/types'
import { getApiErrorMessage } from '@/utils/errors'

export function useInterviewSessions() {
  const user = useAuthStore((s) => s.user)
  return useQuery({
    queryKey: ['interview-sessions', user?.id],
    queryFn: interviewService.listSessions,
    staleTime: 1000 * 30,
    enabled: !!user?.id,
  })
}

export function useInterviewSession(id: string | null) {
  const user = useAuthStore((s) => s.user)
  return useQuery({
    queryKey: ['interview-session', user?.id, id],
    queryFn: () => interviewService.getSession(id!),
    enabled: !!id && !!user?.id,
    staleTime: 0,   // always fresh during active interview
    refetchOnWindowFocus: false,
  })
}

export function useStartInterview() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: StartInterviewPayload) => interviewService.startSession(payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['interview-sessions'] })
    },
    onError: (err) => toast.error(getApiErrorMessage(err, 'Failed to start interview.')),
  })
}

export function useSubmitResponse(sessionId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({
      questionId,
      answer,
      duration,
    }: {
      questionId: string
      answer: string
      duration?: number
    }) => interviewService.submitResponse(sessionId, questionId, answer, duration),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['interview-session', sessionId] })
    },
    onError: (err) => toast.error(getApiErrorMessage(err, 'Failed to submit response.')),
  })
}

export function useEndInterview(sessionId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => interviewService.endSession(sessionId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['interview-sessions'] })
      qc.invalidateQueries({ queryKey: ['interview-session', sessionId] })
    },
    onError: (err) => toast.error(getApiErrorMessage(err, 'Failed to end interview.')),
  })
}

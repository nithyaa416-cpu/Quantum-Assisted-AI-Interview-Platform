import { useQuery } from '@tanstack/react-query'
import { sessionService } from '@/services/sessionService'
import { useAuthStore } from '@/store/authStore'

export function useSessions() {
  const user = useAuthStore((s) => s.user)
  return useQuery({
    queryKey: ['sessions', user?.id],
    queryFn: sessionService.getSessions,
    staleTime: 1000 * 60 * 2,
    enabled: !!user?.id,
  })
}

export function useAssessments() {
  const user = useAuthStore((s) => s.user)
  return useQuery({
    queryKey: ['assessments', user?.id],
    queryFn: sessionService.getAssessments,
    staleTime: 1000 * 60 * 2,
    enabled: !!user?.id,
  })
}

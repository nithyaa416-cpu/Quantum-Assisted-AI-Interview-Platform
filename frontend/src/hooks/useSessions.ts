import { useQuery } from '@tanstack/react-query'
import { sessionService } from '@/services/sessionService'

export function useSessions() {
  return useQuery({
    queryKey: ['sessions'],
    queryFn: sessionService.getSessions,
    staleTime: 1000 * 60 * 2,
  })
}

export function useAssessments() {
  return useQuery({
    queryKey: ['assessments'],
    queryFn: sessionService.getAssessments,
    staleTime: 1000 * 60 * 2,
  })
}

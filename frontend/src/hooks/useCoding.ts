import { useQuery, useMutation } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { codingService } from '@/services/codingService'
import { getApiErrorMessage } from '@/utils/errors'
import type {
  CodingRunRequest,
  CodingSubmissionRequest,
} from '@/types/coding'

export function useCodingProblems() {
  return useQuery({
    queryKey: ['coding-problems'],
    queryFn:  codingService.getProblems,
    staleTime: 1000 * 60 * 10,
  })
}

export function useCodingProblem(id: string | null) {
  return useQuery({
    queryKey: ['coding-problem', id],
    queryFn:  () => codingService.getProblem(id!),
    enabled:  !!id,
    staleTime: 1000 * 60 * 10,
  })
}

export function useRunCode() {
  return useMutation({
    mutationFn: (payload: CodingRunRequest) => codingService.runCode(payload),
    onError: (err) => {
      const msg = getApiErrorMessage(err, 'Code execution failed.')
      // Only toast for server/network errors, not wrong-answer
      if (!msg.includes('unavailable')) toast.error(msg)
    },
  })
}

export function useSubmitCode() {
  return useMutation({
    mutationFn: (payload: CodingSubmissionRequest) => codingService.submitCode(payload),
    onError: (err) => toast.error(getApiErrorMessage(err, 'Submission failed.')),
  })
}

/**
 * Coding Interview API service.
 * Reuses the existing authenticated Axios instance from api.ts.
 * Do NOT create a second Axios client.
 */
import api from './api'
import type {
  CodingProblemSummary,
  CodingProblem,
  CodingRunRequest,
  CodingRunResponse,
  CodingSubmissionRequest,
  CodingSubmissionResponse,
  CodingSubmissionHistoryItem,
} from '@/types/coding'

const BASE = '/api/assessments/coding'

export const codingService = {
  /** GET /api/assessments/coding/problems/ */
  async getProblems(): Promise<CodingProblemSummary[]> {
    const res = await api.get(`${BASE}/problems/`)
    return res.data.data
  },

  /** GET /api/assessments/coding/problems/{id}/ */
  async getProblem(id: string): Promise<CodingProblem> {
    const res = await api.get(`${BASE}/problems/${id}/`)
    return res.data.data
  },

  /** POST /api/assessments/coding/run/ */
  async runCode(payload: CodingRunRequest): Promise<CodingRunResponse> {
    const res = await api.post(`${BASE}/run/`, payload)
    return res.data.data
  },

  /** POST /api/assessments/coding/submit/ */
  async submitCode(payload: CodingSubmissionRequest): Promise<CodingSubmissionResponse> {
    const res = await api.post(`${BASE}/submit/`, payload)
    return res.data.data
  },

  /** GET /api/assessments/coding/submissions/ */
  async getSubmissions(): Promise<CodingSubmissionHistoryItem[]> {
    const res = await api.get(`${BASE}/submissions/`)
    return res.data.data
  },
}

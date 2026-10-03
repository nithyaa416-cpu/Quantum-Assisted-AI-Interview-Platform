import api from './api'
import type {
  InterviewSession, InterviewListItem,
  StartInterviewPayload, SubmitResponseResult,
  InterviewCodingResult,
} from '@/types'
import type { CodingProblem } from '@/types/coding'

export const interviewService = {
  async listSessions(): Promise<InterviewListItem[]> {
    const res = await api.get('/api/interview/sessions/')
    return res.data.data
  },

  async startSession(payload: StartInterviewPayload): Promise<InterviewSession> {
    const res = await api.post('/api/interview/sessions/', payload)
    return res.data.data
  },

  async getSession(id: string): Promise<InterviewSession> {
    const res = await api.get(`/api/interview/sessions/${id}/`)
    return res.data.data
  },

  async submitResponse(
    sessionId: string,
    questionId: string,
    answer: string,
    durationSeconds?: number
  ): Promise<SubmitResponseResult> {
    const res = await api.post(`/api/interview/sessions/${sessionId}/respond/`, {
      question_id: questionId,
      answer,
      duration_seconds: durationSeconds,
    })
    return res.data.data
  },

  async endSession(sessionId: string): Promise<{ session_id: string; status: string; total_questions: number; duration_seconds: number }> {
    const res = await api.post(`/api/interview/sessions/${sessionId}/end/`)
    return res.data.data
  },

  async getHistory(sessionId: string): Promise<InterviewSession> {
    const res = await api.get(`/api/interview/sessions/${sessionId}/history/`)
    return res.data.data
  },

  async transcribeAudio(audioBlob: Blob): Promise<string> {
    const formData = new FormData()
    formData.append('audio', audioBlob, 'candidate_answer.webm')
    const res = await api.post('/api/interview/transcribe/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return res.data?.data?.text || ''
  },

  /**
   * GET /api/interview/sessions/{id}/coding-problem/
   * Returns the coding problem assigned to the current coding-phase turn.
   * Call this when question_type === 'coding' to get the problem to display.
   */
  async getCodingProblemForQuestion(
    sessionId: string
  ): Promise<{ question_id: string; problem: CodingProblem }> {
    const res = await api.get(`/api/interview/sessions/${sessionId}/coding-problem/`)
    return res.data.data
  },

  /**
   * POST /api/interview/sessions/{id}/coding-submit/
   * Submits code during an interview session via Judge0.
   * Returns test results + a follow-up explanation question for the interviewer.
   */
  async submitInterviewCode(
    sessionId: string,
    payload: {
      question_id: string
      problem_id: string
      language: string
      source_code: string
    }
  ): Promise<InterviewCodingResult> {
    const res = await api.post(`/api/interview/sessions/${sessionId}/coding-submit/`, payload)
    return res.data.data
  },
}


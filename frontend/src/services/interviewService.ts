import api from './api'
import type {
  InterviewSession, InterviewListItem,
  StartInterviewPayload, SubmitResponseResult,
} from '@/types'

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
}

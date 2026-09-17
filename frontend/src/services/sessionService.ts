import api from './api'
import type { SessionSummary, Assessment } from '@/types'

export const sessionService = {
  async getSessions(): Promise<SessionSummary[]> {
    const res = await api.get('/api/sessions/')
    return res.data.data as SessionSummary[]
  },

  async getAssessments(): Promise<Assessment[]> {
    const res = await api.get('/api/assessments/')
    return res.data.data as Assessment[]
  },
}

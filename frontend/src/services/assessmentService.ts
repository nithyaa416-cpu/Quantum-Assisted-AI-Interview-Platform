import api from './api'
import type { Assessment } from '@/types'

export const assessmentService = {
  async getSessionAssessment(sessionId: string): Promise<Assessment | null> {
    try {
      const res = await api.get(`/api/assessments/sessions/${sessionId}/`)
      return res.data.data
    } catch {
      return null
    }
  },

  async listAssessments(): Promise<Assessment[]> {
    const res = await api.get('/api/assessments/')
    return res.data.data
  },
}

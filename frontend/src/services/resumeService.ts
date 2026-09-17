import api from './api'
import type {
  ResumeListItem, ResumeDetail, ResumeParseStatus,
  ActiveResumeSummary, ParsedDataUpdate, TargetRole,
} from '@/types'

export const resumeService = {
  // ── Resumes ──────────────────────────────────────────────────────────────
  async list(): Promise<ResumeListItem[]> {
    const res = await api.get('/api/resumes/')
    return res.data.data
  },

  async upload(file: File): Promise<ResumeListItem> {
    const form = new FormData()
    form.append('file', file)
    const res = await api.post('/api/resumes/upload/', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return res.data.data
  },

  async getDetail(id: string): Promise<ResumeDetail> {
    const res = await api.get(`/api/resumes/${id}/`)
    return res.data.data
  },

  async getStatus(id: string): Promise<ResumeParseStatus> {
    const res = await api.get(`/api/resumes/${id}/status/`)
    return res.data.data
  },

  async triggerParse(id: string): Promise<void> {
    await api.post(`/api/resumes/${id}/parse/`)
  },

  async getSkills(id: string): Promise<{ skills: ResumeDetail['skills']; grouped: Record<string, ResumeDetail['skills']> }> {
    const res = await api.get(`/api/resumes/${id}/skills/`)
    return res.data.data
  },

  async updateParsedData(id: string, data: ParsedDataUpdate): Promise<ResumeDetail> {
    const res = await api.patch(`/api/resumes/${id}/`, data)
    return res.data.data
  },

  async delete(id: string): Promise<void> {
    await api.delete(`/api/resumes/${id}/`)
  },

  async getActiveSummary(): Promise<ActiveResumeSummary> {
    const res = await api.get('/api/resumes/active/summary/')
    return res.data.data
  },

  // ── Target Roles ─────────────────────────────────────────────────────────
  async listTargetRoles(): Promise<TargetRole[]> {
    const res = await api.get('/api/resumes/target-roles/')
    return res.data.data
  },

  async createTargetRole(data: Omit<TargetRole, 'id' | 'created_at'>): Promise<TargetRole> {
    const res = await api.post('/api/resumes/target-roles/', data)
    return res.data.data
  },

  async updateTargetRole(id: string, data: Partial<TargetRole>): Promise<TargetRole> {
    const res = await api.patch(`/api/resumes/target-roles/${id}/`, data)
    return res.data.data
  },

  async deleteTargetRole(id: string): Promise<void> {
    await api.delete(`/api/resumes/target-roles/${id}/`)
  },
}

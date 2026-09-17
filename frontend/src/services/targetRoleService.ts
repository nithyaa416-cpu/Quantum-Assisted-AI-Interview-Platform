import api from './api'
import type {
  TargetRole, TargetRoleDetail, RoleCatalogueEntry,
  SkillGapResult, CreateTargetRolePayload,
} from '@/types'

export const targetRoleService = {
  // ── Student's roles ──────────────────────────────────────────────────────
  async list(): Promise<TargetRoleDetail[]> {
    const res = await api.get('/api/target-roles/')
    return res.data.data
  },

  async create(data: CreateTargetRolePayload): Promise<TargetRoleDetail> {
    const res = await api.post('/api/target-roles/', data)
    return res.data.data
  },

  async get(id: string): Promise<TargetRoleDetail> {
    const res = await api.get(`/api/target-roles/${id}/`)
    return res.data.data
  },

  async update(id: string, data: Partial<CreateTargetRolePayload>): Promise<TargetRoleDetail> {
    const res = await api.patch(`/api/target-roles/${id}/`, data)
    return res.data.data
  },

  async delete(id: string): Promise<void> {
    await api.delete(`/api/target-roles/${id}/`)
  },

  async setPrimary(id: string): Promise<TargetRoleDetail> {
    const res = await api.post(`/api/target-roles/${id}/set-primary/`)
    return res.data.data
  },

  async getPrimary(): Promise<TargetRoleDetail> {
    const res = await api.get('/api/target-roles/primary/')
    return res.data.data
  },

  // ── Catalogue ─────────────────────────────────────────────────────────────
  async getCatalogue(params?: { domain?: string; q?: string }): Promise<{
    roles: RoleCatalogueEntry[]
    total: number
  }> {
    const res = await api.get('/api/target-roles/catalogue/', { params })
    return res.data.data
  },

  // ── Skill gap ─────────────────────────────────────────────────────────────
  async getSkillGap(roleId?: string): Promise<SkillGapResult> {
    const params = roleId ? { role_id: roleId } : {}
    const res = await api.get('/api/target-roles/skill-gap/', { params })
    return res.data.data
  },
}

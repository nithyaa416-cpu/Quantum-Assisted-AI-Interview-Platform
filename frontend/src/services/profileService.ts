import api from './api'
import type { StudentProfile, ProfileUpdatePayload } from '@/types'

export const profileService = {
  async getProfile(): Promise<StudentProfile> {
    const res = await api.get('/api/profile/me')
    return res.data.data as StudentProfile
  },

  async updateProfile(data: ProfileUpdatePayload): Promise<StudentProfile> {
    const res = await api.patch('/api/profile/me', data)
    return res.data.data as StudentProfile
  },
}

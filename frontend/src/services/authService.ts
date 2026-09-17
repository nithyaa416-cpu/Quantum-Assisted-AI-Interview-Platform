import api from './api'
import type { AuthResponse, LoginFormData, RegisterFormData, User } from '@/types'

export const authService = {
  async register(data: RegisterFormData): Promise<AuthResponse> {
    const res = await api.post('/api/auth/register', data)
    return res.data.data as AuthResponse
  },

  async login(data: LoginFormData): Promise<AuthResponse> {
    const res = await api.post('/api/auth/login', data)
    return res.data.data as AuthResponse
  },

  async logout(refreshToken: string): Promise<void> {
    await api.post('/api/auth/logout', { refresh: refreshToken })
  },

  async me(): Promise<User> {
    const res = await api.get('/api/auth/me')
    return res.data.data as User
  },
}

import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'
import type { User } from '@/types'
import { queryClient } from '@/queryClient'

interface AuthState {
  user: User | null
  accessToken: string | null
  refreshToken: string | null
  isAuthenticated: boolean

  // Actions
  setAuth: (user: User, accessToken: string, refreshToken: string) => void
  setAccessToken: (token: string) => void
  updateUser: (user: User) => void
  logout: () => void
}

// Clear any residual localStorage auth from older persistent sessions
try {
  localStorage.removeItem('qaip-auth')
} catch {}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,

      setAuth: (user, accessToken, refreshToken) => {
        // Clear all cached query data so the newly logged-in account gets fresh isolated data
        queryClient.clear()
        set({ user, accessToken, refreshToken, isAuthenticated: true })
      },

      setAccessToken: (token) =>
        set({ accessToken: token }),

      updateUser: (user) =>
        set({ user }),

      logout: () => {
        try {
          sessionStorage.removeItem('qaip-auth')
          localStorage.removeItem('qaip-auth')
        } catch {}
        // Instantly purge all query cache in memory
        queryClient.clear()
        set({ user: null, accessToken: null, refreshToken: null, isAuthenticated: false })
      },
    }),
    {
      name: 'qaip-auth',
      storage: createJSONStorage(() => sessionStorage),
      // Only persist tokens and user in session storage — erased on tab/browser close
      partialize: (state) => ({
        user: state.user,
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        isAuthenticated: state.isAuthenticated,
      }),
    },
  ),
)

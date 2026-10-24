import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export type Theme = 'dark' | 'light'

interface ThemeState {
  theme: Theme
  toggleTheme: () => void
  setTheme: (theme: Theme) => void
}

function applyThemeToDocument(theme: Theme) {
  if (typeof document !== 'undefined') {
    if (theme === 'light') {
      document.documentElement.classList.add('light-theme')
    } else {
      document.documentElement.classList.remove('light-theme')
    }
  }
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set, get) => ({
      theme: 'dark',
      toggleTheme: () => {
        const next = get().theme === 'dark' ? 'light' : 'dark'
        applyThemeToDocument(next)
        set({ theme: next })
      },
      setTheme: (theme: Theme) => {
        applyThemeToDocument(theme)
        set({ theme })
      },
    }),
    {
      name: 'qaip-theme',
      onRehydrateStorage: () => (state) => {
        if (state) {
          applyThemeToDocument(state.theme)
        }
      },
    }
  )
)

// Apply immediately on load
if (typeof window !== 'undefined') {
  try {
    const saved = localStorage.getItem('qaip-theme')
    if (saved) {
      const parsed = JSON.parse(saved)
      if (parsed?.state?.theme === 'light') {
        document.documentElement.classList.add('light-theme')
      }
    }
  } catch {}
}
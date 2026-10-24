import { useEffect } from 'react'
import { useThemeStore } from '@/store/themeStore'
import type { Theme } from '@/store/themeStore'

export function useTheme() {
  const theme = useThemeStore((s) => s.theme)
  const toggleTheme = useThemeStore((s) => s.toggleTheme)
  const setTheme = useThemeStore((s) => s.setTheme)

  useEffect(() => {
    if (theme === 'light') {
      document.documentElement.classList.add('light-theme')
    } else {
      document.documentElement.classList.remove('light-theme')
    }
  }, [theme])

  return { theme, toggleTheme, setTheme }
}

export type { Theme }

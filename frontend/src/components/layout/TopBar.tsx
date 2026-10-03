import { Bell, Menu } from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import { ThemeToggle } from '@/components/ui/ThemeToggle'

interface TopBarProps {
  onToggleSidebar: () => void
  title?: string
}

export function TopBar({ onToggleSidebar, title }: TopBarProps) {
  const user = useAuthStore((s) => s.user)

  const initials = user?.full_name
    ? user.full_name.split(' ').map((n) => n[0]).join('').toUpperCase().slice(0, 2)
    : 'S'

  return (
    <header className="h-16 bg-surface-card border-b border-surface-border flex items-center justify-between px-6 sticky top-0 z-10">
      {/* Left */}
      <div className="flex items-center gap-4">
        <button
          onClick={onToggleSidebar}
          className="p-2 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-surface-hover transition-colors"
          aria-label="Toggle sidebar"
        >
          <Menu className="h-5 w-5" />
        </button>
        {title && (
          <h1 className="text-lg font-semibold text-slate-100 hidden sm:block">{title}</h1>
        )}
      </div>

      {/* Right */}
      <div className="flex items-center gap-3">
        <ThemeToggle />
        <button className="p-2 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-surface-hover transition-colors relative">
          <Bell className="h-5 w-5" />
        </button>
        <div className="flex items-center gap-2 pl-3 border-l border-surface-border">
          <div className="h-8 w-8 rounded-full bg-brand-600 flex items-center justify-center text-xs font-bold text-white flex-shrink-0">
            {initials}
          </div>
          <div className="hidden md:block min-w-0">
            <p className="text-sm font-medium text-slate-200 truncate max-w-[140px]">
              {user?.full_name ?? 'Student'}
            </p>
            <p className="text-xs text-slate-500 truncate max-w-[140px]">{user?.email ?? ''}</p>
          </div>
        </div>
      </div>
    </header>
  )
}

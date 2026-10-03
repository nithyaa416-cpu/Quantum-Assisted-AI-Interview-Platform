import { NavLink, useNavigate } from 'react-router-dom'
import { clsx } from 'clsx'
import {
  LayoutDashboard, User, FileText, Brain,
  LogOut, Zap, ChevronRight, Target, MessageSquare, History, Code2,
} from 'lucide-react'
import toast from 'react-hot-toast'
import { useAuthStore } from '@/store/authStore'
import { authService } from '@/services/authService'

const nav = [
  { to: '/dashboard',     icon: LayoutDashboard, label: 'Dashboard'    },
  { to: '/interview/new', icon: MessageSquare,   label: 'Interview'    },
  { to: '/coding-practice', icon: Code2, label: 'Coding Practice' },
  { to: '/sessions',      icon: History,         label: 'Sessions'     },
  { to: '/profile',       icon: User,            label: 'My Profile'   },
  { to: '/resumes',       icon: FileText,        label: 'Resumes'      },
  { to: '/preparation',   icon: Brain,           label: 'Prep Plan'    },
]

interface SidebarProps {
  collapsed?: boolean
}

export function Sidebar({ collapsed = false }: SidebarProps) {
  const { user, refreshToken, logout } = useAuthStore()
  const navigate = useNavigate()

  const handleLogout = async () => {
    try {
      if (refreshToken) await authService.logout(refreshToken)
    } catch {
      // token may already be expired — still clear local state
    }
    logout()
    toast.success('Logged out')
    navigate('/login')
  }

  return (
    <aside
      className={clsx(
        'flex flex-col bg-surface-card border-r border-surface-border h-screen sticky top-0 transition-all duration-300',
        collapsed ? 'w-16' : 'w-64',
      )}
    >
      {/* Logo */}
      <div className="flex items-center gap-3 px-5 py-5 border-b border-surface-border">
        <div className="flex-shrink-0 h-8 w-8 rounded-lg bg-brand-600 flex items-center justify-center">
          <Zap className="h-4 w-4 text-white" />
        </div>
        {!collapsed && (
          <div className="min-w-0">
            <p className="text-sm font-bold text-slate-100 truncate">QAIP</p>
            <p className="text-xs text-slate-500 truncate">Interview Ready</p>
          </div>
        )}
      </div>

      {/* Nav */}
      <nav className="flex-1 py-4 space-y-1 px-2 overflow-y-auto">
        {nav.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              clsx(
                'flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150 group',
                isActive
                  ? 'bg-brand-600/20 text-brand-400'
                  : 'text-slate-400 hover:text-slate-100 hover:bg-surface-hover',
              )
            }
          >
            {({ isActive }) => (
              <>
                <Icon className={clsx('h-4 w-4 flex-shrink-0', isActive && 'text-brand-400')} />
                {!collapsed && <span className="flex-1 truncate">{label}</span>}
                {!collapsed && isActive && <ChevronRight className="h-3 w-3 opacity-60" />}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* User info + logout */}
      <div className="border-t border-surface-border p-3">
        {!collapsed && user && (
          <div className="px-2 py-2 mb-2 min-w-0">
            <p className="text-sm font-medium text-slate-200 truncate">{user.full_name}</p>
            <p className="text-xs text-slate-500 truncate">{user.email}</p>
          </div>
        )}
        <button
          onClick={handleLogout}
          className="flex items-center gap-3 w-full px-3 py-2.5 rounded-xl text-sm font-medium text-slate-400 hover:text-red-400 hover:bg-red-500/10 transition-all duration-150"
        >
          <LogOut className="h-4 w-4 flex-shrink-0" />
          {!collapsed && 'Logout'}
        </button>
      </div>
    </aside>
  )
}

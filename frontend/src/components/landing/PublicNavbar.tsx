/**
 * PublicNavbar — sticky navigation bar for the landing page.
 *
 * Features:
 * - Smooth-scroll section links (Home, Features, How It Works, About, Contact)
 * - Login → existing /login route
 * - Get Started → existing /register route
 * - Responsive mobile menu with working toggle
 * - Respects existing dark/light theme system via ThemeToggle
 * - Subtle blur background effect when scrolled
 */
import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Zap, Menu, X, ChevronRight } from 'lucide-react'
import { clsx } from 'clsx'
import { ThemeToggle } from '@/components/ui/ThemeToggle'

const NAV_LINKS = [
  { label: 'Home',        href: '#home' },
  { label: 'Features',    href: '#features' },
  { label: 'How It Works', href: '#how-it-works' },
  { label: 'About',        href: '#about' },
  { label: 'Contact',      href: '#contact' },
]

export function PublicNavbar() {
  const [scrolled, setScrolled]   = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 12)
    window.addEventListener('scroll', onScroll, { passive: true })
    onScroll()
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  const handleNavClick = (e: React.MouseEvent, href: string) => {
    e.preventDefault()
    setMobileOpen(false)
    const el = document.querySelector(href)
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  return (
    <nav className={clsx(
      'fixed top-0 left-0 right-0 z-50 transition-all duration-300',
      scrolled
        ? 'bg-surface/80 backdrop-blur-xl border-b border-surface-border'
        : 'bg-transparent',
    )}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <a
            href="#home"
            onClick={(e) => handleNavClick(e, '#home')}
            className="flex items-center gap-2.5 group"
          >
            <div className="h-8 w-8 rounded-lg bg-brand-600 flex items-center justify-center shadow-lg shadow-brand-600/30 transition-transform group-hover:scale-110">
              <Zap className="h-4 w-4 text-white" />
            </div>
            <span className="text-lg font-bold text-slate-100">QAIP</span>
          </a>

          {/* Desktop nav links */}
          <div className="hidden md:flex items-center gap-1">
            {NAV_LINKS.map((link) => (
              <a
                key={link.href}
                href={link.href}
                onClick={(e) => handleNavClick(e, link.href)}
                className="px-3 py-2 text-sm font-medium text-slate-400 hover:text-slate-100 hover:bg-surface-hover rounded-lg transition-colors"
              >
                {link.label}
              </a>
            ))}
          </div>

          {/* Desktop actions */}
          <div className="hidden md:flex items-center gap-3">
            <ThemeToggle />
            <button
              onClick={() => navigate('/login')}
              className="px-4 py-2 text-sm font-medium text-slate-300 hover:text-slate-100 transition-colors"
            >
              Login
            </button>
            <button
              onClick={() => navigate('/register')}
              className="px-4 py-2 text-sm font-semibold text-white bg-brand-600 hover:bg-brand-700 rounded-xl transition-all duration-200 flex items-center gap-1.5 shadow-lg shadow-brand-600/25"
            >
              Get Started
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>

          {/* Mobile menu button */}
          <div className="flex md:hidden items-center gap-2">
            <ThemeToggle />
            <button
              onClick={() => setMobileOpen(v => !v)}
              className="p-2 rounded-lg text-slate-300 hover:text-slate-100 hover:bg-surface-hover transition-colors"
              aria-label="Toggle menu"
            >
              {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>
          </div>
        </div>

        {/* Mobile menu */}
        {mobileOpen && (
          <div className="md:hidden pb-4 pt-2 border-t border-surface-border space-y-1 animate-fade-in">
            {NAV_LINKS.map((link) => (
              <a
                key={link.href}
                href={link.href}
                onClick={(e) => handleNavClick(e, link.href)}
                className="block px-3 py-2.5 text-sm font-medium text-slate-400 hover:text-slate-100 hover:bg-surface-hover rounded-lg transition-colors"
              >
                {link.label}
              </a>
            ))}
            <div className="pt-2 flex flex-col gap-2">
              <button
                onClick={() => { setMobileOpen(false); navigate('/login') }}
                className="px-4 py-2.5 text-sm font-medium text-slate-300 hover:text-slate-100 hover:bg-surface-hover rounded-xl transition-colors text-left"
              >
                Login
              </button>
              <button
                onClick={() => { setMobileOpen(false); navigate('/register') }}
                className="px-4 py-2.5 text-sm font-semibold text-white bg-brand-600 hover:bg-brand-700 rounded-xl transition-colors flex items-center justify-center gap-1.5"
              >
                Get Started
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        )}
      </div>
    </nav>
  )
}

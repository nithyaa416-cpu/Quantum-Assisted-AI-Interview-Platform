/**
 * PublicFooter — footer for the landing page.
 *
 * Includes QAIP branding, section navigation links, auth links,
 * and a dynamic copyright year. Does not include fake GitHub/team
 * links or privacy/terms links to non-existent pages.
 */
import { Link } from 'react-router-dom'
import { Zap } from 'lucide-react'

const FOOTER_SECTIONS = [
  { label: 'Home',        href: '#home' },
  { label: 'Features',    href: '#features' },
  { label: 'How It Works', href: '#how-it-works' },
  { label: 'About',        href: '#about' },
  { label: 'Contact',      href: '#contact' },
]

export function PublicFooter() {
  const year = new Date().getFullYear()

  const handleNavClick = (e: React.MouseEvent, href: string) => {
    e.preventDefault()
    const el = document.querySelector(href)
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  return (
    <footer className="bg-surface border-t border-surface-border">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Branding */}
          <div className="space-y-3">
            <div className="flex items-center gap-2.5">
              <div className="h-8 w-8 rounded-lg bg-brand-600 flex items-center justify-center">
                <Zap className="h-4 w-4 text-white" />
              </div>
              <span className="text-lg font-bold text-slate-100">QAIP</span>
            </div>
            <p className="text-sm text-slate-400 max-w-xs leading-relaxed">
              Quantum-Assisted AI Interview Intelligence and Placement Readiness Platform —
              personalized mock interviews, coding assessments, and actionable feedback for students.
            </p>
          </div>

          {/* Navigation links */}
          <div>
            <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-3">
              Explore
            </h4>
            <ul className="space-y-2">
              {FOOTER_SECTIONS.map((link) => (
                <li key={link.href}>
                  <a
                    href={link.href}
                    onClick={(e) => handleNavClick(e, link.href)}
                    className="text-sm text-slate-400 hover:text-brand-400 transition-colors"
                  >
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          {/* Auth links */}
          <div>
            <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-3">
              Get Started
            </h4>
            <ul className="space-y-2">
              <li>
                <Link to="/login" className="text-sm text-slate-400 hover:text-brand-400 transition-colors">
                  Login
                </Link>
              </li>
              <li>
                <Link to="/register" className="text-sm text-slate-400 hover:text-brand-400 transition-colors">
                  Create Account
                </Link>
              </li>
            </ul>
          </div>
        </div>

        {/* Copyright */}
        <div className="mt-10 pt-6 border-t border-surface-border">
          <p className="text-xs text-slate-500 text-center">
            © {year} QAIP — Quantum-Assisted AI Interview Intelligence Platform. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  )
}

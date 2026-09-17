import { ReactNode } from 'react'
import { Zap } from 'lucide-react'

interface AuthShellProps {
  title: string
  subtitle: string
  children: ReactNode
}

/**
 * Shared full-page wrapper for Login and Register.
 * Left panel: branding + feature highlights.
 * Right panel: form content.
 */
export function AuthShell({ title, subtitle, children }: AuthShellProps) {
  return (
    <div className="min-h-screen bg-surface flex">
      {/* ── Left branding panel ── */}
      <div className="hidden lg:flex lg:w-[480px] flex-col justify-between bg-surface-card border-r border-surface-border p-12">
        {/* Logo */}
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-brand-600 flex items-center justify-center">
            <Zap className="h-5 w-5 text-white" />
          </div>
          <div>
            <p className="text-base font-bold text-slate-100">QAIP</p>
            <p className="text-xs text-slate-500">Quantum AI Interview Platform</p>
          </div>
        </div>

        {/* Feature highlights */}
        <div className="space-y-8">
          <div>
            <h2 className="text-3xl font-bold text-slate-100 leading-tight">
              Ace your placement<br />
              <span className="text-brand-400">interviews</span> with AI.
            </h2>
            <p className="mt-3 text-slate-400 text-sm leading-relaxed">
              Personalised AI interviews, live coding assessments, and quantum-optimised
              preparation paths — all tailored to your resume and target role.
            </p>
          </div>

          <div className="space-y-4">
            {[
              { emoji: '🤖', title: 'Adaptive AI Interviewer', desc: 'Dynamic questions based on your responses' },
              { emoji: '💻', title: 'Live Coding Rounds',      desc: 'Real editor with execution and AI review' },
              { emoji: '⚛️', title: 'Quantum Prep Planner',    desc: 'QAOA-optimised study roadmap just for you' },
              { emoji: '📊', title: 'Detailed Reports',        desc: 'Scores, gaps, and actionable feedback' },
            ].map((f) => (
              <div key={f.title} className="flex items-start gap-3">
                <span className="text-xl">{f.emoji}</span>
                <div>
                  <p className="text-sm font-semibold text-slate-200">{f.title}</p>
                  <p className="text-xs text-slate-500">{f.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <p className="text-xs text-slate-600">
          © 2025 QAIP · Built for placement preparation
        </p>
      </div>

      {/* ── Right form panel ── */}
      <div className="flex-1 flex items-center justify-center p-6 sm:p-10">
        <div className="w-full max-w-md animate-slide-up">
          {/* Mobile logo */}
          <div className="flex items-center gap-2 mb-8 lg:hidden">
            <div className="h-8 w-8 rounded-lg bg-brand-600 flex items-center justify-center">
              <Zap className="h-4 w-4 text-white" />
            </div>
            <span className="font-bold text-slate-100">QAIP</span>
          </div>

          <h1 className="text-2xl font-bold text-slate-100">{title}</h1>
          <p className="text-slate-400 text-sm mt-1 mb-8">{subtitle}</p>

          {children}
        </div>
      </div>
    </div>
  )
}

import { clsx } from 'clsx'
import { CheckCircle2, Circle, Loader2 } from 'lucide-react'

const PHASES = [
  { id: 'warmup',    label: 'Warm-Up',   emoji: '👋' },
  { id: 'technical', label: 'Technical', emoji: '💻' },
  { id: 'project',   label: 'Projects',  emoji: '🛠️' },
  { id: 'hr',        label: 'HR',        emoji: '🤝' },
  { id: 'closing',   label: 'Closing',   emoji: '✅' },
]

interface PhaseIndicatorProps {
  currentPhase: string
  phaseProgress: Record<string, { asked: number; total: number }>
}

export function PhaseIndicator({ currentPhase, phaseProgress }: PhaseIndicatorProps) {
  const currentIdx = PHASES.findIndex(p => p.id === currentPhase)

  return (
    <div className="flex items-center gap-1 overflow-x-auto pb-1">
      {PHASES.map((phase, idx) => {
        const prog  = phaseProgress[phase.id]
        const done  = prog && prog.asked >= prog.total && prog.total > 0
        const active = phase.id === currentPhase
        const past  = idx < currentIdx

        return (
          <div key={phase.id} className="flex items-center gap-1 flex-shrink-0">
            <div className={clsx(
              'flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-all duration-300',
              active  ? 'bg-brand-600/20 text-brand-300 border border-brand-500/40' :
              done    ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' :
              past    ? 'bg-slate-500/10 text-slate-500 border border-slate-600/20' :
                        'bg-surface text-slate-600 border border-surface-border',
            )}>
              {done   ? <CheckCircle2 className="h-3 w-3" /> :
               active ? <Loader2 className="h-3 w-3 animate-spin" /> :
                        <Circle className="h-3 w-3" />}
              <span className="hidden sm:inline">{phase.label}</span>
              <span className="sm:hidden">{phase.emoji}</span>
              {prog && prog.total > 0 && (
                <span className="text-xs opacity-70">
                  {prog.asked}/{prog.total}
                </span>
              )}
            </div>
            {idx < PHASES.length - 1 && (
              <div className={clsx(
                'h-px w-4 flex-shrink-0 transition-colors',
                past || done ? 'bg-emerald-500/40' : 'bg-surface-border',
              )} />
            )}
          </div>
        )
      })}
    </div>
  )
}

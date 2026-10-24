import { useState, useEffect, useRef } from 'react'
import { Clock } from 'lucide-react'
import { clsx } from 'clsx'

interface InterviewTimerProps {
  startedAt: string | null
  isActive: boolean
  /** Optional per-question timer in seconds */
  questionTimer?: number | null
  /** Optional targeted session duration in seconds (e.g. 1200, 1500, 1800) */
  durationSeconds?: number | null
}

function formatDuration(secs: number): string {
  const m = Math.floor(secs / 60).toString().padStart(2, '0')
  const s = (secs % 60).toString().padStart(2, '0')
  return `${m}:${s}`
}

/** Overall session elapsed timer */
export function SessionTimer({ startedAt, isActive, durationSeconds }: InterviewTimerProps) {
  const [elapsed, setElapsed] = useState(0)

  useEffect(() => {
    if (!isActive || !startedAt) return
    const base = Math.max(0, Math.floor((Date.now() - new Date(startedAt).getTime()) / 1000))
    setElapsed(base)
    const id = setInterval(() => setElapsed(v => v + 1), 1000)
    return () => clearInterval(id)
  }, [isActive, startedAt])

  if (durationSeconds && durationSeconds > 0) {
    const remaining = Math.max(0, durationSeconds - elapsed)
    const pct = Math.min(100, Math.round((elapsed / durationSeconds) * 100))
    const isOvertime = elapsed > durationSeconds

    return (
      <div
        className="flex items-center gap-2 px-3 py-1 rounded-full bg-slate-800/90 border border-slate-700/80 text-xs shadow-sm"
        title={`Session duration: ${formatDuration(elapsed)} of ${formatDuration(durationSeconds)} (Target: ${Math.round(durationSeconds / 60)} min)`}
      >
        <Clock className={clsx('h-3.5 w-3.5', isOvertime ? 'text-amber-400 animate-pulse' : 'text-brand-400')} />
        <span className="font-mono text-slate-200 font-semibold">{formatDuration(elapsed)}</span>
        <span className="text-slate-500">/</span>
        <span className="font-mono text-slate-400">{formatDuration(durationSeconds)}</span>
        <div className="w-12 h-1.5 bg-slate-700/80 rounded-full overflow-hidden ml-1 hidden md:block">
          <div
            className={clsx(
              'h-full rounded-full transition-all duration-1000',
              isOvertime ? 'bg-amber-400' : 'bg-brand-500'
            )}
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>
    )
  }

  return (
    <div className="flex items-center gap-1.5 text-slate-400 text-sm">
      <Clock className="h-4 w-4" />
      <span className="font-mono text-slate-300">{formatDuration(elapsed)}</span>
    </div>
  )
}

/** Per-question countdown timer */
export function QuestionTimer({ seconds, onExpire }: { seconds: number; onExpire?: () => void }) {
  const [remaining, setRemaining] = useState(seconds)
  const expiredRef = useRef(false)

  useEffect(() => {
    setRemaining(seconds)
    expiredRef.current = false
  }, [seconds])

  useEffect(() => {
    if (remaining <= 0) {
      if (!expiredRef.current) {
        expiredRef.current = true
        onExpire?.()
      }
      return
    }
    const id = setInterval(() => setRemaining(v => v - 1), 1000)
    return () => clearInterval(id)
  }, [remaining, onExpire])

  const pct     = remaining / seconds
  const warning = pct < 0.3
  const danger  = pct < 0.15

  return (
    <div className="flex items-center gap-2">
      <Clock className={clsx('h-3.5 w-3.5', danger ? 'text-red-400' : warning ? 'text-amber-400' : 'text-slate-400')} />
      <span className={clsx(
        'font-mono text-sm font-medium tabular-nums',
        danger  ? 'text-red-400' :
        warning ? 'text-amber-400' :
                  'text-slate-300',
      )}>
        {formatDuration(remaining)}
      </span>
      <div className="flex-1 h-1 bg-surface-border rounded-full overflow-hidden max-w-[80px]">
        <div
          className={clsx(
            'h-full rounded-full transition-all duration-1000',
            danger  ? 'bg-red-500' :
            warning ? 'bg-amber-500' :
                      'bg-brand-500',
          )}
          style={{ width: `${pct * 100}%` }}
        />
      </div>
    </div>
  )
}

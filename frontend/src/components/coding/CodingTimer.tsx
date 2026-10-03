/**
 * CodingTimer — countdown timer for the coding interview.
 *
 * - Starts automatically on mount.
 * - Stable across re-renders (uses useRef for the interval).
 * - Does NOT reset when language changes.
 * - Calls onExpire() once when the timer hits 00:00.
 * - Exposes isExpired so parent can disable Run/Submit.
 */
import { useState, useEffect, useRef } from 'react'
import { Clock, AlertTriangle } from 'lucide-react'
import { clsx } from 'clsx'

interface CodingTimerProps {
  /** Duration in seconds. Default: 1800 (30 minutes). */
  durationSeconds?: number
  onExpire?: () => void
}

function fmt(secs: number): string {
  const m = Math.floor(secs / 60).toString().padStart(2, '0')
  const s = (secs % 60).toString().padStart(2, '0')
  return `${m}:${s}`
}

export function CodingTimer({ durationSeconds = 1800, onExpire }: CodingTimerProps) {
  const [remaining, setRemaining] = useState(durationSeconds)
  const expiredRef  = useRef(false)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    intervalRef.current = setInterval(() => {
      setRemaining((prev) => {
        if (prev <= 1) {
          clearInterval(intervalRef.current!)
          if (!expiredRef.current) {
            expiredRef.current = true
            onExpire?.()
          }
          return 0
        }
        return prev - 1
      })
    }, 1000)

    return () => clearInterval(intervalRef.current!)
  }, []) // intentionally empty — starts once on mount

  const isExpired = remaining === 0
  const pct       = remaining / durationSeconds
  const warning   = pct < 0.2 && !isExpired
  const danger    = pct < 0.1 || isExpired

  return (
    <div className={clsx(
      'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-mono font-semibold transition-colors',
      isExpired ? 'bg-red-500/20 text-red-400 border border-red-500/30' :
      danger    ? 'bg-red-500/10 text-red-400' :
      warning   ? 'bg-amber-500/10 text-amber-400' :
                  'bg-surface-hover text-slate-300',
    )}>
      {isExpired
        ? <AlertTriangle className="h-4 w-4" />
        : <Clock className={clsx('h-4 w-4', danger ? 'animate-pulse' : '')} />
      }
      {isExpired ? 'Time Up!' : fmt(remaining)}
    </div>
  )
}

/** Hook version — use this to get the expired state in parent components */
export function useCodingTimer(durationSeconds = 1800) {
  const [remaining, setRemaining] = useState(durationSeconds)
  const expiredRef  = useRef(false)

  useEffect(() => {
    const id = setInterval(() => {
      setRemaining((prev) => {
        if (prev <= 1) {
          clearInterval(id)
          expiredRef.current = true
          return 0
        }
        return prev - 1
      })
    }, 1000)
    return () => clearInterval(id)
  }, [])

  return {
    remaining,
    isExpired: remaining === 0,
    formatted: fmt(remaining),
  }
}

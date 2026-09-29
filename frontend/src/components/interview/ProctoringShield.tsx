import { useEffect, useState, useCallback } from 'react'
import { AlertTriangle, Maximize2, ShieldAlert, Eye } from 'lucide-react'
import { Button } from '@/components/ui/Button'

interface ProctoringShieldProps {
  onViolation?: (count: number, reason: string) => void
  enabled?: boolean
}

export function ProctoringShield({ onViolation, enabled = true }: ProctoringShieldProps) {
  const [violations, setViolations] = useState<number>(0)
  const [warningActive, setWarningActive] = useState(false)
  const [warningReason, setWarningReason] = useState('')
  const [isFullscreen, setIsFullscreen] = useState(Boolean(document.fullscreenElement))

  const triggerViolation = useCallback((reason: string) => {
    if (!enabled) return
    setViolations((prev) => {
      const next = prev + 1
      onViolation?.(next, reason)
      return next
    })
    setWarningReason(reason)
    setWarningActive(true)
  }, [enabled, onViolation])

  const requestFullscreen = useCallback(async () => {
    try {
      if (!document.fullscreenElement) {
        await document.documentElement.requestFullscreen()
        setIsFullscreen(true)
      }
      setWarningActive(false)
    } catch (err) {
      console.warn('Fullscreen request failed:', err)
      setWarningActive(false)
    }
  }, [])

  useEffect(() => {
    if (!enabled) return

    // Auto-enter fullscreen on mount
    requestFullscreen()

    // 1. Detect tab switching / minimizing
    const handleVisibilityChange = () => {
      if (document.hidden) {
        triggerViolation('Tab switched or browser minimized')
      }
    }

    // 2. Detect window blur (clicking outside the interview window)
    const handleWindowBlur = () => {
      // Slight delay to avoid false positives on system dialogs
      setTimeout(() => {
        if (!document.hasFocus()) {
          triggerViolation('Window focus lost / switched to another application')
        }
      }, 300)
    }

    // 3. Detect exiting fullscreen
    const handleFullscreenChange = () => {
      const isFull = Boolean(document.fullscreenElement)
      setIsFullscreen(isFull)
      if (!isFull) {
        triggerViolation('Exited full screen mode')
      }
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)
    window.addEventListener('blur', handleWindowBlur)
    document.addEventListener('fullscreenchange', handleFullscreenChange)

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange)
      window.removeEventListener('blur', handleWindowBlur)
      document.removeEventListener('fullscreenchange', handleFullscreenChange)
    }
  }, [enabled, requestFullscreen, triggerViolation])

  if (!warningActive) {
    return (
      <div className="fixed top-4 left-4 z-40 flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-900/80 backdrop-blur-md border border-slate-700/60 text-xs text-slate-300 shadow-lg">
        <span className="relative flex h-2 w-2">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
          <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
        </span>
        <span className="font-medium text-slate-200">Strict Proctoring Active</span>
        {violations > 0 && (
          <span className="px-1.5 py-0.2 rounded bg-amber-500/20 text-amber-300 font-semibold text-[10px]">
            {violations} strike{violations > 1 ? 's' : ''}
          </span>
        )}
      </div>
    )
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/90 backdrop-blur-lg animate-fade-in">
      <div className="max-w-md w-full bg-slate-900 border border-red-500/40 rounded-2xl p-6 shadow-2xl text-center space-y-5">
        <div className="mx-auto w-16 h-16 rounded-2xl bg-red-500/10 border border-red-500/20 flex items-center justify-center text-red-400 animate-bounce">
          <ShieldAlert className="h-8 w-8" />
        </div>

        <div className="space-y-2">
          <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-red-500/10 border border-red-500/20 text-red-400 text-xs font-semibold uppercase tracking-wider">
            <AlertTriangle className="h-3.5 w-3.5" /> Proctoring Alert &bull; Strike {violations} of 3
          </div>
          <h2 className="text-xl font-bold text-slate-100">
            Interview Focus Interrupted
          </h2>
          <p className="text-xs text-slate-300 leading-relaxed">
            {warningReason || 'Tab switching and window minimization are strictly prohibited during the live interview.'}
          </p>
          <p className="text-[11px] text-slate-400">
            Please keep your browser in full screen and focus on the interview meeting room.
          </p>
        </div>

        <div className="pt-2">
          <Button
            onClick={requestFullscreen}
            className="w-full bg-red-600 hover:bg-red-500 text-white font-semibold py-2.5"
            icon={<Maximize2 className="h-4 w-4" />}
          >
            Return to Full Screen &amp; Resume
          </Button>
        </div>
      </div>
    </div>
  )
}

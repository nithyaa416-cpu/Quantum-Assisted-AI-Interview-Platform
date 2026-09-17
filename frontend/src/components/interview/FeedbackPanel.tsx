import { clsx } from 'clsx'
import { CheckCircle2, AlertCircle, TrendingUp, ChevronRight } from 'lucide-react'

interface FeedbackPanelProps {
  score: number           // 0–1
  feedback: string
  onContinue: () => void
  isLastQuestion?: boolean
  isLoading?: boolean
}

function ScoreBar({ score }: { score: number }) {
  const pct = Math.round(score * 100)
  const color = score >= 0.65 ? 'bg-emerald-500' : score >= 0.35 ? 'bg-amber-500' : 'bg-red-500'
  const label = score >= 0.65 ? 'Strong' : score >= 0.35 ? 'Good' : 'Needs Work'
  const textColor = score >= 0.65 ? 'text-emerald-400' : score >= 0.35 ? 'text-amber-400' : 'text-red-400'

  return (
    <div className="flex items-center gap-3">
      <div className="flex-1 h-2 bg-surface-border rounded-full overflow-hidden">
        <div
          className={clsx('h-full rounded-full transition-all duration-700', color)}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className={clsx('text-sm font-semibold tabular-nums min-w-[80px] text-right', textColor)}>
        {pct}% · {label}
      </span>
    </div>
  )
}

export function FeedbackPanel({ score, feedback, onContinue, isLastQuestion, isLoading }: FeedbackPanelProps) {
  const isGood = score >= 0.65
  const isWeak = score < 0.35

  return (
    <div className={clsx(
      'card p-5 space-y-4 border-l-4 animate-slide-up',
      isGood ? 'border-l-emerald-500' : isWeak ? 'border-l-red-500' : 'border-l-amber-500',
    )}>
      {/* Score header */}
      <div className="flex items-center gap-2">
        {isGood
          ? <CheckCircle2 className="h-5 w-5 text-emerald-400 flex-shrink-0" />
          : isWeak
          ? <AlertCircle className="h-5 w-5 text-red-400 flex-shrink-0" />
          : <TrendingUp className="h-5 w-5 text-amber-400 flex-shrink-0" />
        }
        <h3 className="text-sm font-semibold text-slate-200">AI Feedback</h3>
      </div>

      {/* Score bar */}
      <ScoreBar score={score} />

      {/* Feedback text */}
      <p className="text-sm text-slate-300 leading-relaxed">{feedback}</p>

      {/* Continue button */}
      <button
        onClick={onContinue}
        disabled={isLoading}
        className={clsx(
          'w-full flex items-center justify-center gap-2 py-3 rounded-xl text-sm font-semibold transition-all duration-200',
          isLoading
            ? 'bg-surface-hover text-slate-500 cursor-not-allowed'
            : isLastQuestion
            ? 'bg-emerald-600 hover:bg-emerald-700 text-white'
            : 'bg-brand-600 hover:bg-brand-700 text-white',
        )}
      >
        {isLoading ? (
          <span className="flex items-center gap-2">
            <span className="h-4 w-4 border-2 border-slate-500 border-t-transparent rounded-full animate-spin" />
            Loading next question…
          </span>
        ) : isLastQuestion ? (
          <>✅ Finish Interview</>
        ) : (
          <>Next Question <ChevronRight className="h-4 w-4" /></>
        )}
      </button>
    </div>
  )
}

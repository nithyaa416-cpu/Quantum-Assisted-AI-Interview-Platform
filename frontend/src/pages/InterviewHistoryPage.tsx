import { useParams, useNavigate, Link } from 'react-router-dom'
import {
  ArrowLeft, CheckCircle2, XCircle, Clock,
  MessageSquare, TrendingUp, ChevronDown, ChevronUp,
} from 'lucide-react'
import { useState } from 'react'
import { clsx } from 'clsx'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Spinner } from '@/components/ui/Spinner'
import { PhaseIndicator } from '@/components/interview/PhaseIndicator'
import { SessionTimer } from '@/components/interview/InterviewTimer'
import { useInterviewSession } from '@/hooks/useInterview'
import type { InterviewTurn } from '@/types'

const PHASE_COLORS: Record<string, string> = {
  warmup:    'bg-amber-500/10 text-amber-300 border-amber-500/20',
  technical: 'bg-blue-500/10 text-blue-300 border-blue-500/20',
  project:   'bg-violet-500/10 text-violet-300 border-violet-500/20',
  hr:        'bg-green-500/10 text-green-300 border-green-500/20',
  closing:   'bg-slate-500/10 text-slate-300 border-slate-500/20',
}

function TurnCard({ turn, index }: { turn: InterviewTurn; index: number }) {
  const [expanded, setExpanded] = useState(index === 0)
  const score = turn.score ?? 0
  const isGood = score >= 0.65
  const isWeak = score < 0.35 && turn.answered

  return (
    <div className={clsx(
      'card overflow-hidden transition-all duration-200',
      turn.is_follow_up && 'ml-6 border-l-2 border-l-brand-500/30',
    )}>
      {/* Turn header */}
      <button
        onClick={() => setExpanded(v => !v)}
        className="w-full flex items-center gap-3 p-4 text-left hover:bg-surface-hover transition-colors"
      >
        <div className="flex-shrink-0 h-7 w-7 rounded-full bg-surface-hover flex items-center justify-center text-xs font-bold text-slate-400">
          {turn.turn_number}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className={clsx(
              'inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border',
              PHASE_COLORS[turn.phase] ?? PHASE_COLORS.technical,
            )}>
              {turn.phase}
            </span>
            {turn.topic && (
              <span className="text-xs text-slate-500">{turn.topic}</span>
            )}
            {turn.is_follow_up && (
              <span className="text-xs text-brand-400 bg-brand-400/10 px-1.5 py-0.5 rounded border border-brand-400/20">
                Follow-up
              </span>
            )}
          </div>
          <p className="text-sm text-slate-300 mt-1 truncate">{turn.question}</p>
        </div>

        <div className="flex items-center gap-2 flex-shrink-0">
          {turn.answered ? (
            <span className={clsx(
              'text-xs font-medium tabular-nums',
              isGood ? 'text-emerald-400' : isWeak ? 'text-red-400' : 'text-amber-400',
            )}>
              {Math.round(score * 100)}%
            </span>
          ) : (
            <span className="text-xs text-slate-600">Unanswered</span>
          )}
          {expanded ? <ChevronUp className="h-4 w-4 text-slate-500" /> : <ChevronDown className="h-4 w-4 text-slate-500" />}
        </div>
      </button>

      {/* Expanded content */}
      {expanded && (
        <div className="px-4 pb-4 space-y-3 border-t border-surface-border pt-3">
          {/* Full question */}
          <div>
            <p className="text-xs text-slate-500 font-medium uppercase tracking-wider mb-1.5">Question</p>
            <p className="text-sm text-slate-200 leading-relaxed">{turn.question}</p>
          </div>

          {/* Response */}
          {turn.answered && turn.response ? (
            <div>
              <p className="text-xs text-slate-500 font-medium uppercase tracking-wider mb-1.5">Your Answer</p>
              <p className="text-sm text-slate-300 leading-relaxed whitespace-pre-wrap">{turn.response}</p>
              {turn.response_time_seconds && (
                <p className="text-xs text-slate-600 mt-1 flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {turn.response_time_seconds}s
                </p>
              )}
            </div>
          ) : (
            <div>
              <p className="text-xs text-slate-500 font-medium uppercase tracking-wider mb-1.5">Answer</p>
              <p className="text-sm text-slate-600 italic">Not answered</p>
            </div>
          )}

          {/* AI feedback */}
          {turn.feedback && (
            <div className={clsx(
              'p-3 rounded-xl border',
              isGood
                ? 'bg-emerald-500/5 border-emerald-500/20'
                : isWeak
                ? 'bg-red-500/5 border-red-500/20'
                : 'bg-amber-500/5 border-amber-500/20',
            )}>
              <p className="text-xs font-medium mb-1 flex items-center gap-1.5">
                {isGood
                  ? <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
                  : <TrendingUp className="h-3.5 w-3.5 text-amber-400" />
                }
                <span className={isGood ? 'text-emerald-400' : 'text-amber-400'}>AI Feedback</span>
              </p>
              <p className="text-xs text-slate-400 leading-relaxed">{turn.feedback}</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default function InterviewHistoryPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { data: session, isLoading } = useInterviewSession(id ?? null)

  if (isLoading) return <div className="flex justify-center py-20"><Spinner size="lg" /></div>
  if (!session) return (
    <div className="text-center py-20 text-slate-500">
      Session not found.{' '}
      <Link to="/interview/new" className="text-brand-400">Start a new interview</Link>
    </div>
  )

  const answeredTurns  = session.turns.filter(t => t.answered)
  const avgScore = answeredTurns.length > 0
    ? answeredTurns.reduce((s, t) => s + (t.score ?? 0), 0) / answeredTurns.length
    : 0

  const scoreColor = avgScore >= 0.65 ? 'text-emerald-400' : avgScore >= 0.35 ? 'text-amber-400' : 'text-red-400'

  return (
    <div className="max-w-3xl mx-auto space-y-6 animate-slide-up">
      {/* Back */}
      <button
        onClick={() => navigate('/interview/new')}
        className="flex items-center gap-2 text-slate-400 hover:text-slate-200 text-sm transition-colors"
      >
        <ArrowLeft className="h-4 w-4" />
        New interview
      </button>

      {/* Session summary card */}
      <Card className="p-6">
        <div className="flex flex-col sm:flex-row sm:items-center gap-4">
          <div className="flex-1">
            <div className="flex items-center gap-2 flex-wrap">
              <h1 className="text-xl font-bold text-slate-100 capitalize">
                {session.session_type.replace('_', ' ')} Interview
              </h1>
              <Badge color={session.status === 'completed' ? 'green' : 'indigo'}>
                {session.status}
              </Badge>
            </div>
            {session.target_role && (
              <p className="text-sm text-slate-400 mt-1">{session.target_role}</p>
            )}
            <div className="flex items-center gap-4 mt-2 text-xs text-slate-500">
              <span>{session.turns.length} questions</span>
              <span>{answeredTurns.length} answered</span>
              {session.duration_seconds && (
                <span className="flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {Math.floor(session.duration_seconds / 60)}m {session.duration_seconds % 60}s
                </span>
              )}
            </div>
          </div>
          {answeredTurns.length > 0 && (
            <div className="text-center">
              <p className={clsx('text-3xl font-bold tabular-nums', scoreColor)}>
                {Math.round(avgScore * 100)}%
              </p>
              <p className="text-xs text-slate-500 mt-0.5">Avg Score</p>
            </div>
          )}
        </div>

        <div className="mt-4">
          <PhaseIndicator
            currentPhase={session.current_phase}
            phaseProgress={session.phase_progress}
          />
        </div>
      </Card>

      {/* Turn-by-turn transcript */}
      <div>
        <h2 className="text-base font-semibold text-slate-200 mb-3 flex items-center gap-2">
          <MessageSquare className="h-4 w-4 text-brand-400" />
          Interview Transcript
        </h2>

        {session.turns.length === 0 ? (
          <p className="text-slate-500 text-sm text-center py-8">No questions asked yet.</p>
        ) : (
          <div className="space-y-3">
            {session.turns.map((turn, i) => (
              <TurnCard key={turn.turn_number} turn={turn} index={i} />
            ))}
          </div>
        )}
      </div>

      {/* Footer CTA */}
      <div className="flex flex-col sm:flex-row gap-3 justify-center pt-2">
        <Button
          onClick={() => navigate('/interview/new')}
          icon={<MessageSquare className="h-4 w-4" />}
        >
          Start New Interview
        </Button>
        <Button variant="secondary" onClick={() => navigate('/dashboard')}>
          Back to Dashboard
        </Button>
      </div>
    </div>
  )
}

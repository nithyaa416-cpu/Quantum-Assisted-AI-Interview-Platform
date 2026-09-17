import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { XCircle, Trophy, List } from 'lucide-react'
import toast from 'react-hot-toast'
import { SessionSetup } from '@/components/interview/SessionSetup'
import { PhaseIndicator } from '@/components/interview/PhaseIndicator'
import { QuestionCard } from '@/components/interview/QuestionCard'
import { AnswerArea } from '@/components/interview/AnswerArea'
import { FeedbackPanel } from '@/components/interview/FeedbackPanel'
import { SessionTimer } from '@/components/interview/InterviewTimer'
import { Spinner, PageLoader } from '@/components/ui/Spinner'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import {
  useStartInterview, useInterviewSession,
  useSubmitResponse, useEndInterview,
} from '@/hooks/useInterview'
import type { InterviewQuestion, SubmitResponseResult, StartInterviewPayload } from '@/types'

// ── Active interview conductor ────────────────────────────────────────────────

function ActiveInterview({ sessionId }: { sessionId: string }) {
  const navigate = useNavigate()
  const { data: session, isLoading, refetch } = useInterviewSession(sessionId)
  const { mutateAsync: submitResponse, isPending: isSubmitting } = useSubmitResponse(sessionId)
  const { mutateAsync: endInterview, isPending: isEnding } = useEndInterview(sessionId)

  const [lastFeedback, setLastFeedback] = useState<SubmitResponseResult | null>(null)
  const [showFeedback, setShowFeedback] = useState(false)
  const [isComplete, setIsComplete]     = useState(false)

  // Keep current question in local state for smooth UX
  const [currentQuestion, setCurrentQuestion] = useState<InterviewQuestion | null>(null)

  useEffect(() => {
    if (session?.current_question && !showFeedback) {
      setCurrentQuestion(session.current_question)
    }
  }, [session, showFeedback])

  if (isLoading || !session) return <div className="flex justify-center py-20"><PageLoader /></div>

  if (session.status === 'completed') {
    navigate(`/interview/history/${sessionId}`, { replace: true })
    return null
  }

  const totalExpected = Object.values(session.phase_progress).reduce(
    (s, p) => s + p.total, 0
  )

  const handleSubmit = async (answer: string, duration: number) => {
    if (!currentQuestion) return
    try {
      const result = await submitResponse({
        questionId: currentQuestion.id,
        answer,
        duration,
      })
      setLastFeedback(result)
      setShowFeedback(true)
      if (result.interview_complete) setIsComplete(true)
    } catch {
      // error handled by hook
    }
  }

  const handleContinue = async () => {
    if (isComplete || lastFeedback?.interview_complete) {
      await handleEndInterview()
      return
    }
    // Next question is already in lastFeedback.next_question
    if (lastFeedback?.next_question) {
      setCurrentQuestion(lastFeedback.next_question)
    }
    setShowFeedback(false)
    setLastFeedback(null)
    // Also refetch to sync DB state
    await refetch()
  }

  const handleEndInterview = async () => {
    try {
      await endInterview()
      navigate(`/interview/history/${sessionId}`)
    } catch {
      // handled
    }
  }

  const q = showFeedback ? currentQuestion : (currentQuestion || session.current_question)

  return (
    <div className="max-w-3xl mx-auto space-y-5 animate-slide-up">
      {/* Top bar */}
      <div className="flex items-center justify-between gap-4">
        <div className="flex flex-col gap-2 flex-1">
          <div className="flex items-center gap-3">
            <h1 className="text-lg font-bold text-slate-100 capitalize">
              {session.session_type.replace('_', ' ')} Interview
            </h1>
            {session.target_role && (
              <span className="text-xs text-slate-500 bg-surface border border-surface-border px-2 py-0.5 rounded-full">
                {session.target_role}
              </span>
            )}
          </div>
          <PhaseIndicator
            currentPhase={showFeedback ? (currentQuestion?.phase ?? session.current_phase) : session.current_phase}
            phaseProgress={lastFeedback?.phase_progress ?? session.phase_progress}
          />
        </div>
        <div className="flex items-center gap-3 flex-shrink-0">
          <SessionTimer startedAt={session.started_at} isActive={true} />
          <Button
            variant="ghost"
            size="sm"
            onClick={handleEndInterview}
            loading={isEnding}
            icon={<XCircle className="h-4 w-4 text-red-400" />}
          >
            End
          </Button>
        </div>
      </div>

      {/* Question */}
      {q ? (
        <QuestionCard
          question={q}
          turnNumber={session.turn_count || 1}
          totalTurns={totalExpected}
        />
      ) : (
        <Card className="p-8 flex justify-center"><Spinner /></Card>
      )}

      {/* Answer area OR Feedback */}
      {showFeedback && lastFeedback ? (
        <FeedbackPanel
          score={lastFeedback.response_saved.score}
          feedback={lastFeedback.response_saved.feedback}
          onContinue={handleContinue}
          isLastQuestion={lastFeedback.interview_complete}
        />
      ) : q && !q.answered ? (
        <AnswerArea
          questionId={q.id}
          onSubmit={handleSubmit}
          isSubmitting={isSubmitting}
        />
      ) : null}

      {/* Progress footer */}
      <div className="flex items-center justify-between text-xs text-slate-600 px-1">
        <span>
          {session.turn_count} question{session.turn_count !== 1 ? 's' : ''} asked
        </span>
        <button
          onClick={() => navigate(`/interview/history/${sessionId}`)}
          className="flex items-center gap-1 hover:text-slate-400 transition-colors"
        >
          <List className="h-3 w-3" /> View all Q&amp;A
        </button>
      </div>
    </div>
  )
}

// ── Completion screen ─────────────────────────────────────────────────────────

function CompletionScreen({ sessionId }: { sessionId: string }) {
  const navigate = useNavigate()
  return (
    <div className="max-w-lg mx-auto text-center space-y-6 py-16 animate-slide-up">
      <div className="flex justify-center">
        <div className="h-20 w-20 rounded-full bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
          <Trophy className="h-10 w-10 text-emerald-400" />
        </div>
      </div>
      <div>
        <h1 className="text-2xl font-bold text-slate-100">Interview Complete!</h1>
        <p className="text-slate-400 mt-2 text-sm">
          Well done for completing the interview. View the full Q&amp;A transcript below.
        </p>
      </div>
      <div className="flex flex-col sm:flex-row gap-3 justify-center">
        <Button onClick={() => navigate(`/interview/history/${sessionId}`)}>
          View Transcript
        </Button>
        <Button variant="secondary" onClick={() => navigate('/interview/new')}>
          Start New Interview
        </Button>
      </div>
    </div>
  )
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function InterviewPage() {
  const { id } = useParams<{ id?: string }>()
  const navigate = useNavigate()

  const { mutateAsync: startInterview, isPending: isStarting } = useStartInterview()
  const [activeSessionId, setActiveSessionId] = useState<string | null>(id ?? null)
  const [isComplete, setIsComplete] = useState(false)

  const handleStart = async (payload: StartInterviewPayload) => {
    try {
      const session = await startInterview(payload)
      setActiveSessionId(session.id)
      navigate(`/interview/${session.id}`, { replace: true })
      toast.success('Interview started! Good luck! 🎯')
    } catch {
      // error handled by hook
    }
  }

  // If id param present, go straight to active interview
  if (id) {
    if (isComplete) return <CompletionScreen sessionId={id} />
    return <ActiveInterview sessionId={id} />
  }

  // If activeSessionId set after start
  if (activeSessionId) {
    return <ActiveInterview sessionId={activeSessionId} />
  }

  return (
    <SessionSetup onStart={handleStart} isLoading={isStarting} />
  )
}

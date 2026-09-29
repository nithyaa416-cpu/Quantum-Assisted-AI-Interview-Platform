import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Trophy, List, RotateCcw } from 'lucide-react'
import toast from 'react-hot-toast'

import { SessionSetup } from '@/components/interview/SessionSetup'
import { InterviewPrerequisites } from '@/components/interview/InterviewPrerequisites'
import { MeetingRoom } from '@/components/interview/MeetingRoom'
import { PageLoader } from '@/components/ui/Spinner'
import { Button } from '@/components/ui/Button'
import { useAuthStore } from '@/store/authStore'
import { stopAllMediaStreams } from '@/utils/mediaStreamManager'
import { stopAllAudioAndSpeech } from '@/utils/audioSpeechManager'
import {
  useStartInterview, useInterviewSession,
  useSubmitResponse, useEndInterview,
} from '@/hooks/useInterview'
import type { InterviewQuestion, SubmitResponseResult, StartInterviewPayload } from '@/types'

// ── Active meeting room container ────────────────────────────────────────────

function ActiveInterviewMeeting({ sessionId }: { sessionId: string }) {
  const navigate = useNavigate()
  const user = useAuthStore((s) => s.user)
  const candidateName = user?.full_name || user?.email?.split('@')[0] || 'Candidate'

  const { data: session, isLoading, refetch } = useInterviewSession(sessionId)
  const { mutateAsync: submitResponse, isPending: isSubmitting } = useSubmitResponse(sessionId)
  const { mutateAsync: endInterview, isPending: isEnding } = useEndInterview(sessionId)

  const [lastFeedback, setLastFeedback] = useState<SubmitResponseResult | null>(null)
  const [currentQuestion, setCurrentQuestion] = useState<InterviewQuestion | null>(null)

  useEffect(() => {
    if (session?.current_question) {
      setCurrentQuestion(session.current_question)
    }
  }, [session?.current_question?.id])

  // Stop camera, mic hardware, and all audio/speech whenever leaving this active room
  useEffect(() => {
    return () => {
      stopAllAudioAndSpeech()
      stopAllMediaStreams()
    }
  }, [])

  if (isLoading || !session) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950 text-slate-200">
        <PageLoader />
      </div>
    )
  }

  if (session.status === 'completed') {
    stopAllAudioAndSpeech()
    stopAllMediaStreams()
    navigate(`/interview/history/${sessionId}`, { replace: true })
    return null
  }

  const handleSubmit = async (answer: string, duration: number) => {
    if (!currentQuestion) return
    try {
      const result = await submitResponse({
        questionId: currentQuestion.id,
        answer,
        duration,
      })
      setLastFeedback(result)
    } catch {
      // error handled by hook
    }
  }

  const handleContinue = async () => {
    if (lastFeedback?.interview_complete) {
      await handleEndInterview()
      return
    }

    if (lastFeedback?.next_question) {
      setCurrentQuestion(lastFeedback.next_question)
    }
    setLastFeedback(null)
    await refetch()
  }

  const handleEndInterview = async () => {
    stopAllAudioAndSpeech()
    stopAllMediaStreams()
    try {
      if (document.fullscreenElement) {
        try {
          await document.exitFullscreen()
        } catch {}
      }
      await endInterview()
    } catch {
      // handled
    } finally {
      stopAllAudioAndSpeech()
      stopAllMediaStreams()
      navigate(`/interview/history/${sessionId}`)
    }
  }

  return (
    <div className="fixed inset-0 z-50 w-screen h-screen bg-slate-950 overflow-hidden">
      <MeetingRoom
        session={session}
        currentQuestion={currentQuestion || session.current_question}
        lastFeedback={lastFeedback}
        isSubmitting={isSubmitting}
        isEnding={isEnding}
        onSubmitAnswer={handleSubmit}
        onContinueNext={handleContinue}
        onEndInterview={handleEndInterview}
        candidateName={candidateName}
      />
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
          Well done for completing the live interview. You can review your detailed answers, scores, and AI feedback below.
        </p>
      </div>
      <div className="flex flex-col sm:flex-row gap-3 justify-center">
        <Button onClick={() => navigate(`/interview/history/${sessionId}`)} icon={<List className="h-4 w-4" />}>
          View Full Transcript
        </Button>
        <Button variant="secondary" onClick={() => navigate('/interview/new')} icon={<RotateCcw className="h-4 w-4" />}>
          Start Another Interview
        </Button>
      </div>
    </div>
  )
}

// ── Main Page with Mandatory Prerequisites Check ─────────────────────────────

export default function InterviewPage() {
  const { id } = useParams<{ id?: string }>()
  const navigate = useNavigate()

  // Make sure all hardware tracks stop if candidate leaves interview page completely
  useEffect(() => {
    return () => {
      stopAllMediaStreams()
    }
  }, [])

  const { mutateAsync: startInterview, isPending: isStarting } = useStartInterview()
  const [activeSessionId, setActiveSessionId] = useState<string | null>(id ?? null)
  const [pendingPayload, setPendingPayload] = useState<StartInterviewPayload | null>(null)

  // Step 1: User fills setup, clicks "Continue to Hardware & Rules Verification"
  const handleConfigReady = (payload: StartInterviewPayload) => {
    setPendingPayload(payload)
  }

  // Step 2: All prerequisites verified, launch proctored interview
  const handlePrerequisitesPassed = async (payload: StartInterviewPayload) => {
    try {
      const session = await startInterview(payload)
      setActiveSessionId(session.id)
      navigate(`/interview/${session.id}`, { replace: true })
      toast.success('Entering Proctored Examination… 🎯')
    } catch {
      // error handled by hook
    }
  }

  // Active meeting room when ID is present
  if (id || activeSessionId) {
    return <ActiveInterviewMeeting sessionId={(id || activeSessionId)!} />
  }

  // Step 2: Mandatory Hardware & Proctoring Verification
  if (pendingPayload) {
    return (
      <InterviewPrerequisites
        initialPayload={pendingPayload}
        onReadyToEnter={handlePrerequisitesPassed}
        isLoading={isStarting}
      />
    )
  }

  // Step 1: Pre-interview configuration
  return (
    <div className="max-w-3xl mx-auto py-4">
      <SessionSetup onStart={handleConfigReady} isLoading={isStarting} />
    </div>
  )
}

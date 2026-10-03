/**
 * InterviewCodingPanel
 *
 * Renders a full coding environment INSIDE the interview session UI.
 * Used by MeetingRoom.tsx when the current question has phase='coding'.
 *
 * This is NOT the standalone practice page — this is the assessment context.
 * Submissions go to /api/interview/sessions/{id}/coding-submit/ and are
 * saved as attempt_type='interview', contributing to the interview report.
 *
 * After submission, the backend generates an explanation follow-up question
 * which the interviewer avatar then asks verbally.
 *
 * Reuses existing coding components: CodeEditor, ProblemPanel, LanguageSelector, TestCasePanel.
 */
import { useState, useEffect } from 'react'
import { Play, Send, Loader2, CheckCircle2, XCircle, AlertTriangle } from 'lucide-react'
import { clsx } from 'clsx'
import toast from 'react-hot-toast'

import { CodeEditor }      from '@/components/coding/CodeEditor'
import { ProblemPanel }    from '@/components/coding/ProblemPanel'
import { LanguageSelector } from '@/components/coding/LanguageSelector'
import { TestCasePanel }   from '@/components/coding/TestCasePanel'
import { Button }          from '@/components/ui/Button'
import { Spinner }         from '@/components/ui/Spinner'

import { useRunCode }       from '@/hooks/useCoding'
import { interviewService } from '@/services/interviewService'

import { CODING_LANGUAGES } from '@/types/coding'
import type {
  CodingLanguage,
  CodingProblem,
  CodingRunResponse,
} from '@/types/coding'
import type { InterviewCodingResult } from '@/types/index'

interface InterviewCodingPanelProps {
  /** The active interview session ID */
  sessionId: string
  /** The current interview question ID (coding phase question) */
  questionId: string
  /** Called after code is successfully submitted — passes the follow-up question text */
  onSubmitted: (result: InterviewCodingResult) => void
  /** Called if user explicitly skips coding */
  onSkip?: () => void
}

const DEFAULT_LANG = CODING_LANGUAGES[0]  // Python

export function InterviewCodingPanel({
  sessionId,
  questionId,
  onSubmitted,
  onSkip,
}: InterviewCodingPanelProps) {
  // ── Problem fetching ────────────────────────────────────────────────────────
  const [problem, setProblem] = useState<CodingProblem | null>(null)
  const [loadingProblem, setLoadingProblem] = useState(true)
  const [problemError, setProblemError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setLoadingProblem(true)
    setProblemError(null)

    interviewService.getCodingProblemForQuestion(sessionId)
      .then(({ problem: p }) => {
        if (!cancelled) {
          setProblem(p)
          setLoadingProblem(false)
        }
      })
      .catch((err) => {
        if (!cancelled) {
          const msg = err?.response?.data?.message || 'Failed to load coding problem.'
          setProblemError(msg)
          setLoadingProblem(false)
        }
      })

    return () => { cancelled = true }
  }, [sessionId, questionId])

  // ── Language / code state ─────────────────────────────────────────────────
  const [language, setLanguage] = useState<CodingLanguage>(DEFAULT_LANG)
  const [code, setCode]         = useState('')
  const [starterLoaded, setStarterLoaded] = useState(false)

  useEffect(() => {
    if (problem) {
      const starter = problem.starter_code[language.id] ?? ''
      if (!starterLoaded || code === '') {
        setCode(starter)
        setStarterLoaded(true)
      }
    }
  }, [problem?.id, language.id])  // eslint-disable-line

  const handleLanguageChange = (newLang: CodingLanguage) => {
    if (!problem) { setLanguage(newLang); return }
    const currentStarter = problem.starter_code[language.id] ?? ''
    const isEdited = code.trim() !== currentStarter.trim() && code.trim() !== ''
    if (isEdited) {
      const confirmed = window.confirm(
        `Switch to ${newLang.name}?\n\nYour current code will be replaced with the ${newLang.name} starter template.`
      )
      if (!confirmed) return
    }
    setLanguage(newLang)
    setCode(problem.starter_code[newLang.id] ?? '')
  }

  // ── Run Code (against public test cases only) ─────────────────────────────
  const { mutateAsync: runCode, isPending: isRunning } = useRunCode()
  const [runResult, setRunResult] = useState<CodingRunResponse | null>(null)

  const handleRun = async () => {
    if (!problem || !code.trim()) return
    setRunResult(null)
    try {
      const result = await runCode({
        problem_id:  problem.id,
        language:    language.id,
        source_code: code,
      })
      setRunResult(result)
    } catch {
      // error toasted by hook
    }
  }

  // ── Submit (interview — runs ALL test cases, saves as interview attempt) ──
  const [isSubmitting, setIsSubmitting]   = useState(false)
  const [submitResult, setSubmitResult]   = useState<InterviewCodingResult | null>(null)
  const [submitted, setSubmitted]         = useState(false)

  const handleSubmit = async () => {
    if (!problem || !code.trim() || isSubmitting || submitted) return

    const confirmed = window.confirm(
      'Submit your solution?\n\nAll test cases (including hidden ones) will be run.\nThis is your interview submission — it will be evaluated and scored.'
    )
    if (!confirmed) return

    setIsSubmitting(true)
    try {
      const result = await interviewService.submitInterviewCode(sessionId, {
        question_id: questionId,
        problem_id:  problem.id,
        language:    language.id,
        source_code: code,
      })
      setSubmitResult(result)
      setSubmitted(true)

      if (result.status === 'accepted') {
        toast.success(`Accepted! ${result.passed}/${result.total} test cases passed.`)
      } else {
        toast.error(`${result.status.replace(/_/g, ' ')} — ${result.passed}/${result.total} test cases passed.`)
      }

      // Notify parent so MeetingRoom can transition to explanation follow-up
      onSubmitted(result)
    } catch (err: any) {
      const msg = err?.response?.data?.message || 'Submission failed. Please try again.'
      toast.error(msg)
    } finally {
      setIsSubmitting(false)
    }
  }

  const isActionDisabled = isRunning || isSubmitting || submitted || !problem

  // ── Status indicator after submission ─────────────────────────────────────
  const renderSubmitStatus = () => {
    if (!submitResult) return null
    const { status, passed, total, score } = submitResult
    const pct = Math.round(score * 100)

    return (
      <div className={clsx(
        'flex items-center gap-3 px-4 py-3 rounded-xl border text-sm',
        status === 'accepted'
          ? 'bg-green-500/10 border-green-500/30 text-green-400'
          : 'bg-yellow-500/10 border-yellow-500/30 text-yellow-400'
      )}>
        {status === 'accepted'
          ? <CheckCircle2 className="h-4 w-4 flex-shrink-0" />
          : score >= 0.5
            ? <AlertTriangle className="h-4 w-4 flex-shrink-0" />
            : <XCircle className="h-4 w-4 flex-shrink-0" />
        }
        <div>
          <span className="font-semibold capitalize">{status.replace(/_/g, ' ')}</span>
          <span className="text-slate-400 ml-2">
            {passed}/{total} tests passed · {pct}% score
          </span>
        </div>
        <span className="ml-auto text-xs text-slate-500">
          Now explain your approach to the interviewer.
        </span>
      </div>
    )
  }

  // ── Loading / error states ────────────────────────────────────────────────
  if (loadingProblem) {
    return (
      <div className="flex items-center justify-center h-64 gap-3 text-slate-400">
        <Spinner size="sm" />
        <span className="text-sm">Loading coding problem…</span>
      </div>
    )
  }

  if (problemError || !problem) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-3 text-slate-400">
        <XCircle className="h-8 w-8 text-red-400" />
        <p className="text-sm">{problemError || 'Problem not found.'}</p>
        {onSkip && (
          <Button variant="secondary" size="sm" onClick={onSkip}>
            Skip coding question
          </Button>
        )}
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full border border-surface-border rounded-xl overflow-hidden bg-surface">
      {/* ── Header ─────────────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between px-4 py-2.5 bg-surface-card border-b border-surface-border flex-shrink-0">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-md bg-orange-500/20 border border-orange-500/30">
            <span className="text-xs font-semibold text-orange-400 tracking-wide">CODING</span>
          </div>
          <span className="text-sm font-semibold text-slate-200 truncate max-w-[300px]">
            {problem.title}
          </span>
          {problem.difficulty && (
            <span className={clsx(
              'text-xs px-1.5 py-0.5 rounded font-medium',
              problem.difficulty === 'easy'   && 'bg-green-500/20 text-green-400',
              problem.difficulty === 'medium' && 'bg-yellow-500/20 text-yellow-400',
              problem.difficulty === 'hard'   && 'bg-red-500/20 text-red-400',
            )}>
              {problem.difficulty}
            </span>
          )}
          {/* Topic tags */}
          {(problem as any).topics?.slice(0, 2).map((t: string) => (
            <span key={t} className="hidden xl:inline text-xs px-1.5 py-0.5 rounded bg-slate-700 text-slate-400 capitalize">
              {t.replace(/_/g, ' ')}
            </span>
          ))}
        </div>

        {submitted && (
          <span className="text-xs text-green-400 flex items-center gap-1">
            <CheckCircle2 className="h-3 w-3" />
            Submitted
          </span>
        )}
      </div>

      {/* ── Submission result banner ──────────────────────────────────────── */}
      {submitResult && (
        <div className="px-3 py-2 flex-shrink-0">
          {renderSubmitStatus()}
        </div>
      )}

      {/* ── Main split: Problem | Editor ─────────────────────────────────── */}
      <div className="flex flex-1 min-h-0 overflow-hidden">

        {/* Left: Problem description */}
        <div className="w-[42%] min-w-[280px] max-w-[440px] border-r border-surface-border overflow-hidden flex-shrink-0">
          <ProblemPanel problem={problem} isLoading={false} />
        </div>

        {/* Right: Language selector + Monaco + Run/Submit + Test cases */}
        <div className="flex flex-col flex-1 min-w-0 overflow-hidden">

          {/* Language bar + action buttons */}
          <div className="flex items-center justify-between px-3 py-2 bg-surface-card border-b border-surface-border flex-shrink-0">
            <LanguageSelector
              selected={language}
              onChange={handleLanguageChange}
              disabled={isActionDisabled}
            />
            <div className="flex items-center gap-2">
              <Button
                variant="secondary"
                size="sm"
                onClick={handleRun}
                disabled={isActionDisabled}
                loading={isRunning}
                icon={!isRunning ? <Play className="h-3.5 w-3.5" /> : undefined}
              >
                {isRunning ? 'Running…' : 'Run Code'}
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={handleSubmit}
                disabled={isActionDisabled || submitted}
                loading={isSubmitting}
                icon={
                  submitted
                    ? <CheckCircle2 className="h-3.5 w-3.5" />
                    : !isSubmitting
                      ? <Send className="h-3.5 w-3.5" />
                      : undefined
                }
              >
                {submitted ? 'Submitted' : isSubmitting ? 'Submitting…' : 'Submit'}
              </Button>
              {onSkip && !submitted && (
                <Button variant="ghost" size="sm" onClick={onSkip}>
                  Skip
                </Button>
              )}
            </div>
          </div>

          {/* Monaco editor */}
          <div className="flex-1 min-h-0 p-2">
            <CodeEditor
              value={code}
              onChange={setCode}
              language={language}
              readOnly={isRunning || isSubmitting || submitted}
              height="100%"
            />
          </div>

          {/* Test case results */}
          <div className="h-48 flex-shrink-0">
            <TestCasePanel
              publicTestCases={problem.public_test_cases ?? []}
              runResult={runResult}
              submitResult={submitResult as any}
              isRunning={isRunning}
              isSubmitting={isSubmitting}
            />
          </div>
        </div>
      </div>
    </div>
  )
}


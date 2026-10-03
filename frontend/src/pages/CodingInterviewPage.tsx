/**
 * CodingInterviewPage — LeetCode-style coding interview interface.
 *
 * Layout (desktop):
 *   ┌──────────────────────────────────────────────────────────┐
 *   │  TopBar: Problem selector | Difficulty | Timer           │
 *   ├───────────────────────┬──────────────────────────────────┤
 *   │  ProblemPanel (scroll)│  LanguageSelector                │
 *   │                       │  ┌────────────────────────────┐  │
 *   │                       │  │  Monaco Editor             │  │
 *   │                       │  └────────────────────────────┘  │
 *   │                       │  [Run Code]        [Submit]       │
 *   ├───────────────────────┴──────────────────────────────────┤
 *   │  TestCasePanel (Examples / Run Results / Submission)      │
 *   └──────────────────────────────────────────────────────────┘
 *
 * Mobile: all panels stacked vertically.
 */
import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import toast from 'react-hot-toast'
import { ArrowLeft, Play, Send, ChevronDown } from 'lucide-react'
import { clsx } from 'clsx'

import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { Spinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'

import { CodeEditor }      from '@/components/coding/CodeEditor'
import { ProblemPanel }    from '@/components/coding/ProblemPanel'
import { LanguageSelector } from '@/components/coding/LanguageSelector'
import { TestCasePanel }   from '@/components/coding/TestCasePanel'
import { CodingTimer, useCodingTimer } from '@/components/coding/CodingTimer'

import {
  useCodingProblems,
  useCodingProblem,
  useRunCode,
  useSubmitCode,
} from '@/hooks/useCoding'

import { CODING_LANGUAGES } from '@/types/coding'
import type {
  CodingLanguage,
  CodingRunResponse,
  CodingSubmissionResponse,
} from '@/types/coding'

const DEFAULT_LANG = CODING_LANGUAGES[0]   // Python

export default function CodingInterviewPage() {
  const { problemId }  = useParams<{ problemId?: string }>()
  const navigate       = useNavigate()

  // ── Problem selection state ─────────────────────────────────────────────────
  const { data: problems = [], isLoading: problemsLoading } = useCodingProblems()
  const [selectedProblemId, setSelectedProblemId] = useState<string | null>(problemId ?? null)

  // Auto-select first problem when list loads
  useEffect(() => {
    if (!selectedProblemId && problems.length > 0) {
      setSelectedProblemId(problems[0].id)
    }
  }, [problems, selectedProblemId])

  const { data: problem, isLoading: problemLoading } = useCodingProblem(selectedProblemId)

  // ── Language / code state ───────────────────────────────────────────────────
  const [language, setLanguage] = useState<CodingLanguage>(DEFAULT_LANG)
  const [code, setCode]         = useState('')
  const [starterLoaded, setStarterLoaded] = useState(false)

  // Load starter code when problem / language changes
  useEffect(() => {
    if (problem) {
      const starter = problem.starter_code[language.id] ?? ''
      if (!starterLoaded || code === '' || code === getOtherStarter()) {
        setCode(starter)
        setStarterLoaded(true)
      }
    }
  }, [problem?.id, language.id])

  function getOtherStarter(): string {
    if (!problem) return ''
    for (const lang of CODING_LANGUAGES) {
      if (lang.id !== language.id) {
        const s = problem.starter_code[lang.id]
        if (s) return s
      }
    }
    return ''
  }

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

  // ── Timer ────────────────────────────────────────────────────────────────────
  const { isExpired } = useCodingTimer(30 * 60)

  const handleTimerExpired = useCallback(() => {
    toast.error('⏱ Time is up! Your code has been preserved.', { duration: 6000 })
  }, [])

  // ── Run Code ─────────────────────────────────────────────────────────────────
  const { mutateAsync: runCode, isPending: isRunning } = useRunCode()
  const [runResult, setRunResult] = useState<CodingRunResponse | null>(null)

  const handleRun = async () => {
    if (!problem || isExpired) return
    setRunResult(null)
    try {
      const result = await runCode({
        problem_id:  problem.id,
        language:    language.id,
        source_code: code,
      })
      setRunResult(result)
    } catch {
      // error handled by hook
    }
  }

  // ── Submit ────────────────────────────────────────────────────────────────────
  const { mutateAsync: submitCode, isPending: isSubmitting } = useSubmitCode()
  const [submitResult, setSubmitResult] = useState<CodingSubmissionResponse | null>(null)

  const handleSubmit = async () => {
    if (!problem || isExpired) return
    const confirmed = window.confirm('Submit your solution?\n\nAll test cases (including hidden ones) will be run.')
    if (!confirmed) return
    setSubmitResult(null)
    try {
      const result = await submitCode({
        problem_id:  problem.id,
        language:    language.id,
        source_code: code,
      })
      setSubmitResult(result)
      if (result.status === 'accepted') {
        toast.success(`✅ Accepted! ${result.passed}/${result.total} test cases passed.`)
      } else {
        toast.error(`❌ ${result.status.replace(/_/g, ' ')} — ${result.passed}/${result.total} passed.`)
      }
    } catch {
      // error handled by hook
    }
  }

  // ── Problem selector in top bar ───────────────────────────────────────────────
  const diffBadge = (d?: string) => {
    if (d === 'easy')   return <Badge color="green">Easy</Badge>
    if (d === 'medium') return <Badge color="yellow">Medium</Badge>
    if (d === 'hard')   return <Badge color="red">Hard</Badge>
    return null
  }

  const isActionDisabled = isRunning || isSubmitting || isExpired || !problem

  return (
    <div className="flex flex-col h-screen bg-surface overflow-hidden">
      {/* ── Top bar ─────────────────────────────────────────────────────────── */}
      <header className="flex items-center justify-between px-4 py-2 bg-surface-card border-b border-surface-border flex-shrink-0 gap-4">
        <div className="flex items-center gap-3">
          <Link to="/dashboard" className="text-slate-400 hover:text-slate-200 transition-colors">
            <ArrowLeft className="h-4 w-4" />
          </Link>

          {/* Problem picker */}
          <div className="relative flex items-center gap-2">
            {problemsLoading ? (
              <Spinner size="sm" />
            ) : (
              <>
                <select
                  value={selectedProblemId ?? ''}
                  onChange={(e) => {
                    setSelectedProblemId(e.target.value)
                    setRunResult(null)
                    setSubmitResult(null)
                    setStarterLoaded(false)
                  }}
                  className="appearance-none bg-transparent text-slate-200 font-semibold text-sm pr-6 focus:outline-none cursor-pointer max-w-[200px] truncate"
                >
                  {problems.map((p) => (
                    <option key={p.id} value={p.id}>{p.title}</option>
                  ))}
                </select>
                <ChevronDown className="h-3.5 w-3.5 text-slate-500 pointer-events-none absolute right-0" />
              </>
            )}
          </div>

          {diffBadge(problem?.difficulty)}
        </div>

        <CodingTimer durationSeconds={30 * 60} onExpire={handleTimerExpired} />
      </header>

      {/* ── Main content ─────────────────────────────────────────────────────── */}
      <div className="flex flex-1 min-h-0 overflow-hidden">

        {/* ── Left: Problem panel ─────────────────────────────────────────────── */}
        <div className="hidden lg:flex flex-col w-[42%] min-w-[320px] max-w-[500px] border-r border-surface-border overflow-hidden flex-shrink-0">
          <ProblemPanel problem={problem} isLoading={problemLoading} />
        </div>

        {/* ── Right: Editor + TestCasePanel ────────────────────────────────────── */}
        <div className="flex flex-col flex-1 min-w-0 overflow-hidden">

          {/* Editor area — takes most of the space */}
          <div className="flex flex-col flex-1 min-h-0">
            {/* Language selector bar */}
            <div className="flex items-center justify-between px-4 py-2 bg-surface-card border-b border-surface-border flex-shrink-0">
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
                  disabled={isActionDisabled}
                  loading={isSubmitting}
                  icon={!isSubmitting ? <Send className="h-3.5 w-3.5" /> : undefined}
                >
                  {isSubmitting ? 'Submitting…' : 'Submit'}
                </Button>
              </div>
            </div>

            {/* Monaco editor fills remaining height */}
            <div className="flex-1 min-h-0 p-2">
              {isExpired ? (
                <div className="h-full flex items-center justify-center">
                  <EmptyState
                    title="Time's Up"
                    description="The coding session has ended. Your code has been preserved above."
                    icon={<Play className="h-7 w-7" />}
                  />
                </div>
              ) : (
                <CodeEditor
                  value={code}
                  onChange={setCode}
                  language={language}
                  readOnly={isActionDisabled && !isRunning && !isSubmitting}
                  height="100%"
                />
              )}
            </div>
          </div>

          {/* Test case panel — fixed height at bottom */}
          <div className="h-56 flex-shrink-0">
            <TestCasePanel
              publicTestCases={problem?.public_test_cases ?? []}
              runResult={runResult}
              submitResult={submitResult}
              isRunning={isRunning}
              isSubmitting={isSubmitting}
            />
          </div>
        </div>
      </div>

      {/* Mobile: problem panel below editor (only on small screens) */}
      <div className="lg:hidden border-t border-surface-border max-h-64 overflow-y-auto">
        <ProblemPanel problem={problem} isLoading={problemLoading} />
      </div>
    </div>
  )
}

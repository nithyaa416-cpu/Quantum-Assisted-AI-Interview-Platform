/**
 * CodingPracticePage — Standalone coding preparation module.
 *
 * This is NOT an interview. It is a practice environment where students
 * can independently solve coding problems to improve their skills.
 *
 * Submissions here are saved with attempt_type='practice' and contribute
 * to skill improvement tracking and weakness detection — not interview scores.
 *
 * Layout:
 *   ┌──────────────────────────────────────────────────────────┐
 *   │  TopBar: [PRACTICE MODE] Problem selector | Timer        │
 *   ├───────────────────────┬──────────────────────────────────┤
 *   │  ProblemPanel (scroll)│  LanguageSelector                │
 *   │                       │  Monaco Editor                   │
 *   │                       │  [Run Code]  [Submit]            │
 *   ├───────────────────────┴──────────────────────────────────┤
 *   │  TestCasePanel                                           │
 *   └──────────────────────────────────────────────────────────┘
 */
import { useState, useEffect, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'
import toast from 'react-hot-toast'
import { ArrowLeft, Play, Send, ChevronDown, BookOpen, TrendingUp } from 'lucide-react'

import { Button } from '@/components/ui/Button'
import { Badge }  from '@/components/ui/Badge'
import { Spinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'

import { CodeEditor }       from '@/components/coding/CodeEditor'
import { ProblemPanel }     from '@/components/coding/ProblemPanel'
import { LanguageSelector }  from '@/components/coding/LanguageSelector'
import { TestCasePanel }    from '@/components/coding/TestCasePanel'
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

const DEFAULT_LANG = CODING_LANGUAGES[0]  // Python

export default function CodingPracticePage() {
  const { problemId } = useParams<{ problemId?: string }>()

  // ── Problem selection ─────────────────────────────────────────────────────
  const { data: problems = [], isLoading: problemsLoading } = useCodingProblems()
  const [selectedProblemId, setSelectedProblemId] = useState<string | null>(problemId ?? null)
  const [difficultyFilter, setDifficultyFilter] = useState<string>('all')
  const [topicFilter, setTopicFilter] = useState<string>('all')

  // Auto-select first problem when list loads
  useEffect(() => {
    if (!selectedProblemId && problems.length > 0) {
      setSelectedProblemId(problems[0].id)
    }
  }, [problems, selectedProblemId])

  const { data: problem, isLoading: problemLoading } = useCodingProblem(selectedProblemId)

  // Filter problems by difficulty / topic
  const filteredProblems = problems.filter((p) => {
    const diffMatch = difficultyFilter === 'all' || p.difficulty === difficultyFilter
    return diffMatch
  })

  // ── Language / code state ─────────────────────────────────────────────────
  const [language, setLanguage] = useState<CodingLanguage>(DEFAULT_LANG)
  const [code, setCode]         = useState('')
  const [starterLoaded, setStarterLoaded] = useState(false)

  useEffect(() => {
    if (problem) {
      const starter = problem.starter_code[language.id] ?? ''
      if (!starterLoaded || code === '' || code === getOtherStarter()) {
        setCode(starter)
        setStarterLoaded(true)
      }
    }
  }, [problem?.id, language.id])  // eslint-disable-line

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

  // ── Timer (60 min for practice) ───────────────────────────────────────────
  const { isExpired } = useCodingTimer(60 * 60)

  const handleTimerExpired = useCallback(() => {
    toast('Practice session time is up — you can still continue at your own pace.', {
      duration: 6000,
      icon: '⏱',
    })
  }, [])

  // ── Run Code ─────────────────────────────────────────────────────────────
  const { mutateAsync: runCode, isPending: isRunning } = useRunCode()
  const [runResult, setRunResult] = useState<CodingRunResponse | null>(null)

  const handleRun = async () => {
    if (!problem) return
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

  // ── Submit ────────────────────────────────────────────────────────────────
  const { mutateAsync: submitCode, isPending: isSubmitting } = useSubmitCode()
  const [submitResult, setSubmitResult] = useState<CodingSubmissionResponse | null>(null)

  const handleSubmit = async () => {
    if (!problem) return
    const confirmed = window.confirm(
      'Submit your solution?\n\nAll test cases (including hidden ones) will be run.\nThis submission will count towards your practice progress.'
    )
    if (!confirmed) return
    setSubmitResult(null)
    try {
      const result = await submitCode({
        problem_id:  problem.id,
        language:    language.id,
        source_code: code,
        // attempt_type is set by backend for non-session submissions
      })
      setSubmitResult(result)
      if (result.status === 'accepted') {
        toast.success(`Accepted! ${result.passed}/${result.total} test cases passed.`)
      } else {
        toast.error(`${result.status.replace(/_/g, ' ')} — ${result.passed}/${result.total} passed.`)
      }
    } catch {
      // error handled by hook
    }
  }

  // ── Difficulty badge ──────────────────────────────────────────────────────
  const diffBadge = (d?: string) => {
    if (d === 'easy')   return <Badge color="green">Easy</Badge>
    if (d === 'medium') return <Badge color="yellow">Medium</Badge>
    if (d === 'hard')   return <Badge color="red">Hard</Badge>
    return null
  }

  const isActionDisabled = isRunning || isSubmitting || !problem

  return (
    <div className="flex flex-col h-screen bg-surface overflow-hidden">
      {/* ── Top bar ─────────────────────────────────────────────────────────── */}
      <header className="flex items-center justify-between px-4 py-2 bg-surface-card border-b border-surface-border flex-shrink-0 gap-4">
        <div className="flex items-center gap-3">
          <Link to="/dashboard" className="text-slate-400 hover:text-slate-200 transition-colors">
            <ArrowLeft className="h-4 w-4" />
          </Link>

          {/* Practice Mode badge */}
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-brand-600/20 border border-brand-600/30">
            <BookOpen className="h-3.5 w-3.5 text-brand-400" />
            <span className="text-xs font-semibold text-brand-400 tracking-wide">PRACTICE MODE</span>
          </div>

          {/* Difficulty filter */}
          <select
            value={difficultyFilter}
            onChange={(e) => setDifficultyFilter(e.target.value)}
            className="text-xs bg-surface-hover border border-surface-border rounded-lg px-2 py-1 text-slate-300 focus:outline-none"
          >
            <option value="all" className="bg-slate-900 text-slate-300">All difficulties</option>
            <option value="easy" className="bg-slate-900 text-emerald-400">Easy</option>
            <option value="medium" className="bg-slate-900 text-amber-400">Medium</option>
            <option value="hard" className="bg-slate-900 text-rose-400">Hard</option>
          </select>

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
                  className="appearance-none bg-transparent text-slate-200 font-semibold text-sm pr-6 focus:outline-none cursor-pointer max-w-[220px] truncate"
                >
                  {filteredProblems.map((p) => (
                    <option key={p.id} value={p.id} className="bg-slate-900 text-slate-200">
                      {p.title}
                    </option>
                  ))}
                </select>
                <ChevronDown className="h-3.5 w-3.5 text-slate-500 pointer-events-none absolute right-0" />
              </>
            )}
          </div>

          {diffBadge(problem?.difficulty)}

          {/* Topic tags */}
          {problem && (problem as any).topics?.length > 0 && (
            <div className="hidden xl:flex items-center gap-1">
              {((problem as any).topics as string[]).slice(0, 3).map((t: string) => (
                <span
                  key={t}
                  className="px-1.5 py-0.5 text-xs rounded bg-slate-700 text-slate-400 capitalize"
                >
                  {t.replace(/_/g, ' ')}
                </span>
              ))}
            </div>
          )}
        </div>

        <div className="flex items-center gap-3">
          <CodingTimer durationSeconds={60 * 60} onExpire={handleTimerExpired} />
          <div className="flex items-center gap-1 text-xs text-slate-500">
            <TrendingUp className="h-3 w-3" />
            <span>Practice</span>
          </div>
        </div>
      </header>

      {/* ── Main content ─────────────────────────────────────────────────────── */}
      <div className="flex flex-1 min-h-0 overflow-hidden">

        {/* ── Left: Problem panel ─────────────────────────────────────────────── */}
        <div className="hidden lg:flex flex-col w-[42%] min-w-[320px] max-w-[500px] border-r border-surface-border overflow-hidden flex-shrink-0">
          <ProblemPanel problem={problem} isLoading={problemLoading} />
        </div>

        {/* ── Right: Editor + TestCasePanel ─────────────────────────────────── */}
        <div className="flex flex-col flex-1 min-w-0 overflow-hidden">

          {/* Editor area */}
          <div className="flex flex-col flex-1 min-h-0">
            {/* Language selector + action buttons */}
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

            {/* Monaco editor */}
            <div className="flex-1 min-h-0 p-2">
              {isExpired ? (
                <div className="h-full flex items-center justify-center">
                  <EmptyState
                    title="Session Timer Expired"
                    description="You can still keep practicing — there's no hard limit in practice mode."
                    icon={<Play className="h-7 w-7" />}
                  />
                </div>
              ) : (
                <CodeEditor
                  value={code}
                  onChange={setCode}
                  language={language}
                  readOnly={isRunning || isSubmitting}
                  height="100%"
                />
              )}
            </div>
          </div>

          {/* Test case panel */}
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

      {/* Mobile: problem panel below editor */}
      <div className="lg:hidden border-t border-surface-border max-h-64 overflow-y-auto">
        <ProblemPanel problem={problem} isLoading={problemLoading} />
      </div>
    </div>
  )
}


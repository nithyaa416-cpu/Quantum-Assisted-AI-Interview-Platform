import { useState } from 'react'
import { clsx } from 'clsx'
import {
  CheckCircle2, XCircle, Clock, MemoryStick,
  AlertCircle, PlayCircle, Trophy,
} from 'lucide-react'
import { Spinner } from '@/components/ui/Spinner'
import type {
  CodingTestCase, CodingRunResponse,
  CodingSubmissionResponse, ExecutionStatus,
} from '@/types/coding'

type Tab = 'examples' | 'run_results' | 'submit_result'

// ── Status display helpers ─────────────────────────────────────────────────────

const STATUS_CONFIG: Record<ExecutionStatus, { label: string; color: string; Icon: React.ElementType }> = {
  accepted:             { label: 'Accepted',              color: 'text-emerald-400', Icon: CheckCircle2 },
  wrong_answer:         { label: 'Wrong Answer',          color: 'text-red-400',     Icon: XCircle      },
  compilation_error:    { label: 'Compilation Error',     color: 'text-amber-400',   Icon: AlertCircle  },
  runtime_error:        { label: 'Runtime Error',         color: 'text-red-400',     Icon: AlertCircle  },
  time_limit_exceeded:  { label: 'Time Limit Exceeded',   color: 'text-orange-400',  Icon: Clock        },
  memory_limit_exceeded:{ label: 'Memory Limit Exceeded', color: 'text-orange-400',  Icon: MemoryStick  },
  internal_error:       { label: 'Internal Error',        color: 'text-slate-400',   Icon: AlertCircle  },
  pending:              { label: 'Pending',               color: 'text-slate-400',   Icon: Clock        },
}

function StatusBadge({ status }: { status: ExecutionStatus }) {
  const cfg = STATUS_CONFIG[status] ?? STATUS_CONFIG.internal_error
  const { label, color, Icon } = cfg
  return (
    <span className={clsx('inline-flex items-center gap-1.5 text-sm font-semibold', color)}>
      <Icon className="h-4 w-4" />
      {label}
    </span>
  )
}

function CodeBox({ label, content }: { label: string; content: string }) {
  if (!content) return null
  return (
    <div className="space-y-1">
      <p className="text-xs text-slate-500 font-medium">{label}</p>
      <pre className="bg-surface rounded-lg p-3 text-xs font-mono text-slate-300 overflow-x-auto border border-surface-border whitespace-pre-wrap max-h-32">
        {content}
      </pre>
    </div>
  )
}

// ── Examples tab ──────────────────────────────────────────────────────────────

function ExamplesTab({ testCases }: { testCases: CodingTestCase[] }) {
  if (testCases.length === 0) {
    return <p className="text-slate-500 text-sm py-4 text-center">No sample test cases available.</p>
  }
  return (
    <div className="space-y-4">
      {testCases.map((tc, i) => (
        <div key={tc.id} className="space-y-2">
          <p className="text-xs font-semibold text-slate-400">Case {i + 1}</p>
          <CodeBox label="Input" content={tc.input_data} />
          <CodeBox label="Expected Output" content={tc.expected_output} />
        </div>
      ))}
    </div>
  )
}

// ── Run results tab ────────────────────────────────────────────────────────────

function RunResultsTab({ result, isRunning }: { result: CodingRunResponse | null; isRunning: boolean }) {
  if (isRunning) {
    return (
      <div className="flex items-center gap-3 py-6 justify-center text-slate-400">
        <Spinner size="sm" />
        <span className="text-sm">Executing…</span>
      </div>
    )
  }
  if (!result) {
    return (
      <div className="flex flex-col items-center gap-2 py-8 text-slate-600">
        <PlayCircle className="h-8 w-8" />
        <p className="text-sm">Run your code to see the results.</p>
      </div>
    )
  }
  return (
    <div className="space-y-4">
      {/* Summary */}
      <div className="flex items-center justify-between">
        <StatusBadge status={result.overall_status} />
        <span className="text-sm text-slate-400">
          {result.passed} / {result.total} passed
        </span>
      </div>

      {/* Per test case */}
      {result.results.map((r, i) => (
        <div key={r.test_case_id || i}
          className={clsx(
            'rounded-xl border p-3 space-y-2',
            r.passed
              ? 'border-emerald-500/20 bg-emerald-500/5'
              : 'border-red-500/20 bg-red-500/5',
          )}>
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-300">Test case {i + 1}</span>
            <div className="flex items-center gap-3">
              {r.time_ms !== null && (
                <span className="text-xs text-slate-500 flex items-center gap-1">
                  <Clock className="h-3 w-3" />{r.time_ms.toFixed(0)}ms
                </span>
              )}
              <StatusBadge status={r.passed ? 'accepted' : r.status} />
            </div>
          </div>
          {r.input        && <CodeBox label="Input"           content={r.input} />}
          {r.expected_output && <CodeBox label="Expected"     content={r.expected_output} />}
          {r.stdout       && <CodeBox label="Your Output"     content={r.stdout} />}
          {r.stderr       && <CodeBox label="Error"           content={r.stderr} />}
        </div>
      ))}
    </div>
  )
}

// ── Submit result tab ──────────────────────────────────────────────────────────

function SubmitResultTab({
  result, isSubmitting,
}: { result: CodingSubmissionResponse | null; isSubmitting: boolean }) {
  if (isSubmitting) {
    return (
      <div className="flex items-center gap-3 py-6 justify-center text-slate-400">
        <Spinner size="sm" />
        <span className="text-sm">Submitting all test cases…</span>
      </div>
    )
  }
  if (!result) {
    return (
      <div className="flex flex-col items-center gap-2 py-8 text-slate-600">
        <Trophy className="h-8 w-8" />
        <p className="text-sm">Submit your solution to see the final result.</p>
      </div>
    )
  }
  const accepted = result.status === 'accepted'
  return (
    <div className="space-y-4">
      <div className={clsx(
        'rounded-xl border p-4 space-y-3',
        accepted
          ? 'border-emerald-500/30 bg-emerald-500/8'
          : 'border-red-500/30 bg-red-500/8',
      )}>
        <StatusBadge status={result.status} />
        <div className="grid grid-cols-2 gap-x-6 gap-y-1 text-sm">
          <div className="text-slate-500">Test cases</div>
          <div className="text-slate-200 font-medium">{result.passed} / {result.total}</div>
          {result.runtime_ms !== null && (
            <>
              <div className="text-slate-500">Runtime</div>
              <div className="text-slate-200 font-medium">{result.runtime_ms.toFixed(0)} ms</div>
            </>
          )}
          {result.memory_kb !== null && (
            <>
              <div className="text-slate-500">Memory</div>
              <div className="text-slate-200 font-medium">{(result.memory_kb / 1024).toFixed(1)} MB</div>
            </>
          )}
          <div className="text-slate-500">Score</div>
          <div className="text-slate-200 font-medium">{Math.round(result.score * 100)}%</div>
        </div>
      </div>

      {/* Show visible test results only */}
      {result.results.filter(r => r.input !== null).map((r, i) => (
        <div key={r.test_case_id || i}
          className={clsx(
            'rounded-xl border p-3 space-y-2',
            r.passed ? 'border-emerald-500/20 bg-emerald-500/5' : 'border-red-500/20 bg-red-500/5',
          )}>
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400">Test case {i + 1}</span>
            <StatusBadge status={r.passed ? 'accepted' : r.status} />
          </div>
          {r.input           && <CodeBox label="Input"    content={r.input} />}
          {r.expected_output && <CodeBox label="Expected" content={r.expected_output} />}
          {r.stdout          && <CodeBox label="Output"   content={r.stdout} />}
          {r.stderr          && <CodeBox label="Error"    content={r.stderr} />}
        </div>
      ))}
    </div>
  )
}

// ── Main panel ────────────────────────────────────────────────────────────────

interface TestCasePanelProps {
  publicTestCases: CodingTestCase[]
  runResult:     CodingRunResponse | null
  submitResult:  CodingSubmissionResponse | null
  isRunning:     boolean
  isSubmitting:  boolean
}

export function TestCasePanel({
  publicTestCases, runResult, submitResult, isRunning, isSubmitting,
}: TestCasePanelProps) {
  // Auto-switch tabs when results arrive
  const [activeTab, setActiveTab] = useState<Tab>('examples')

  const tabs: { id: Tab; label: string }[] = [
    { id: 'examples',      label: 'Examples' },
    { id: 'run_results',   label: isRunning  ? 'Running…'   : (runResult    ? `Results (${runResult.passed}/${runResult.total})`    : 'Test Results') },
    { id: 'submit_result', label: isSubmitting ? 'Submitting…' : (submitResult ? `Submission`                                       : 'Submission') },
  ]

  // Auto-switch when results come in
  if (isRunning && activeTab !== 'run_results')     setActiveTab('run_results')
  if (isSubmitting && activeTab !== 'submit_result') setActiveTab('submit_result')
  if (runResult    && !isRunning    && activeTab === 'examples') setActiveTab('run_results')
  if (submitResult && !isSubmitting && activeTab !== 'submit_result') setActiveTab('submit_result')

  return (
    <div className="flex flex-col h-full border-t border-surface-border bg-surface-card">
      {/* Tab bar */}
      <div className="flex border-b border-surface-border flex-shrink-0">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={clsx(
              'px-4 py-2.5 text-sm font-medium transition-colors border-b-2 whitespace-nowrap',
              activeTab === tab.id
                ? 'border-brand-500 text-brand-400'
                : 'border-transparent text-slate-400 hover:text-slate-200',
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {activeTab === 'examples'      && <ExamplesTab testCases={publicTestCases} />}
        {activeTab === 'run_results'   && <RunResultsTab result={runResult} isRunning={isRunning} />}
        {activeTab === 'submit_result' && <SubmitResultTab result={submitResult} isSubmitting={isSubmitting} />}
      </div>
    </div>
  )
}

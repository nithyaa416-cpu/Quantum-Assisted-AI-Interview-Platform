import { clsx } from 'clsx'
import { Clock, Cpu, AlertCircle } from 'lucide-react'
import { Badge } from '@/components/ui/Badge'
import { Spinner } from '@/components/ui/Spinner'
import type { CodingProblem } from '@/types/coding'

interface ProblemPanelProps {
  problem: CodingProblem | undefined
  isLoading: boolean
}

const difficultyConfig = {
  easy:   { color: 'green'  as const, label: 'Easy'   },
  medium: { color: 'yellow' as const, label: 'Medium' },
  hard:   { color: 'red'    as const, label: 'Hard'   },
}

function CodeBlock({ children }: { children: string }) {
  return (
    <pre className="bg-surface rounded-lg p-3 text-xs font-mono text-slate-300 overflow-x-auto border border-surface-border leading-relaxed whitespace-pre-wrap">
      {children}
    </pre>
  )
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="space-y-2">
      <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">{title}</h3>
      {children}
    </div>
  )
}

export function ProblemPanel({ problem, isLoading }: ProblemPanelProps) {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Spinner size="md" />
      </div>
    )
  }

  if (!problem) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-3 text-slate-500">
        <AlertCircle className="h-8 w-8" />
        <p className="text-sm">Problem not found.</p>
      </div>
    )
  }

  const diff = difficultyConfig[problem.difficulty] ?? difficultyConfig.easy

  return (
    <div className="h-full overflow-y-auto px-5 py-4 space-y-5">
      {/* Header */}
      <div className="space-y-2">
        <div className="flex items-start justify-between gap-3">
          <h1 className="text-lg font-bold text-slate-100 leading-tight">{problem.title}</h1>
          <Badge color={diff.color} className="flex-shrink-0">{diff.label}</Badge>
        </div>
        <div className="flex items-center gap-4 text-xs text-slate-500">
          <span className="flex items-center gap-1">
            <Clock className="h-3.5 w-3.5" />
            {problem.time_limit_seconds}s
          </span>
          <span className="flex items-center gap-1">
            <Cpu className="h-3.5 w-3.5" />
            {problem.memory_limit_mb} MB
          </span>
        </div>
      </div>

      {/* Description */}
      <Section title="Description">
        <p className="text-sm text-slate-300 leading-relaxed whitespace-pre-wrap">
          {problem.description}
        </p>
      </Section>

      {/* Input / Output format */}
      {problem.input_format && (
        <Section title="Input Format">
          <p className="text-sm text-slate-400 leading-relaxed">{problem.input_format}</p>
        </Section>
      )}
      {problem.output_format && (
        <Section title="Output Format">
          <p className="text-sm text-slate-400 leading-relaxed">{problem.output_format}</p>
        </Section>
      )}

      {/* Constraints */}
      {problem.constraints.length > 0 && (
        <Section title="Constraints">
          <ul className="space-y-1">
            {problem.constraints.map((c, i) => (
              <li key={i} className="text-sm text-slate-400 flex items-start gap-2">
                <span className="text-brand-500 mt-0.5 flex-shrink-0">•</span>
                <code className="font-mono text-xs">{c}</code>
              </li>
            ))}
          </ul>
        </Section>
      )}

      {/* Examples */}
      {problem.examples.length > 0 && (
        <Section title={`Example${problem.examples.length > 1 ? 's' : ''}`}>
          <div className="space-y-4">
            {problem.examples.map((ex, i) => (
              <div key={i} className="space-y-2">
                {problem.examples.length > 1 && (
                  <p className="text-xs text-slate-500 font-medium">Example {i + 1}</p>
                )}
                <div>
                  <p className="text-xs text-slate-500 mb-1">Input:</p>
                  <CodeBlock>{ex.input}</CodeBlock>
                </div>
                <div>
                  <p className="text-xs text-slate-500 mb-1">Output:</p>
                  <CodeBlock>{ex.output}</CodeBlock>
                </div>
                {ex.explanation && (
                  <div className="flex items-start gap-2 text-xs text-slate-400">
                    <span className="text-brand-400 flex-shrink-0">Explanation:</span>
                    <span>{ex.explanation}</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        </Section>
      )}
    </div>
  )
}

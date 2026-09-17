import { useState } from 'react'
import { PlayCircle, Target, Brain, Clock, ChevronRight } from 'lucide-react'
import { clsx } from 'clsx'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Spinner } from '@/components/ui/Spinner'
import { DomainBadge } from '@/components/target-role/DomainBadge'
import { useTargetRoles } from '@/hooks/useTargetRoles'
import type { StartInterviewPayload } from '@/types'

const SESSION_TYPES = [
  { id: 'mixed',     label: 'Full Interview',   desc: 'Warm-up + Technical + Project + HR', emoji: '🎯', recommended: true },
  { id: 'technical', label: 'Technical Only',   desc: 'DSA, System Design, Concepts',       emoji: '💻' },
  { id: 'hr',        label: 'HR / Behavioural', desc: 'Soft skills, scenarios, goals',       emoji: '🤝' },
  { id: 'project',   label: 'Project Focus',    desc: 'Deep dive into your projects',        emoji: '🛠️' },
  { id: 'coding',    label: 'Coding Round',     desc: 'Algorithm and problem solving',       emoji: '⌨️' },
] as const

const DIFFICULTIES = [
  { id: 'beginner',     label: 'Beginner',     desc: 'Fresher / Entry level',      color: 'text-emerald-400' },
  { id: 'intermediate', label: 'Intermediate', desc: 'Internship / 0–1 years',     color: 'text-amber-400' },
  { id: 'advanced',     label: 'Advanced',     desc: 'Campus placement / 1+ years', color: 'text-red-400' },
] as const

interface SessionSetupProps {
  onStart: (payload: StartInterviewPayload) => void
  isLoading: boolean
}

export function SessionSetup({ onStart, isLoading }: SessionSetupProps) {
  const [sessionType, setSessionType] = useState<StartInterviewPayload['session_type']>('mixed')
  const [difficulty, setDifficulty]   = useState<StartInterviewPayload['difficulty']>('intermediate')
  const [roleId, setRoleId]           = useState<string | undefined>(undefined)

  const { data: roles = [], isLoading: rolesLoading } = useTargetRoles()

  const handleStart = () => {
    onStart({ session_type: sessionType, difficulty, target_role_id: roleId })
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6 animate-slide-up">
      {/* Header */}
      <div className="text-center space-y-2">
        <div className="flex justify-center">
          <div className="h-14 w-14 rounded-2xl bg-brand-600/20 border border-brand-500/30 flex items-center justify-center">
            <Brain className="h-7 w-7 text-brand-400" />
          </div>
        </div>
        <h1 className="text-2xl font-bold text-slate-100">Start AI Interview</h1>
        <p className="text-slate-400 text-sm">
          Configure your session and the AI will conduct a personalised adaptive interview.
        </p>
      </div>

      {/* Session type */}
      <Card className="p-5">
        <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-3">
          Interview Type
        </h2>
        <div className="space-y-2">
          {SESSION_TYPES.map(type => (
            <button
              key={type.id}
              onClick={() => setSessionType(type.id)}
              className={clsx(
                'w-full flex items-center gap-3 p-3.5 rounded-xl border text-left transition-all duration-150',
                sessionType === type.id
                  ? 'bg-brand-600/15 border-brand-500/40 ring-1 ring-brand-500/20'
                  : 'bg-surface border-surface-border hover:bg-surface-hover hover:border-slate-500',
              )}
            >
              <span className="text-xl">{type.emoji}</span>
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-slate-200">{type.label}</span>
                  {(type as any).recommended && (
                    <span className="px-1.5 py-0.5 rounded-full text-xs bg-brand-500/15 text-brand-300 border border-brand-500/20">
                      Recommended
                    </span>
                  )}
                </div>
                <p className="text-xs text-slate-500 mt-0.5">{type.desc}</p>
              </div>
              {sessionType === type.id && (
                <ChevronRight className="h-4 w-4 text-brand-400 flex-shrink-0" />
              )}
            </button>
          ))}
        </div>
      </Card>

      {/* Difficulty */}
      <Card className="p-5">
        <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-3">
          Difficulty Level
        </h2>
        <div className="grid grid-cols-3 gap-2">
          {DIFFICULTIES.map(diff => (
            <button
              key={diff.id}
              onClick={() => setDifficulty(diff.id)}
              className={clsx(
                'flex flex-col items-center gap-1 p-3.5 rounded-xl border text-center transition-all duration-150',
                difficulty === diff.id
                  ? 'bg-brand-600/15 border-brand-500/40 ring-1 ring-brand-500/20'
                  : 'bg-surface border-surface-border hover:bg-surface-hover',
              )}
            >
              <span className={clsx('text-sm font-semibold', diff.color)}>{diff.label}</span>
              <span className="text-xs text-slate-500">{diff.desc}</span>
            </button>
          ))}
        </div>
      </Card>

      {/* Target role */}
      <Card className="p-5">
        <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-3 flex items-center gap-2">
          <Target className="h-4 w-4 text-brand-400" />
          Target Role
        </h2>
        {rolesLoading ? (
          <div className="flex justify-center py-4"><Spinner size="sm" /></div>
        ) : roles.length === 0 ? (
          <p className="text-sm text-slate-500 text-center py-3">
            No target roles set. The AI will ask general questions.{' '}
            <a href="/target-roles" className="text-brand-400 hover:text-brand-300">Add a role →</a>
          </p>
        ) : (
          <div className="space-y-2">
            <button
              onClick={() => setRoleId(undefined)}
              className={clsx(
                'w-full flex items-center gap-3 p-3 rounded-xl border text-left transition-all',
                !roleId
                  ? 'bg-brand-600/15 border-brand-500/40'
                  : 'bg-surface border-surface-border hover:bg-surface-hover',
              )}
            >
              <span className="text-sm text-slate-400">Auto (use primary role)</span>
            </button>
            {roles.map(role => (
              <button
                key={role.id}
                onClick={() => setRoleId(role.id)}
                className={clsx(
                  'w-full flex items-center gap-3 p-3 rounded-xl border text-left transition-all',
                  roleId === role.id
                    ? 'bg-brand-600/15 border-brand-500/40'
                    : 'bg-surface border-surface-border hover:bg-surface-hover',
                )}
              >
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-slate-200">{role.role_name}</span>
                    {role.is_primary && (
                      <span className="text-xs text-brand-400">Primary</span>
                    )}
                  </div>
                </div>
                <DomainBadge domain={role.domain} />
              </button>
            ))}
          </div>
        )}
      </Card>

      {/* Duration hint */}
      <div className="flex items-center gap-2 px-4 py-3 rounded-xl bg-surface border border-surface-border text-xs text-slate-500">
        <Clock className="h-4 w-4 flex-shrink-0 text-brand-400" />
        <span>
          Estimated duration: {sessionType === 'mixed' ? '25–35' : '15–20'} minutes ·
          The AI adapts question difficulty based on your responses.
        </span>
      </div>

      {/* Start button */}
      <Button
        onClick={handleStart}
        loading={isLoading}
        className="w-full"
        icon={<PlayCircle className="h-5 w-5" />}
      >
        Start Interview
      </Button>
    </div>
  )
}

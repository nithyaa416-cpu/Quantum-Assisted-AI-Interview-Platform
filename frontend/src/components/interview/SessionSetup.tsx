import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import {
  PlayCircle, Target, Brain, Clock, ChevronRight,
  FileText, Sparkles, CheckCircle2, Upload, Briefcase,
} from 'lucide-react'
import { clsx } from 'clsx'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { Spinner } from '@/components/ui/Spinner'
import { useResumes } from '@/hooks/useResumes'
import type { StartInterviewPayload } from '@/types'

const SESSION_TYPES = [
  { id: 'mixed',     label: 'Full Interview',   desc: 'Warm-up → Technical → Coding → Project → HR → Closing', emoji: '🎯', recommended: true },
  { id: 'technical', label: 'Technical Only',   desc: 'DSA, System Design, Concepts',                          emoji: '💻' },
  { id: 'hr',        label: 'HR / Behavioural', desc: 'Soft skills, scenarios, goals',                         emoji: '🤝' },
  { id: 'project',   label: 'Project Focus',    desc: 'Deep dive into your projects',                          emoji: '🛠️' },
  { id: 'coding',    label: 'Coding Round',     desc: 'Coding problems + explanation follow-up (no HR)',       emoji: '⌨️' },
] as const


const DIFFICULTIES = [
  { id: 'beginner',     label: 'Beginner',     desc: 'Fresher / Entry level',      color: 'text-emerald-400' },
  { id: 'intermediate', label: 'Intermediate', desc: 'Internship / 0–1 years',     color: 'text-amber-400' },
  { id: 'advanced',     label: 'Advanced',     desc: 'Campus placement / 1+ years', color: 'text-red-400' },
] as const

export const DURATION_OPTIONS = [
  {
    minutes: 20,
    title: '20 Minutes',
    badge: 'Fresher / Fast Track',
    badgeClass: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
    desc: 'Targeted screening focusing on foundational knowledge, basic syntax, and crisp problem solving.',
    expLevel: 'Recommended for Freshers & Entry-Level Graduates',
  },
  {
    minutes: 25,
    title: '25 Minutes',
    badge: 'Intermediate (Standard)',
    badgeClass: 'bg-brand-500/15 text-brand-300 border-brand-500/30',
    desc: 'Balanced 1-on-1 industry format with deep technical questioning, live problem solving, and behavioral checks.',
    expLevel: 'Recommended for 1–3 Years Experience (Standard Industry Pace)',
    recommended: true,
  },
  {
    minutes: 30,
    title: '30 Minutes',
    badge: 'Senior / Deep-Dive',
    badgeClass: 'bg-purple-500/15 text-purple-300 border-purple-500/30',
    desc: 'Exhaustive technical assessment covering architecture trade-offs, edge cases, project deep-dive, and leadership.',
    expLevel: 'Recommended for Senior Engineers & Thorough Evaluations',
  },
] as const

const POPULAR_ROLES = [
  'Full Stack Developer',
  'Frontend Engineer',
  'Backend Developer',
  'Product Manager',
  'Data Scientist / ML',
  'Data Analyst',
  'UI/UX Designer',
  'DevOps & Cloud Engineer',
  'Business Analyst',
  'Marketing Specialist',
]

interface SessionSetupProps {
  onStart: (payload: StartInterviewPayload) => void
  isLoading: boolean
}

export function SessionSetup({ onStart, isLoading }: SessionSetupProps) {
  const [sessionType, setSessionType]       = useState<StartInterviewPayload['session_type']>('mixed')
  const [difficulty, setDifficulty]         = useState<StartInterviewPayload['difficulty']>('intermediate')
  const [durationMinutes, setDurationMinutes] = useState<number>(25)
  const [targetRole, setTargetRole]         = useState('Full Stack Developer')
  const [jobDescription, setJobDescription] = useState('')
  const [selectedResumeId, setSelectedResumeId] = useState<string | undefined>(undefined)

  const { data: resumes = [], isLoading: resumesLoading } = useResumes()

  // Default to the first available parsed resume
  useEffect(() => {
    if (resumes.length > 0 && selectedResumeId === undefined) {
      const activeOrFirst = resumes.find(r => r.is_active) || resumes[0]
      setSelectedResumeId(activeOrFirst.id)
    }
  }, [resumes, selectedResumeId])

  const handleStart = () => {
    onStart({
      session_type: sessionType,
      difficulty,
      duration_minutes: durationMinutes,
      target_role_name: targetRole.trim() || undefined,
      job_description: jobDescription.trim() || undefined,
      resume_id: selectedResumeId,
    })
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6 animate-slide-up pb-12">
      {/* Header */}
      <div className="text-center space-y-2">
        <div className="flex justify-center">
          <div className="h-14 w-14 rounded-2xl bg-brand-600/20 border border-brand-500/30 flex items-center justify-center">
            <Brain className="h-7 w-7 text-brand-400" />
          </div>
        </div>
        <h1 className="text-2xl font-bold text-slate-100">Start AI Interview</h1>
        <p className="text-slate-400 text-sm">
          Set your target role, paste the job description, and the AI will conduct a personalised interview.
        </p>
      </div>

      {/* Target Role & Job Description */}
      <Card className="p-5 space-y-4">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <Target className="h-4 w-4 text-brand-400" />
            <h2 className="text-sm font-semibold text-slate-200 uppercase tracking-wider">
              Target Role
            </h2>
          </div>
          <p className="text-xs text-slate-400 mb-3">
            Choose a quick role or type the exact job position you're interviewing for.
          </p>

          {/* Quick role pills */}
          <div className="flex flex-wrap gap-1.5 mb-3">
            {POPULAR_ROLES.map((r) => (
              <button
                key={r}
                type="button"
                onClick={() => setTargetRole(r)}
                className={clsx(
                  'px-2.5 py-1 rounded-lg text-xs font-medium transition-all',
                  targetRole === r
                    ? 'bg-brand-600 text-white shadow-sm'
                    : 'bg-surface-hover text-slate-300 hover:text-slate-100 hover:bg-slate-700/60'
                )}
              >
                {r}
              </button>
            ))}
          </div>

          <div className="relative">
            <Briefcase className="h-4 w-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
            <input
              type="text"
              value={targetRole}
              onChange={(e) => setTargetRole(e.target.value)}
              placeholder="e.g. Senior Backend Engineer - Python"
              className="input-base pl-10 w-full"
            />
          </div>
        </div>

        {/* Job Description text area */}
        <div className="pt-2 border-t border-surface-border">
          <div className="flex items-center justify-between mb-1.5">
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-amber-400" />
              <label className="text-sm font-semibold text-slate-200">
                Job Description (JD)
              </label>
            </div>
            <span className="text-xs text-slate-500">Optional · Highly Recommended</span>
          </div>
          <textarea
            rows={4}
            value={jobDescription}
            onChange={(e) => setJobDescription(e.target.value)}
            placeholder="Paste the job requirements, responsibilities, or tech stack here from LinkedIn/Indeed to tailor the interview to this exact opening..."
            className="input-base w-full text-sm font-normal py-2.5 resize-y"
          />
          <p className="text-xs text-slate-500 mt-1.5">
            The AI interviewer will analyze this JD to challenge you on the job's required technologies and responsibilities.
          </p>
        </div>
      </Card>

      {/* Resume Selection */}
      <Card className="p-5">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <FileText className="h-4 w-4 text-brand-400" />
            <h2 className="text-sm font-semibold text-slate-200 uppercase tracking-wider">
              Select Resume
            </h2>
          </div>
          <Link
            to="/resumes"
            className="text-xs text-brand-400 hover:text-brand-300 flex items-center gap-1 transition-colors"
          >
            <Upload className="h-3 w-3" /> Manage Resumes
          </Link>
        </div>

        {resumesLoading ? (
          <div className="flex justify-center py-4"><Spinner size="sm" /></div>
        ) : resumes.length === 0 ? (
          <div className="p-4 rounded-xl bg-surface border border-surface-border text-center space-y-2">
            <p className="text-xs text-slate-400">
              No resumes uploaded yet. The interview can proceed with general questions, or you can upload your resume.
            </p>
            <Link
              to="/resumes"
              className="inline-flex items-center gap-1 text-xs text-brand-400 hover:text-brand-300 font-medium"
            >
              Upload a resume now →
            </Link>
          </div>
        ) : (
          <div className="space-y-2">
            {resumes.map((resume) => {
              const isSelected = selectedResumeId === resume.id
              return (
                <button
                  key={resume.id}
                  type="button"
                  onClick={() => setSelectedResumeId(resume.id)}
                  className={clsx(
                    'w-full flex items-center justify-between p-3 rounded-xl border text-left transition-all',
                    isSelected
                      ? 'bg-brand-600/15 border-brand-500/40 ring-1 ring-brand-500/20'
                      : 'bg-surface border-surface-border hover:bg-surface-hover hover:border-slate-500'
                  )}
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="p-2 rounded-lg bg-surface-card flex-shrink-0">
                      <FileText className="h-4 w-4 text-brand-400" />
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-sm font-medium text-slate-200 truncate max-w-[240px]">
                          {resume.original_filename}
                        </span>
                        <Badge color="slate">v{resume.version}</Badge>
                      </div>
                      <p className="text-xs text-slate-500 mt-0.5">
                        {resume.is_parsed
                          ? `${resume.skills_count} skills extracted`
                          : resume.parse_status}
                      </p>
                    </div>
                  </div>
                  {isSelected && (
                    <CheckCircle2 className="h-4 w-4 text-brand-400 flex-shrink-0" />
                  )}
                </button>
              )
            })}

            {/* Option to proceed without resume */}
            <button
              type="button"
              onClick={() => setSelectedResumeId(undefined)}
              className={clsx(
                'w-full flex items-center justify-between p-2.5 rounded-xl border text-left transition-all text-xs',
                selectedResumeId === undefined
                  ? 'bg-brand-600/15 border-brand-500/40 text-slate-300'
                  : 'bg-surface border-surface-border hover:bg-surface-hover text-slate-500'
              )}
            >
              <span>General interview without specific resume</span>
              {selectedResumeId === undefined && (
                <CheckCircle2 className="h-3.5 w-3.5 text-brand-400" />
              )}
            </button>
          </div>
        )}
      </Card>

      {/* Session type */}
      <Card className="p-5">
        <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-3">
          Interview Round Type
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

      {/* Interview Duration Selection */}
      <Card className="p-5 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Clock className="h-4 w-4 text-brand-400" />
            <h2 className="text-sm font-semibold text-slate-200 uppercase tracking-wider">
              Interview Duration & Pacing
            </h2>
          </div>
          <span className="text-xs text-brand-400 font-medium">
            {durationMinutes} Minutes Selected
          </span>
        </div>
        <p className="text-xs text-slate-400">
          The AI pacing engine dynamically adjusts question depth, live follow-ups, and transition speed based on your selected duration.
        </p>

        <div className="space-y-2.5 pt-1">
          {DURATION_OPTIONS.map((opt) => {
            const isSelected = durationMinutes === opt.minutes
            return (
              <button
                key={opt.minutes}
                type="button"
                onClick={() => setDurationMinutes(opt.minutes)}
                className={clsx(
                  'w-full flex items-start justify-between p-3.5 rounded-xl border text-left transition-all duration-150',
                  isSelected
                    ? 'bg-brand-600/15 border-brand-500/50 ring-1 ring-brand-500/30'
                    : 'bg-surface border-surface-border hover:bg-surface-hover hover:border-slate-600'
                )}
              >
                <div className="space-y-1 pr-3">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-sm font-bold text-slate-100">
                      {opt.title}
                    </span>
                    <span
                      className={clsx(
                        'px-2 py-0.5 rounded-full text-[11px] font-semibold border',
                        opt.badgeClass
                      )}
                    >
                      {opt.badge}
                    </span>
                    {(opt as any).recommended && (
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-brand-500/20 text-brand-300 border border-brand-500/30">
                        Default Recommended
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-slate-400 leading-relaxed">
                    {opt.desc}
                  </p>
                  <p className="text-[11px] text-slate-500 font-medium flex items-center gap-1.5 pt-0.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-brand-400/80" />
                    {opt.expLevel}
                  </p>
                </div>
                <div className="pt-0.5 flex-shrink-0">
                  <div
                    className={clsx(
                      'w-5 h-5 rounded-full border flex items-center justify-center transition-all',
                      isSelected
                        ? 'border-brand-400 bg-brand-500/20 text-brand-300'
                        : 'border-slate-600 bg-slate-800/50'
                    )}
                  >
                    {isSelected && <CheckCircle2 className="w-4 h-4 text-brand-400" />}
                  </div>
                </div>
              </button>
            )
          })}
        </div>
      </Card>

      {/* Duration hint */}
      <div className="flex items-center gap-2 px-4 py-3 rounded-xl bg-surface border border-surface-border text-xs text-slate-400">
        <Clock className="h-4 w-4 flex-shrink-0 text-brand-400" />
        <span>
          Selected: <strong className="text-slate-200">{durationMinutes} minutes</strong> · {sessionType === 'mixed' ? 'Full 6-phase simulated panel' : `${sessionType.toUpperCase()} specialized round`} · Real-time AI adapts question difficulty and follow-ups.
        </span>
      </div>

      {/* Start button */}
      <Button
        onClick={handleStart}
        loading={isLoading}
        className="w-full py-3 text-base"
        icon={<PlayCircle className="h-5 w-5" />}
      >
        Continue to Hardware & Biometric Verification
      </Button>
    </div>
  )
}

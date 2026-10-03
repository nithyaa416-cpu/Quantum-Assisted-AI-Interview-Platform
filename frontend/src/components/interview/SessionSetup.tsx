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

const POPULAR_ROLES = [
  'Full Stack Developer',
  'Frontend Engineer',
  'Backend Developer',
  'Data Scientist / ML',
  'DevOps & Cloud Engineer',
  'Software Engineer',
]

interface SessionSetupProps {
  onStart: (payload: StartInterviewPayload) => void
  isLoading: boolean
}

export function SessionSetup({ onStart, isLoading }: SessionSetupProps) {
  const [sessionType, setSessionType]       = useState<StartInterviewPayload['session_type']>('mixed')
  const [difficulty, setDifficulty]         = useState<StartInterviewPayload['difficulty']>('intermediate')
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
        className="w-full py-3 text-base"
        icon={<PlayCircle className="h-5 w-5" />}
      >
        Start AI Interview
      </Button>
    </div>
  )
}

import { Link } from 'react-router-dom'
import {
  PlayCircle, FileText, Brain, TrendingUp,
  Clock, CheckCircle2, AlertCircle, ArrowRight,
  Sparkles, Target,
} from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import { useProfile } from '@/hooks/useProfile'
import { useSessions, useAssessments } from '@/hooks/useSessions'
import { Card, StatCard } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { ScoreRing } from '@/components/ui/ScoreRing'
import { EmptyState } from '@/components/ui/EmptyState'
import { Spinner } from '@/components/ui/Spinner'
import type { SessionSummary, Assessment } from '@/types'

// ── helpers ──────────────────────────────────────────────────────────────────
function statusBadge(status: string) {
  const map: Record<string, { color: 'green' | 'indigo' | 'yellow' | 'slate'; label: string }> = {
    completed: { color: 'green',  label: 'Completed' },
    active:    { color: 'indigo', label: 'In Progress' },
    created:   { color: 'yellow', label: 'Not Started' },
    aborted:   { color: 'slate',  label: 'Aborted' },
  }
  const m = map[status] ?? { color: 'slate', label: status }
  return <Badge color={m.color}>{m.label}</Badge>
}

function typeBadge(type: string) {
  const colors: Record<string, 'indigo' | 'purple' | 'green' | 'yellow' | 'slate'> = {
    technical: 'indigo', hr: 'green', coding: 'purple',
    project: 'yellow', mixed: 'slate',
  }
  return <Badge color={colors[type] ?? 'slate'}>{type}</Badge>
}

function formatDuration(secs: number | null) {
  if (!secs) return '—'
  const m = Math.floor(secs / 60)
  const s = secs % 60
  return `${m}m ${s}s`
}

function timeAgo(dateStr: string) {
  const diff = Date.now() - new Date(dateStr).getTime()
  const d = Math.floor(diff / 86400000)
  if (d === 0) return 'Today'
  if (d === 1) return 'Yesterday'
  if (d < 7)  return `${d} days ago`
  return new Date(dateStr).toLocaleDateString()
}

// ── sub-components ────────────────────────────────────────────────────────────

function QuickActions() {
  return (
    <Card className="p-6">
      <div className="flex items-center gap-2 mb-5">
        <Sparkles className="h-5 w-5 text-brand-400" />
        <h2 className="section-title text-base">Quick Actions</h2>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {[
          {
            icon: <PlayCircle className="h-5 w-5" />,
            title: 'Start Interview',
            desc: 'Begin a new AI-powered interview session',
            to: '/interview/new',
            primary: true,
          },
          {
            icon: <FileText className="h-5 w-5" />,
            title: 'Upload Resume',
            desc: 'Let AI extract your skills and projects',
            to: '/resumes',
            primary: false,
          },
          {
            icon: <Brain className="h-5 w-5" />,
            title: 'View Prep Plan',
            desc: 'See your quantum-optimised study roadmap',
            to: '/preparation',
            primary: false,
          },
          {
            icon: <Target className="h-5 w-5" />,
            title: 'Set Target Role',
            desc: 'Configure your placement goal',
            to: '/profile',
            primary: false,
          },
        ].map((action) => (
          <Link
            key={action.title}
            to={action.to}
            className={`flex items-start gap-3 p-4 rounded-xl border transition-all duration-200 group ${
              action.primary
                ? 'bg-brand-600/10 border-brand-500/30 hover:bg-brand-600/20 hover:border-brand-500/50'
                : 'bg-surface border-surface-border hover:bg-surface-hover hover:border-slate-500'
            }`}
          >
            <span className={`mt-0.5 ${action.primary ? 'text-brand-400' : 'text-slate-400 group-hover:text-slate-200'}`}>
              {action.icon}
            </span>
            <div>
              <p className={`text-sm font-semibold ${action.primary ? 'text-brand-300' : 'text-slate-200'}`}>
                {action.title}
              </p>
              <p className="text-xs text-slate-500 mt-0.5">{action.desc}</p>
            </div>
          </Link>
        ))}
      </div>
    </Card>
  )
}

function RecentSessions({ sessions, loading }: { sessions: SessionSummary[]; loading: boolean }) {
  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-5">
        <h2 className="section-title text-base">Recent Sessions</h2>
        <Link to="/sessions" className="text-xs text-brand-400 hover:text-brand-300 flex items-center gap-1">
          View all <ArrowRight className="h-3 w-3" />
        </Link>
      </div>

      {loading ? (
        <div className="flex justify-center py-8"><Spinner /></div>
      ) : sessions.length === 0 ? (
        <EmptyState
          title="No sessions yet"
          description="Start your first interview session to track your progress."
          icon={<PlayCircle className="h-7 w-7" />}
        />
      ) : (
        <div className="space-y-3">
          {sessions.slice(0, 5).map((s) => (
            <div
              key={s.id}
              className="flex items-center justify-between p-3 rounded-xl bg-surface hover:bg-surface-hover transition-colors"
            >
              <div className="flex items-center gap-3 min-w-0">
                <div className="p-2 rounded-lg bg-surface-hover flex-shrink-0">
                  <PlayCircle className="h-4 w-4 text-brand-400" />
                </div>
                <div className="min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    {typeBadge(s.session_type)}
                    {statusBadge(s.status)}
                  </div>
                  <div className="flex items-center gap-3 mt-1">
                    {s.target_role_name && (
                      <span className="text-xs text-slate-400 truncate">{s.target_role_name}</span>
                    )}
                    <span className="text-xs text-slate-600 flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {formatDuration(s.duration_seconds)}
                    </span>
                  </div>
                </div>
              </div>
              <span className="text-xs text-slate-500 flex-shrink-0 ml-2">{timeAgo(s.created_at)}</span>
            </div>
          ))}
        </div>
      )}
    </Card>
  )
}

function PerformanceSnapshot({ assessments, loading }: { assessments: Assessment[]; loading: boolean }) {
  if (loading) return <div className="flex justify-center py-8"><Spinner /></div>
  if (assessments.length === 0) {
    return (
      <Card className="p-6">
        <h2 className="section-title text-base mb-5">Performance Snapshot</h2>
        <EmptyState
          title="No assessments yet"
          description="Complete an interview to see your performance breakdown."
          icon={<TrendingUp className="h-7 w-7" />}
        />
      </Card>
    )
  }

  const latest = assessments[0]
  const dims = [
    { label: 'Technical',      score: latest.technical_score,      color: '#6366f1' },
    { label: 'Communication',  score: latest.communication_score,  color: '#8b5cf6' },
    { label: 'Behavioural',    score: latest.behavioural_score ?? 0, color: '#06b6d4' },
    { label: 'Coding',         score: latest.coding_score ?? 0,    color: '#10b981' },
    { label: 'Problem Solving',score: latest.problem_solving_score, color: '#f59e0b' },
  ]

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-5">
        <h2 className="section-title text-base">Latest Performance</h2>
        <span className="text-xs text-slate-500">{timeAgo(latest.generated_at)}</span>
      </div>

      <div className="flex items-center gap-6 mb-6">
        <ScoreRing score={Number(latest.overall_score)} size={88} label="Overall" />
        <div className="flex-1 min-w-0">
          <p className="text-2xl font-bold text-slate-100">
            {Math.round(Number(latest.overall_score) * 100)}
            <span className="text-sm text-slate-500 font-normal">/100</span>
          </p>
          <p className="text-sm text-slate-400 mt-1">Overall Score</p>
          {latest.strengths.length > 0 && (
            <div className="flex items-start gap-1.5 mt-2">
              <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400 mt-0.5 flex-shrink-0" />
              <p className="text-xs text-emerald-400">{latest.strengths[0]}</p>
            </div>
          )}
          {latest.improvement_areas.length > 0 && (
            <div className="flex items-start gap-1.5 mt-1">
              <AlertCircle className="h-3.5 w-3.5 text-amber-400 mt-0.5 flex-shrink-0" />
              <p className="text-xs text-amber-400">{latest.improvement_areas[0]?.area}</p>
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-5 gap-2">
        {dims.map((d) => (
          <ScoreRing key={d.label} score={Number(d.score)} size={52} label={d.label.split(' ')[0]} color={d.color} />
        ))}
      </div>
    </Card>
  )
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function DashboardPage() {
  const user = useAuthStore((s) => s.user)
  const { data: profile } = useProfile()
  const { data: sessions = [], isLoading: sessLoading } = useSessions()
  const { data: assessments = [], isLoading: assLoading } = useAssessments()

  const completedSessions = sessions.filter((s) => s.status === 'completed').length
  const avgScore = assessments.length
    ? Math.round(assessments.reduce((acc, a) => acc + Number(a.overall_score), 0) / assessments.length * 100)
    : null

  const hour = new Date().getHours()
  const greeting = hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening'
  const firstName = user?.full_name.split(' ')[0] ?? 'Student'

  return (
    <div className="max-w-6xl mx-auto space-y-6 animate-slide-up">
      {/* Welcome banner */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">
            {greeting}, {firstName} 👋
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            {profile?.college
              ? `${profile.college} · `
              : ''}
            {sessions.length > 0
              ? `${completedSessions} session${completedSessions !== 1 ? 's' : ''} completed`
              : 'No sessions yet — start your first interview!'}
          </p>
        </div>
        <Link to="/interview/new">
          <Button icon={<PlayCircle className="h-4 w-4" />}>
            Start Interview
          </Button>
        </Link>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Sessions"
          value={sessions.length}
          sub={`${completedSessions} completed`}
          icon={<PlayCircle className="h-5 w-5" />}
        />
        <StatCard
          label="Avg Score"
          value={avgScore !== null ? `${avgScore}%` : '—'}
          sub={avgScore !== null ? 'Across all sessions' : 'Complete a session first'}
          icon={<TrendingUp className="h-5 w-5" />}
          trend={avgScore !== null ? (avgScore >= 70 ? 'up' : 'down') : 'neutral'}
        />
        <StatCard
          label="Skills"
          value={profile?.skills.length ?? 0}
          sub="Extracted from resume"
          icon={<CheckCircle2 className="h-5 w-5" />}
        />
        <StatCard
          label="Target Roles"
          value={profile?.target_roles.length ?? 0}
          sub="Configured in profile"
          icon={<Target className="h-5 w-5" />}
        />
      </div>

      {/* Main grid */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <QuickActions />
        <PerformanceSnapshot assessments={assessments} loading={assLoading} />
      </div>

      {/* Recent sessions */}
      <RecentSessions sessions={sessions} loading={sessLoading} />
    </div>
  )
}

import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  MessageSquare, Play, CheckCircle2, Clock,
  Search, Filter, ChevronRight, RotateCcw, ListFilter,
  Award, BarChart3, HelpCircle
} from 'lucide-react'
import { useInterviewSessions } from '@/hooks/useInterview'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Spinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import type { InterviewListItem } from '@/types'

export default function SessionsPage() {
  const navigate = useNavigate()
  const { data: sessions, isLoading, refetch } = useInterviewSessions()

  const [statusFilter, setStatusFilter] = useState<'all' | 'completed' | 'active'>('all')
  const [searchQuery, setSearchQuery] = useState('')

  const sessionList: InterviewListItem[] = sessions || []

  // Filtered sessions
  const filteredSessions = sessionList.filter((s) => {
    const matchesStatus =
      statusFilter === 'all'
        ? true
        : statusFilter === 'completed'
        ? s.status === 'completed'
        : s.status === 'active' || s.status === 'in_progress'

    const matchesSearch =
      (s.target_role || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
      (s.session_type || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
      (s.difficulty || '').toLowerCase().includes(searchQuery.toLowerCase())

    return matchesStatus && matchesSearch
  })

  // Summary statistics
  const totalSessions = sessionList.length
  const completedSessions = sessionList.filter((s) => s.status === 'completed')
  const totalAnswered = sessionList.reduce((acc, s) => acc + (s.answered_count || 0), 0)

  const scoredSessions = completedSessions.filter((s) => s.avg_score != null)
  const avgOverallScore = scoredSessions.length
    ? Math.round(
        scoredSessions.reduce((acc, s) => acc + (s.avg_score || 0), 0) / scoredSessions.length * 10
      )
    : null

  const formatDuration = (seconds?: number | null) => {
    if (!seconds) return '—'
    const m = Math.floor(seconds / 60)
    const s = seconds % 60
    return `${m}m ${s}s`
  }

  const formatDate = (isoString?: string | null) => {
    if (!isoString) return '—'
    try {
      const d = new Date(isoString)
      return d.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
    } catch {
      return isoString
    }
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6 animate-fade-in pb-12">
      {/* 1. Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-100 flex items-center gap-2.5">
            <MessageSquare className="h-7 w-7 text-brand-400" />
            Interview Sessions
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Track your completed mock interviews, review verbal transcripts, and view AI feedback.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => refetch()}
            icon={<RotateCcw className="h-4 w-4" />}
          >
            Refresh
          </Button>
          <Button
            onClick={() => navigate('/interview/new')}
            icon={<Play className="h-4 w-4" />}
            className="bg-brand-600 hover:bg-brand-500 font-semibold"
          >
            Start New Interview
          </Button>
        </div>
      </div>

      {/* 2. Metrics Overview Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-4 bg-slate-900/60 border-slate-800">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Total Interviews</span>
            <div className="p-2 rounded-lg bg-brand-500/10 text-brand-400">
              <MessageSquare className="h-4 w-4" />
            </div>
          </div>
          <p className="text-2xl font-bold text-slate-100 mt-2">{totalSessions}</p>
          <p className="text-[11px] text-slate-500 mt-0.5">{completedSessions.length} completed</p>
        </Card>

        <Card className="p-4 bg-slate-900/60 border-slate-800">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Avg AI Score</span>
            <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400">
              <Award className="h-4 w-4" />
            </div>
          </div>
          <p className="text-2xl font-bold text-slate-100 mt-2">
            {avgOverallScore != null ? `${avgOverallScore}%` : '—'}
          </p>
          <p className="text-[11px] text-slate-500 mt-0.5">Across completed sessions</p>
        </Card>

        <Card className="p-4 bg-slate-900/60 border-slate-800">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Questions Answered</span>
            <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400">
              <CheckCircle2 className="h-4 w-4" />
            </div>
          </div>
          <p className="text-2xl font-bold text-slate-100 mt-2">{totalAnswered}</p>
          <p className="text-[11px] text-slate-500 mt-0.5">Spoken verbal responses</p>
        </Card>

        <Card className="p-4 bg-slate-900/60 border-slate-800">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Completion Rate</span>
            <div className="p-2 rounded-lg bg-cyan-500/10 text-cyan-400">
              <BarChart3 className="h-4 w-4" />
            </div>
          </div>
          <p className="text-2xl font-bold text-slate-100 mt-2">
            {totalSessions > 0 ? `${Math.round((completedSessions.length / totalSessions) * 100)}%` : '0%'}
          </p>
          <p className="text-[11px] text-slate-500 mt-0.5">Finished through closing</p>
        </Card>
      </div>

      {/* 3. Search and Status Filters */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 bg-slate-900/80 p-3 rounded-2xl border border-slate-800">
        {/* Search */}
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by role (e.g. Full Stack Developer, Python)..."
            className="w-full bg-slate-950/70 border border-slate-800 rounded-xl pl-9 pr-4 py-2 text-xs sm:text-sm text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-brand-500/50"
          />
        </div>

        {/* Status Pills */}
        <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-xl border border-slate-800/80">
          {(['all', 'completed', 'active'] as const).map((filter) => (
            <button
              key={filter}
              type="button"
              onClick={() => setStatusFilter(filter)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium capitalize transition-all ${
                statusFilter === filter
                  ? 'bg-brand-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {filter === 'all' ? 'All Sessions' : filter}
            </button>
          ))}
        </div>
      </div>

      {/* 4. Session Cards List */}
      {isLoading ? (
        <div className="flex justify-center py-16">
          <Spinner size="lg" />
        </div>
      ) : filteredSessions.length === 0 ? (
        <EmptyState
          title={searchQuery ? 'No matching interview sessions' : 'No interview sessions yet'}
          description={
            searchQuery
              ? 'Try changing your search term or status filter.'
              : 'Begin your first AI-assisted mock interview to see your transcripts and evaluations.'
          }
          icon={<MessageSquare className="h-8 w-8 text-slate-500" />}
          action={
            <Button onClick={() => navigate('/interview/new')} icon={<Play className="h-4 w-4" />}>
              Start An Interview
            </Button>
          }
        />
      ) : (
        <div className="space-y-3.5">
          {filteredSessions.map((session) => {
            const isCompleted = session.status === 'completed'
            const scoreDisplay = session.avg_score != null ? `${Math.round(session.avg_score * 10)}%` : null

            return (
              <div
                key={session.id}
                className="group relative p-4 sm:p-5 rounded-2xl bg-slate-900/70 border border-slate-800 hover:border-brand-500/40 transition-all shadow-md hover:shadow-xl flex flex-col sm:flex-row sm:items-center justify-between gap-4"
              >
                {/* Left: Role and Metadata */}
                <div className="flex items-start gap-4 min-w-0">
                  <div
                    className={`h-11 w-11 rounded-xl flex items-center justify-center flex-shrink-0 ${
                      isCompleted
                        ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                        : 'bg-brand-500/10 text-brand-400 border border-brand-500/20'
                    }`}
                  >
                    {isCompleted ? <CheckCircle2 className="h-5 w-5" /> : <Play className="h-5 w-5" />}
                  </div>

                  <div className="space-y-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <h3 className="text-sm sm:text-base font-bold text-slate-100 truncate">
                        {session.target_role || 'Software Engineering'}
                      </h3>
                      <span
                        className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border ${
                          isCompleted
                            ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
                            : 'bg-amber-500/10 text-amber-300 border-amber-500/30'
                        }`}
                      >
                        {session.status}
                      </span>
                      <span className="text-[11px] font-medium px-2 py-0.5 rounded-full bg-slate-800 border border-slate-700 text-slate-300 capitalize">
                        {session.session_type}
                      </span>
                    </div>

                    <div className="flex items-center gap-3 text-xs text-slate-400 flex-wrap">
                      <span>{session.turn_count} questions</span>
                      <span>&bull;</span>
                      <span>{session.answered_count} answered</span>
                      <span>&bull;</span>
                      <span className="flex items-center gap-1">
                        <Clock className="h-3 w-3 text-slate-500" />
                        {formatDuration(session.duration_seconds)}
                      </span>
                      <span>&bull;</span>
                      <span>{formatDate(session.started_at || session.created_at)}</span>
                    </div>
                  </div>
                </div>

                {/* Right: Score and Action */}
                <div className="flex items-center justify-between sm:justify-end gap-4 border-t sm:border-t-0 pt-3 sm:pt-0 border-slate-800/80">
                  {scoreDisplay && (
                    <div className="text-right sm:pr-2">
                      <p className="text-xs text-slate-400">Score</p>
                      <p className="text-base font-extrabold text-emerald-400">{scoreDisplay}</p>
                    </div>
                  )}

                  {isCompleted ? (
                    <Link to={`/interview/history/${session.id}`}>
                      <Button
                        size="sm"
                        variant="secondary"
                        className="bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold"
                        icon={<ChevronRight className="h-3.5 w-3.5" />}
                      >
                        View Transcript &amp; Feedback
                      </Button>
                    </Link>
                  ) : (
                    <Link to={`/interview/${session.id}`}>
                      <Button
                        size="sm"
                        className="bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold"
                        icon={<Play className="h-3.5 w-3.5" />}
                      >
                        Resume Interview
                      </Button>
                    </Link>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

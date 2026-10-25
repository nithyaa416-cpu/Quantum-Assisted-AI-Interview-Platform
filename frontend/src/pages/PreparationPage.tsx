import { useState, useEffect, useMemo, useCallback } from 'react'
import {
  Brain,
  Zap,
  Clock,
  CheckCircle2,
  Circle,
  Sparkles,
  BarChart3,
  Calendar,
  Layers,
  ArrowRight,
  RefreshCw,
  Sliders,
  Check,
  AlertTriangle,
  X,
  BookOpen,
  Code2,
  ChevronRight,
  ChevronDown,
  Activity,
  Cpu,
  ExternalLink,
  GraduationCap,
  Play,
  FileText,
  Monitor,
} from 'lucide-react'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Spinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { preparationService } from '@/services/preparationService'
import { getResourcesForTopic, type LearningResource } from '@/data/learningResources'
import type {
  PreparationPlan,
  PracticeModule,
  FeedbackAnalysisData,
  GeneratePlanPayload,
  QuantumBenchmarkResult,
} from '@/types'

const PRIORITY_OPTIONS = [
  { id: 'coding', label: 'Data Structures & Algorithms' },
  { id: 'system_design', label: 'System Design & Architecture' },
  { id: 'concurrency', label: 'Concurrency & Multithreading' },
  { id: 'databases', label: 'Databases & Query Optimization' },
  { id: 'behavioral', label: 'Behavioral & Leadership' },
]

export default function PreparationPage() {
  const [loading, setLoading] = useState<boolean>(true)
  const [plan, setPlan] = useState<PreparationPlan | null>(null)
  const [feedback, setFeedback] = useState<FeedbackAnalysisData | null>(null)
  const [error, setError] = useState<string | null>(null)

  // Configuration drawer / modal state
  const [showConfig, setShowConfig] = useState<boolean>(false)
  const [generating, setGenerating] = useState<boolean>(false)
  const [daysRemaining, setDaysRemaining] = useState<number>(7)
  const [dailyHours, setDailyHours] = useState<number>(2.0)
  const [selectedPriorities, setSelectedPriorities] = useState<string[]>(['coding'])
  const [selectedAlgorithm, setSelectedAlgorithm] = useState<'qaoa' | 'classical'>('qaoa')

  // Selected Day tab in roadmap view
  const [activeDay, setActiveDay] = useState<number>(1)

  // Quantum Benchmark Modal state
  const [showBenchmark, setShowBenchmark] = useState<boolean>(false)
  const [benchmarkLoading, setBenchmarkLoading] = useState<boolean>(false)
  const [benchmarkQubits, setBenchmarkQubits] = useState<number>(6)
  const [benchmarkBudget, setBenchmarkBudget] = useState<number>(12.0)
  const [benchmarkResult, setBenchmarkResult] = useState<QuantumBenchmarkResult | null>(null)

  // Module updating status cache
  const [updatingModules, setUpdatingModules] = useState<Record<string, boolean>>({})

  // Collapsible state for Free Learning Resources per module (keyed by module.id)
  const [collapsedResources, setCollapsedResources] = useState<Record<string, boolean>>({})

  const toggleResourcesCollapse = (moduleId: string) => {
    setCollapsedResources((prev) => ({
      ...prev,
      [moduleId]: !prev[moduleId],
    }))
  }

  // Load initial active plan & feedback
  useEffect(() => {
    async function loadData() {
      setLoading(true)
      setError(null)
      try {
        const [activePlan, feedbackData] = await Promise.all([
          preparationService.getActivePlan(),
          preparationService.getFeedbackAnalysis(),
        ])
        setPlan(activePlan)
        setFeedback(feedbackData)
        if (activePlan) {
          setDaysRemaining(activePlan.preparation_days)
          setDailyHours(activePlan.daily_hours)
          if (activePlan.priority_areas?.length) {
            setSelectedPriorities(activePlan.priority_areas)
          }
        }
      } catch (err: any) {
        console.error('Error loading preparation data:', err)
        setError('Failed to load preparation roadmap. Please check your connection and refresh.')
      } finally {
        setLoading(false)
      }
    }
    loadData()
  }, [])

  // Days grouping for active plan
  const modulesByDay = useMemo(() => {
    if (!plan?.practice_modules) return {}
    const grouped: Record<number, PracticeModule[]> = {}
    for (const mod of plan.practice_modules) {
      if (!grouped[mod.scheduled_day]) {
        grouped[mod.scheduled_day] = []
      }
      grouped[mod.scheduled_day].push(mod)
    }
    return grouped
  }, [plan])

  const scheduledDaysList = useMemo(() => {
    const keys = Object.keys(modulesByDay).map(Number)
    return keys.sort((a, b) => a - b)
  }, [modulesByDay])

  // Progress metrics
  const progressStats = useMemo(() => {
    if (!plan?.practice_modules?.length) return { total: 0, completed: 0, percent: 0, hoursLeft: 0 }
    const total = plan.practice_modules.length
    const completed = plan.practice_modules.filter((m) => m.status === 'completed').length
    const percent = Math.round((completed / total) * 100)
    const hoursLeft = plan.practice_modules
      .filter((m) => m.status !== 'completed')
      .reduce((sum, m) => sum + Number(m.estimated_hours), 0)
    return { total, completed, percent, hoursLeft: Math.round(hoursLeft * 10) / 10 }
  }, [plan])

  // Toggle Module Status
  const handleToggleModule = async (module: PracticeModule) => {
    const nextStatus = module.status === 'completed' ? 'pending' : 'completed'
    setUpdatingModules((prev) => ({ ...prev, [module.id]: true }))

    // Optimistic UI update
    setPlan((prevPlan) => {
      if (!prevPlan) return prevPlan
      return {
        ...prevPlan,
        practice_modules: prevPlan.practice_modules.map((m) =>
          m.id === module.id
            ? { ...m, status: nextStatus, is_completed: nextStatus === 'completed' }
            : m
        ),
      }
    })

    try {
      await preparationService.updateModuleStatus(module.id, nextStatus)
    } catch (err) {
      console.error('Failed to update module status:', err)
      // Revert on failure
      setPlan((prevPlan) => {
        if (!prevPlan) return prevPlan
        return {
          ...prevPlan,
          practice_modules: prevPlan.practice_modules.map((m) =>
            m.id === module.id ? module : m
          ),
        }
      })
    } finally {
      setUpdatingModules((prev) => ({ ...prev, [module.id]: false }))
    }
  }

  // Generate / Regenerate Plan
  const handleGeneratePlan = async () => {
    setGenerating(true)
    setError(null)
    try {
      const payload: GeneratePlanPayload = {
        days_remaining: daysRemaining,
        daily_hours: dailyHours,
        total_hours_budget: Math.round(daysRemaining * dailyHours * 10) / 10,
        priority_areas: selectedPriorities,
        force_algorithm: selectedAlgorithm,
      }
      const newPlan = await preparationService.generatePlan(payload)
      setPlan(newPlan)
      setShowConfig(false)
      setActiveDay(1)
    } catch (err: any) {
      console.error('Failed to generate plan:', err)
      setError(err?.response?.data?.error?.message || 'Error executing QAOA optimization.')
    } finally {
      setGenerating(false)
    }
  }

  // Trigger Quantum Benchmark
  const handleRunBenchmark = async () => {
    setBenchmarkLoading(true)
    try {
      const res = await preparationService.runBenchmark({
        num_qubits: benchmarkQubits,
        total_hours_budget: benchmarkBudget,
        p_layers: 1,
      })
      setBenchmarkResult(res)
    } catch (err) {
      console.error('Benchmark failed:', err)
    } finally {
      setBenchmarkLoading(false)
    }
  }

  const togglePriority = (id: string) => {
    setSelectedPriorities((prev) =>
      prev.includes(id) ? prev.filter((p) => p !== id) : [...prev, id]
    )
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <Spinner size="lg" />
        <p className="text-slate-400 text-sm">Evaluating skill gaps and quantum formulation...</p>
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto space-y-8 animate-slide-up pb-16">
      {/* ─── Top Header ────────────────────────────────────────────── */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl md:text-3xl font-bold text-slate-100 flex items-center gap-2.5">
              <Sparkles className="h-7 w-7 text-brand-400" />
              Preparation Roadmap
            </h1>
            <Badge color="purple" className="flex items-center gap-1.5 py-1 px-2.5">
              <Zap className="h-3.5 w-3.5" />
              QAOA Quantum-Optimized
            </Badge>
          </div>
          <p className="text-slate-400 text-sm mt-1.5">
            Personalized learning path balancing verified skill gaps, role relevance, and study hours.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="secondary"
            size="sm"
            icon={<BarChart3 className="h-4 w-4" />}
            onClick={() => {
              setShowBenchmark(true)
              if (!benchmarkResult) handleRunBenchmark()
            }}
          >
            Quantum Benchmark
          </Button>

          <Button
            variant="primary"
            size="sm"
            icon={<Sliders className="h-4 w-4" />}
            onClick={() => setShowConfig(true)}
          >
            {plan ? 'Adjust Preferences' : 'Generate Plan'}
          </Button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 text-sm flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <AlertTriangle className="h-4 w-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
          <button onClick={() => setError(null)} className="text-red-400 hover:text-red-200">
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* ─── Quantum Optimization Specs Banner (When plan exists) ─────── */}
      {plan && plan.optimization_metadata && (
        <Card className="p-5 bg-gradient-to-r from-brand-950/40 via-purple-950/20 to-slate-900 border-brand-500/20">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 divide-y sm:divide-y-0 sm:divide-x divide-slate-800">
            <div className="px-2">
              <span className="text-xs text-slate-400 uppercase tracking-wider block">Optimizer</span>
              <span className="text-sm font-semibold text-brand-300 mt-0.5 flex items-center gap-1.5">
                <Cpu className="h-4 w-4 text-brand-400" />
                {plan.algorithm_used.includes('QAOA') ? 'QAOA Statevector (p=1)' : 'Classical Exact (B&B)'}
              </span>
            </div>

            <div className="px-2 pt-2 sm:pt-0">
              <span className="text-xs text-slate-400 uppercase tracking-wider block">Circuit Specs</span>
              <span className="text-sm font-semibold text-slate-200 mt-0.5">
                {plan.optimization_metadata.num_qubits ?? 8} Qubits · Depth{' '}
                {plan.circuit_depth ?? plan.optimization_metadata.circuit_depth ?? 5}
              </span>
            </div>

            <div className="px-2 pt-2 sm:pt-0">
              <span className="text-xs text-slate-400 uppercase tracking-wider block">Sol. Quality</span>
              <span className="text-sm font-semibold text-emerald-400 mt-0.5 flex items-center gap-1.5">
                <Activity className="h-4 w-4" />
                Ratio:{' '}
                {plan.optimization_metadata.classical_comparison?.qaoa_approximation_ratio ?? 1.0} (
                {(
                  (plan.optimization_metadata.classical_comparison?.qaoa_approximation_ratio ?? 1.0) *
                  100
                ).toFixed(0)}
                %)
              </span>
            </div>

            <div className="px-2 pt-2 sm:pt-0">
              <span className="text-xs text-slate-400 uppercase tracking-wider block">Total Scheduled</span>
              <span className="text-sm font-semibold text-slate-200 mt-0.5 flex items-center gap-1.5">
                <Clock className="h-4 w-4 text-purple-400" />
                {plan.total_hours_budget} hrs / {plan.preparation_days} days
              </span>
            </div>
          </div>
        </Card>
      )}

      {/* ─── Feedback & Skill Gap Insights Card ──────────────────────── */}
      {feedback && (
        <Card className="p-6 space-y-5">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2">
              <Brain className="h-5 w-5 text-brand-400" />
              <h2 className="text-base font-semibold text-slate-200">
                AI Feedback & Diagnostic Skill Profile
              </h2>
            </div>
            <div className="flex flex-wrap items-center gap-2 text-xs">
              <Badge color={feedback.has_mock_interview ? 'green' : 'slate'}>
                {feedback.has_mock_interview ? 'Mock Interview Calibrated' : 'Resume & Role Baseline'}
              </Badge>
              {feedback.target_role?.role_name && (
                <span className="text-slate-400">
                  Target: <strong className="text-slate-200">{feedback.target_role.role_name}</strong>
                </span>
              )}
            </div>
          </div>

          {/* Genuine Session Metrics Summary */}
          {feedback.has_mock_interview && feedback.interview_metrics && (
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 p-3.5 bg-slate-900/80 rounded-xl border border-slate-800 text-xs">
              <div className="flex items-center justify-between sm:justify-start gap-3">
                <span className="text-slate-400">Questions Answered:</span>
                <span className="font-bold text-slate-200">
                  {feedback.interview_metrics.questions_answered} / {feedback.interview_metrics.total_questions_asked}
                  {feedback.interview_metrics.questions_answered === 0 && (
                    <span className="ml-1.5 text-rose-400 font-normal">(0 answered)</span>
                  )}
                </span>
              </div>
              <div className="flex items-center justify-between sm:justify-start gap-3">
                <span className="text-slate-400">Session Overall Score:</span>
                <span className={`font-extrabold tabular-nums ${
                  feedback.interview_metrics.overall_score_pct === 0
                    ? 'text-rose-500'
                    : feedback.interview_metrics.overall_score_pct < 40
                    ? 'text-rose-400'
                    : feedback.interview_metrics.overall_score_pct < 70
                    ? 'text-amber-400'
                    : 'text-emerald-400'
                }`}>
                  {feedback.interview_metrics.overall_score_pct}%
                </span>
              </div>
              <div className="flex items-center justify-between sm:justify-start gap-3">
                <span className="text-slate-400">Diagnostic Status:</span>
                <span className="font-medium text-slate-300">
                  {feedback.interview_metrics.overall_score_pct === 0
                    ? 'Incomplete / 0 Answers'
                    : feedback.interview_metrics.overall_score_pct < 50
                    ? 'Needs Foundational Study'
                    : 'Working Competency'}
                </span>
              </div>
            </div>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 pt-1">
            {/* ─── Areas You Are Strong In ─── */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-emerald-400 flex items-center gap-1.5">
                  <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                  Areas You Are Strong In
                </h3>
                {feedback.strong_areas && feedback.strong_areas.length > 0 && (
                  <span className="text-[11px] text-emerald-400/80 font-medium">
                    {feedback.strong_areas.length} verified
                  </span>
                )}
              </div>

              {feedback.strong_areas && feedback.strong_areas.length > 0 ? (
                <div className="space-y-2">
                  {feedback.strong_areas.map((sa, idx) => (
                    <div
                      key={idx}
                      className="text-xs bg-emerald-500/5 border border-emerald-500/20 rounded-xl p-3 space-y-1.5"
                    >
                      <div className="flex items-center justify-between font-semibold text-slate-200">
                        <span className="text-emerald-300">{sa.topic}</span>
                        <span className="bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 rounded-md px-2 py-0.5 text-[11px] font-bold">
                          {sa.score_pct}% Mastery
                        </span>
                      </div>
                      <p className="text-slate-300 text-[11px] leading-relaxed">
                        {sa.summary || 'Demonstrated solid technical depth and clear reasoning during the assessment.'}
                      </p>
                    </div>
                  ))}
                </div>
              ) : feedback.strengths && feedback.strengths.length > 0 && !feedback.has_mock_interview ? (
                <ul className="space-y-1.5">
                  {feedback.strengths.slice(0, 4).map((s, idx) => (
                    <li
                      key={idx}
                      className="text-xs text-slate-300 bg-emerald-500/5 border border-emerald-500/15 rounded-lg px-3 py-2 flex items-start gap-2"
                    >
                      <span className="text-emerald-400 font-bold">•</span>
                      <span>{s}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 text-center space-y-1">
                  <p className="text-xs font-medium text-slate-300">No verified strong areas yet</p>
                  <p className="text-[11px] text-slate-500 leading-relaxed max-w-sm mx-auto">
                    {feedback.has_mock_interview && feedback.interview_metrics?.questions_answered === 0
                      ? 'No questions were answered in your interview session (0%). Answer questions in your next mock interview to demonstrate topic mastery.'
                      : 'All assessed topics scored below the 70% mastery threshold. Follow the preparation roadmap below to build verified strengths.'}
                  </p>
                </div>
              )}
            </div>

            {/* ─── Areas Needing Improvement (Weak Areas) ─── */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-rose-400 flex items-center gap-1.5">
                  <AlertTriangle className="h-4 w-4 text-rose-400" />
                  Areas Needing Improvement (Weak Areas)
                </h3>
                {feedback.weak_areas && feedback.weak_areas.length > 0 && (
                  <span className="text-[11px] text-rose-400/80 font-medium">
                    {feedback.weak_areas.length} gaps identified
                  </span>
                )}
              </div>

              {feedback.weak_areas && feedback.weak_areas.length > 0 ? (
                <div className="space-y-2">
                  {feedback.weak_areas.map((wa, idx) => (
                    <div
                      key={idx}
                      className="text-xs bg-rose-500/5 border border-rose-500/20 rounded-xl p-3 space-y-1.5"
                    >
                      <div className="flex items-center justify-between font-semibold text-slate-200">
                        <span className="text-rose-300">{wa.topic}</span>
                        <div className="flex items-center gap-1.5">
                          <span className={`px-2 py-0.5 rounded-md text-[10px] font-bold uppercase ${
                            wa.status === 'unanswered' || wa.score_pct === 0
                              ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                              : 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                          }`}>
                            {wa.status === 'unanswered' ? '0% · Unanswered' : `${wa.score_pct}% Score`}
                          </span>
                          <span className="bg-slate-800 text-slate-400 text-[10px] uppercase px-1.5 py-0.5 rounded">
                            {wa.priority || 'high'}
                          </span>
                        </div>
                      </div>
                      <p className="text-slate-300 text-[11px] leading-relaxed">
                        {wa.reason || wa.recommendation}
                      </p>
                      {wa.recommendation && wa.reason && (
                        <p className="text-slate-400 text-[10px] border-t border-rose-500/10 pt-1 mt-1">
                          Action: {wa.recommendation}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              ) : feedback.weaknesses && feedback.weaknesses.length > 0 ? (
                <div className="space-y-2">
                  {feedback.weaknesses.slice(0, 4).map((w, idx) => (
                    <div
                      key={idx}
                      className="text-xs text-slate-300 bg-amber-500/5 border border-amber-500/15 rounded-lg p-2.5"
                    >
                      <div className="flex items-center justify-between font-medium text-slate-200">
                        <span>{w.area}</span>
                        <span className="text-amber-400 text-[11px] uppercase tracking-wide">
                          {w.priority} priority
                        </span>
                      </div>
                      <p className="text-slate-400 text-[11px] mt-1">{w.recommendation}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-slate-500 italic">
                  No critical deficiencies identified. Focus on competitive role mastery below.
                </p>
              )}
            </div>
          </div>
        </Card>
      )}

      {/* ─── Main Roadmap or Empty State ─────────────────────────────── */}
      {!plan ? (
        <Card className="p-10">
          <EmptyState
            title="Generate Your QAOA Preparation Plan"
            description="Our quantum optimizer will balance your identified skill gaps, target role expectations, and remaining study days to formulate your highest-yield preparation path."
            icon={<Brain className="h-10 w-10 text-brand-400" />}
            action={
              <Button
                variant="primary"
                icon={<Sparkles className="h-4 w-4" />}
                onClick={() => setShowConfig(true)}
              >
                Configure & Run QAOA
              </Button>
            }
          />
        </Card>
      ) : (
        <div className="space-y-6">
          {/* Progress Header */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-900/60 border border-slate-800 p-4 rounded-2xl">
            <div className="flex items-center gap-4">
              <div className="relative h-12 w-12 flex items-center justify-center">
                <svg className="h-12 w-12 transform -rotate-90">
                  <circle
                    cx="24"
                    cy="24"
                    r="18"
                    stroke="currentColor"
                    strokeWidth="4"
                    fill="transparent"
                    className="text-slate-800"
                  />
                  <circle
                    cx="24"
                    cy="24"
                    r="18"
                    stroke="currentColor"
                    strokeWidth="4"
                    fill="transparent"
                    strokeDasharray={113}
                    strokeDashoffset={113 - (113 * progressStats.percent) / 100}
                    className="text-brand-500 transition-all duration-500"
                  />
                </svg>
                <span className="absolute text-xs font-bold text-slate-200">
                  {progressStats.percent}%
                </span>
              </div>
              <div>
                <h3 className="text-sm font-semibold text-slate-200">Roadmap Progress</h3>
                <p className="text-xs text-slate-400">
                  {progressStats.completed} of {progressStats.total} modules mastered ·{' '}
                  {progressStats.hoursLeft} hrs remaining
                </p>
              </div>
            </div>

            {/* Day Selector Pills */}
            <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0">
              {scheduledDaysList.map((dayNum) => {
                const dayMods = modulesByDay[dayNum] || []
                const dayDone = dayMods.every((m) => m.status === 'completed')
                return (
                  <button
                    key={dayNum}
                    onClick={() => setActiveDay(dayNum)}
                    className={`px-3 py-1.5 rounded-xl text-xs font-medium transition-all flex items-center gap-1.5 ${
                      activeDay === dayNum
                        ? 'bg-brand-500 text-white shadow-lg shadow-brand-500/25'
                        : 'bg-slate-800 text-slate-400 hover:text-slate-200 hover:bg-slate-700/60'
                    }`}
                  >
                    <span>Day {dayNum}</span>
                    {dayDone && <Check className="h-3 w-3 text-emerald-300" />}
                  </button>
                )
              })}
            </div>
          </div>

          {/* Active Day Modules List */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
                <Calendar className="h-5 w-5 text-brand-400" />
                Day {activeDay} Curriculum Schedule
              </h2>
              <span className="text-xs text-slate-400">
                {modulesByDay[activeDay]?.length ?? 0} modules scheduled
              </span>
            </div>

            <div className="grid grid-cols-1 gap-4">
              {modulesByDay[activeDay]?.map((mod) => {
                const isUpdating = updatingModules[mod.id]
                const isCompleted = mod.status === 'completed'

                return (
                  <Card
                    key={mod.id}
                    className={`p-5 transition-all ${
                      isCompleted
                        ? 'bg-emerald-950/10 border-emerald-500/20'
                        : 'hover:border-slate-700'
                    }`}
                  >
                    <div className="flex items-start gap-4">
                      {/* Checkbox */}
                      <button
                        onClick={() => handleToggleModule(mod)}
                        disabled={isUpdating}
                        className={`mt-1 h-6 w-6 rounded-lg border flex items-center justify-center transition-all ${
                          isCompleted
                            ? 'bg-emerald-500 border-emerald-400 text-slate-950 shadow-md shadow-emerald-500/30'
                            : 'border-slate-700 bg-slate-800 hover:border-brand-500 text-transparent'
                        }`}
                        title={isCompleted ? 'Mark pending' : 'Mark completed'}
                      >
                        {isUpdating ? (
                          <Spinner size="sm" />
                        ) : isCompleted ? (
                          <Check className="h-4 w-4 stroke-[3]" />
                        ) : (
                          <Circle className="h-3.5 w-3.5" />
                        )}
                      </button>

                      {/* Content */}
                      <div className="flex-1 space-y-3">
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                          <div>
                            <h3
                              className={`text-base font-semibold transition-all ${
                                isCompleted
                                  ? 'text-slate-400 line-through'
                                  : 'text-slate-100'
                              }`}
                            >
                              {mod.topic}
                            </h3>
                            <div className="flex items-center gap-2.5 mt-1">
                              <Badge
                                color={
                                  mod.priority === 'high'
                                    ? 'red'
                                    : mod.priority === 'medium'
                                    ? 'yellow'
                                    : 'slate'
                                }
                                className="text-[10px] py-0.5 px-2 uppercase"
                              >
                                {mod.priority} priority
                              </Badge>

                              <span className="text-xs text-slate-400 flex items-center gap-1">
                                <Clock className="h-3 w-3 text-purple-400" />
                                {mod.estimated_hours} hrs
                              </span>

                              {mod.prerequisites?.length > 0 && (
                                <span className="text-xs text-indigo-400 flex items-center gap-1">
                                  <Layers className="h-3 w-3" />
                                  Requires: {mod.prerequisites.join(', ')}
                                </span>
                              )}
                            </div>
                          </div>

                          <div className="text-right">
                            {isCompleted ? (
                              <Badge color="green">Mastered</Badge>
                            ) : (
                              <Badge color="slate">Pending</Badge>
                            )}
                          </div>
                        </div>

                        {/* Why Selected Rationale */}
                        {mod.why_selected && (
                          <div className="text-xs bg-slate-900/80 border border-slate-800 rounded-xl p-3 text-slate-300">
                            <span className="text-brand-300 font-semibold block mb-0.5">
                              Why Quantum Optimizer Selected This:
                            </span>
                            {mod.why_selected}
                          </div>
                        )}

                        {/* Expected Outcome */}
                        {mod.expected_outcome && (
                          <div className="text-xs text-slate-400 flex items-start gap-1.5">
                            <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400 flex-shrink-0 mt-0.5" />
                            <span>
                              <strong className="text-slate-300">Expected Outcome:</strong>{' '}
                              {mod.expected_outcome}
                            </span>
                          </div>
                        )}

                        {/* Free Learning Resources */}
                        {(() => {
                          const resources = getResourcesForTopic(
                            mod.activity_id,
                            mod.topic,
                            (mod as any).category || '',
                            mod.sub_topics || []
                          )
                          const isCollapsed = !!collapsedResources[mod.id]

                          return (
                            <div className="pt-2 border-t border-slate-800/80">
                              <div className="flex items-center justify-between mb-2">
                                <button
                                  type="button"
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    toggleResourcesCollapse(mod.id)
                                  }}
                                  className="text-xs font-semibold text-slate-300 hover:text-brand-300 flex items-center gap-1.5 transition-colors group"
                                >
                                  <BookOpen className="h-3.5 w-3.5 text-purple-400 group-hover:text-brand-400" />
                                  <span>Free Learning Resources</span>
                                  <Badge color="purple" className="text-[10px] py-0 px-1.5 ml-1">
                                    {resources.length} free
                                  </Badge>
                                  {isCollapsed ? (
                                    <ChevronRight className="h-3.5 w-3.5 text-slate-500" />
                                  ) : (
                                    <ChevronDown className="h-3.5 w-3.5 text-slate-500" />
                                  )}
                                </button>
                                <span className="text-[11px] text-slate-500 hidden sm:inline">
                                  Curated tutorials, courses & docs
                                </span>
                              </div>

                              {!isCollapsed && (
                                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5 mt-1.5 animate-fade-in">
                                  {resources.map((res, rIdx) => {
                                    const typeColor =
                                      res.type === 'Video'
                                        ? 'bg-rose-500/15 text-rose-300 border-rose-500/30'
                                        : res.type === 'Course'
                                        ? 'bg-purple-500/15 text-purple-300 border-purple-500/30'
                                        : res.type === 'Practice'
                                        ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30'
                                        : res.type === 'Documentation'
                                        ? 'bg-amber-500/15 text-amber-300 border-amber-500/30'
                                        : 'bg-brand-500/15 text-brand-300 border-brand-500/30'

                                    const TypeIcon =
                                      res.type === 'Video'
                                        ? Play
                                        : res.type === 'Course'
                                        ? GraduationCap
                                        : res.type === 'Documentation'
                                        ? FileText
                                        : res.type === 'Practice'
                                        ? Code2
                                        : Monitor

                                    return (
                                      <div
                                        key={rIdx}
                                        className="p-2.5 rounded-xl bg-slate-900/90 border border-slate-800 hover:border-slate-700 hover:bg-slate-850 transition-all flex flex-col justify-between group"
                                      >
                                        <div className="space-y-1.5">
                                          <div className="flex items-center justify-between gap-1">
                                            <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider truncate">
                                              {res.platform}
                                            </span>
                                            <span
                                              className={`text-[9px] px-1.5 py-0.5 rounded-md border font-medium flex items-center gap-1 ${typeColor}`}
                                            >
                                              <TypeIcon className="h-2.5 w-2.5" />
                                              {res.type}
                                            </span>
                                          </div>
                                          <h4 className="text-xs font-semibold text-slate-200 line-clamp-1 group-hover:text-brand-300 transition-colors">
                                            {res.title}
                                          </h4>
                                          <p className="text-[11px] text-slate-400 line-clamp-2 leading-relaxed">
                                            {res.description}
                                          </p>
                                        </div>
                                        <div className="pt-2 mt-2 border-t border-slate-800/60 flex items-center justify-end">
                                          <a
                                            href={res.url}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            onClick={(e) => e.stopPropagation()}
                                            className="text-[11px] font-medium text-brand-400 hover:text-brand-300 flex items-center gap-1 hover:underline"
                                          >
                                            <span>Open Resource</span>
                                            <ExternalLink className="h-3 w-3" />
                                          </a>
                                        </div>
                                      </div>
                                    )
                                  })}
                                </div>
                              )}
                            </div>
                          )
                        })()}

                        {/* Exercises list */}
                        {mod.practice_exercises?.length > 0 && (
                          <div className="pt-2 border-t border-slate-800/80">
                            <span className="text-xs font-semibold text-slate-400 block mb-1.5 flex items-center gap-1.5">
                              <Code2 className="h-3.5 w-3.5 text-brand-400" />
                              Recommended Coding Challenges & Drills:
                            </span>
                            <div className="flex flex-wrap gap-1.5">
                              {mod.practice_exercises.map((ex, idx) => (
                                <span
                                  key={idx}
                                  className="text-xs font-mono bg-brand-500/10 text-brand-300 border border-brand-500/20 px-2.5 py-1 rounded-lg"
                                >
                                  {ex}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </Card>
                )
              })}
            </div>
          </div>
        </div>
      )}

      {/* ─── Preferences & Regeneration Modal ───────────────────────── */}
      {showConfig && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4 animate-fade-in">
          <Card className="max-w-xl w-full p-6 space-y-6 bg-slate-900 border-slate-800 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <div className="flex items-center gap-2.5">
                <Sliders className="h-5 w-5 text-brand-400" />
                <h2 className="text-lg font-bold text-slate-100">Preparation Preferences</h2>
              </div>
              <button
                onClick={() => setShowConfig(false)}
                className="text-slate-400 hover:text-slate-200"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="space-y-5">
              {/* Days Slider */}
              <div>
                <div className="flex justify-between text-xs font-medium text-slate-300 mb-2">
                  <span>Days Until Interview / Placement:</span>
                  <span className="text-brand-400 font-bold text-sm">{daysRemaining} Days</span>
                </div>
                <input
                  type="range"
                  min="2"
                  max="30"
                  step="1"
                  value={daysRemaining}
                  onChange={(e) => setDaysRemaining(Number(e.target.value))}
                  className="w-full accent-brand-500 cursor-pointer"
                />
                <div className="flex justify-between text-[10px] text-slate-500 mt-1">
                  <span>2 days (Cram)</span>
                  <span>14 days</span>
                  <span>30 days (Comprehensive)</span>
                </div>
              </div>

              {/* Daily Hours Slider */}
              <div>
                <div className="flex justify-between text-xs font-medium text-slate-300 mb-2">
                  <span>Daily Study Commitment:</span>
                  <span className="text-purple-400 font-bold text-sm">{dailyHours} Hours/Day</span>
                </div>
                <input
                  type="range"
                  min="0.5"
                  max="6.0"
                  step="0.5"
                  value={dailyHours}
                  onChange={(e) => setDailyHours(Number(e.target.value))}
                  className="w-full accent-purple-500 cursor-pointer"
                />
                <div className="flex justify-between text-[10px] text-slate-500 mt-1">
                  <span>30 mins</span>
                  <span>Total Budget: {Math.round(daysRemaining * dailyHours * 10) / 10} Hours</span>
                  <span>6 hours</span>
                </div>
              </div>

              {/* Priority Pills */}
              <div>
                <label className="text-xs font-medium text-slate-300 block mb-2">
                  Priority Focus Areas (+15% QAOA Value Weight):
                </label>
                <div className="flex flex-wrap gap-2">
                  {PRIORITY_OPTIONS.map((opt) => {
                    const isSelected = selectedPriorities.includes(opt.id)
                    return (
                      <button
                        key={opt.id}
                        type="button"
                        onClick={() => togglePriority(opt.id)}
                        className={`text-xs px-3 py-1.5 rounded-xl border transition-all ${
                          isSelected
                            ? 'bg-brand-500/20 border-brand-500 text-brand-300 shadow-sm'
                            : 'bg-slate-800/80 border-slate-700 text-slate-400 hover:text-slate-200'
                        }`}
                      >
                        {opt.label}
                      </button>
                    )
                  })}
                </div>
              </div>

              {/* Optimization Algorithm Selection */}
              <div>
                <label className="text-xs font-medium text-slate-300 block mb-2">
                  Optimization Engine:
                </label>
                <div className="grid grid-cols-2 gap-3">
                  <button
                    type="button"
                    onClick={() => setSelectedAlgorithm('qaoa')}
                    className={`p-3 rounded-xl border text-left transition-all ${
                      selectedAlgorithm === 'qaoa'
                        ? 'bg-purple-950/40 border-purple-500 text-slate-200 shadow-md'
                        : 'bg-slate-800/50 border-slate-700 text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    <div className="flex items-center gap-1.5 font-semibold text-xs text-purple-300 mb-0.5">
                      <Zap className="h-3.5 w-3.5" />
                      Quantum QAOA
                    </div>
                    <p className="text-[11px] text-slate-400">
                      Qiskit ansatz circuit, QUBO knapsack mapping.
                    </p>
                  </button>

                  <button
                    type="button"
                    onClick={() => setSelectedAlgorithm('classical')}
                    className={`p-3 rounded-xl border text-left transition-all ${
                      selectedAlgorithm === 'classical'
                        ? 'bg-brand-950/40 border-brand-500 text-slate-200 shadow-md'
                        : 'bg-slate-800/50 border-slate-700 text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    <div className="flex items-center gap-1.5 font-semibold text-xs text-brand-300 mb-0.5">
                      <Cpu className="h-3.5 w-3.5" />
                      Classical (B&B)
                    </div>
                    <p className="text-[11px] text-slate-400">
                      Exact deterministic branch-and-bound baseline.
                    </p>
                  </button>
                </div>
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
              <Button variant="ghost" size="sm" onClick={() => setShowConfig(false)}>
                Cancel
              </Button>
              <Button
                variant="primary"
                size="sm"
                loading={generating}
                icon={<Sparkles className="h-4 w-4" />}
                onClick={handleGeneratePlan}
              >
                {plan ? 'Regenerate Roadmap' : 'Generate Roadmap'}
              </Button>
            </div>
          </Card>
        </div>
      )}

      {/* ─── Quantum Benchmark Modal ─────────────────────────────────── */}
      {showBenchmark && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4 animate-fade-in">
          <Card className="max-w-2xl w-full p-6 space-y-6 bg-slate-900 border-slate-800 shadow-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <div className="flex items-center gap-2.5">
                <BarChart3 className="h-5 w-5 text-purple-400" />
                <div>
                  <h2 className="text-lg font-bold text-slate-100">
                    QAOA Quantum vs Classical Benchmark
                  </h2>
                  <p className="text-xs text-slate-400">
                    Scientific performance evaluation on identical problem instances.
                  </p>
                </div>
              </div>
              <button
                onClick={() => setShowBenchmark(false)}
                className="text-slate-400 hover:text-slate-200"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Benchmark Controls */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 bg-slate-950/60 p-4 rounded-xl border border-slate-800">
              <div>
                <label className="text-xs text-slate-400 block mb-1">
                  Problem Size (Qubits): <strong>{benchmarkQubits}</strong>
                </label>
                <input
                  type="range"
                  min="4"
                  max="10"
                  step="1"
                  value={benchmarkQubits}
                  onChange={(e) => setBenchmarkQubits(Number(e.target.value))}
                  className="w-full accent-purple-500 cursor-pointer"
                />
              </div>

              <div>
                <label className="text-xs text-slate-400 block mb-1">
                  Budget Constraint: <strong>{benchmarkBudget} hrs</strong>
                </label>
                <input
                  type="range"
                  min="4"
                  max="24"
                  step="2"
                  value={benchmarkBudget}
                  onChange={(e) => setBenchmarkBudget(Number(e.target.value))}
                  className="w-full accent-brand-500 cursor-pointer"
                />
              </div>

              <div className="sm:col-span-2 flex justify-end">
                <Button
                  variant="secondary"
                  size="sm"
                  loading={benchmarkLoading}
                  icon={<RefreshCw className="h-4 w-4" />}
                  onClick={handleRunBenchmark}
                >
                  Run Benchmark Sweep
                </Button>
              </div>
            </div>

            {/* Benchmark Results */}
            {benchmarkResult ? (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  {/* Quantum QAOA Card */}
                  <div className="p-4 rounded-xl bg-purple-950/20 border border-purple-500/30 space-y-2">
                    <span className="text-xs font-semibold text-purple-300 flex items-center gap-1.5">
                      <Zap className="h-4 w-4 text-purple-400" />
                      Quantum QAOA (Qiskit)
                    </span>
                    <div className="text-2xl font-bold text-slate-100">
                      {benchmarkResult.qaoa_total_value}{' '}
                      <span className="text-xs font-normal text-slate-400">value pts</span>
                    </div>
                    <div className="text-xs text-slate-400 space-y-1 pt-1 border-t border-purple-500/20">
                      <div>Execution: {benchmarkResult.qaoa_execution_time_ms} ms</div>
                      <div>Circuit Depth: {benchmarkResult.circuit_depth}</div>
                      <div>Scheduled: {benchmarkResult.qaoa_hours_scheduled} hrs</div>
                      <div>
                        Feasible Raw: {benchmarkResult.qaoa_is_feasible ? 'Yes' : 'Repaired'}
                      </div>
                    </div>
                  </div>

                  {/* Classical Exact Card */}
                  <div className="p-4 rounded-xl bg-brand-950/20 border border-brand-500/30 space-y-2">
                    <span className="text-xs font-semibold text-brand-300 flex items-center gap-1.5">
                      <Cpu className="h-4 w-4 text-brand-400" />
                      Classical Exact Solver
                    </span>
                    <div className="text-2xl font-bold text-slate-100">
                      {benchmarkResult.classical_comparison.classical_optimal_value}{' '}
                      <span className="text-xs font-normal text-slate-400">value pts</span>
                    </div>
                    <div className="text-xs text-slate-400 space-y-1 pt-1 border-t border-brand-500/20">
                      <div>
                        Execution:{' '}
                        {benchmarkResult.classical_comparison.classical_execution_time_ms} ms
                      </div>
                      <div>Optimality: Provably 100%</div>
                      <div>
                        Scheduled: {benchmarkResult.classical_comparison.classical_hours} hrs
                      </div>
                      <div>Prerequisites: Fully Respected</div>
                    </div>
                  </div>
                </div>

                {/* Approximation Ratio Banner */}
                <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-center">
                  <span className="text-xs text-slate-400 block mb-0.5">
                    QAOA Approximation Ratio (\alpha)
                  </span>
                  <span className="text-xl font-bold text-emerald-400">
                    {benchmarkResult.classical_comparison.qaoa_approximation_ratio} (
                    {(
                      benchmarkResult.classical_comparison.qaoa_approximation_ratio * 100
                    ).toFixed(1)}
                    % of theoretical optimum)
                  </span>
                </div>

                {/* Top Measured States */}
                {benchmarkResult.top_measurement_states?.length > 0 && (
                  <div>
                    <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
                      Top Sampled Quantum Measurement Bitstrings:
                    </h4>
                    <div className="space-y-1 font-mono text-xs">
                      {benchmarkResult.top_measurement_states.map((st, idx) => (
                        <div
                          key={idx}
                          className="flex items-center justify-between bg-slate-800/60 px-3 py-1.5 rounded-lg border border-slate-700/60"
                        >
                          <span className="text-purple-300">|{st.bitstring}⟩</span>
                          <span className="text-slate-400">
                            Prob: {(st.probability * 100).toFixed(1)}% · Val: {st.value} ·{' '}
                            {st.hours} hrs
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-8">
                <Spinner size="md" />
                <p className="text-xs text-slate-400 mt-2">Computing quantum expectation values...</p>
              </div>
            )}
          </Card>
        </div>
      )}
    </div>
  )
}

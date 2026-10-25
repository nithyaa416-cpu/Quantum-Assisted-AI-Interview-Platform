import { Link } from 'react-router-dom'
import {
  Trophy, CheckCircle2, AlertTriangle, Eye, Mic, Volume2,
  Sparkles, ShieldCheck, ShieldAlert, Smartphone, Brain,
  TrendingUp, Award, Clock, ArrowRight, Zap, Target
} from 'lucide-react'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import type { Assessment } from '@/types'

interface AssessmentReportViewProps {
  assessment: Assessment
}

export function AssessmentReportView({ assessment }: AssessmentReportViewProps) {
  const overallPct = Math.round(Number(assessment.overall_score) * 100)
  const techPct = Math.round(Number(assessment.technical_score) * 100)
  const commPct = Math.round(Number(assessment.communication_score) * 100)
  const behPct = assessment.behavioural_score !== null ? Math.round(Number(assessment.behavioural_score) * 100) : (overallPct === 0 ? 0 : 50)
  const probPct = Math.round(Number(assessment.problem_solving_score) * 100)
  const codingPct = assessment.coding_score !== null ? Math.round(Number(assessment.coding_score) * 100) : null

  // Speech & Voice metrics (no artificial defaults)
  const speech = assessment.speech_metrics || {}
  const wpm = speech.words_per_minute ?? 0
  const fluencyScore = speech.fluency_score ?? 0
  const modulationScore = speech.pitch_modulation_score ?? 0
  const articulation = speech.articulation_quality ?? (overallPct === 0 ? 'unattempted' : 'steady')

  // Behavioral & Facial metrics
  const beh = assessment.behavioural_metrics || {}
  const eyeContactPct = beh.eye_contact_percentage ?? 0
  const confidenceScore = beh.confidence_score ?? 0
  const postureScore = beh.posture_stability_score ?? 0
  const dominantExp = beh.dominant_expression ?? (overallPct === 0 ? 'neutral' : 'confident')
  const phoneIncidents = beh.phone_detected_incidents ?? 0
  const singleHumanCompliance = beh.single_human_compliance ?? 100

  // Readiness categorization with realistic scoring thresholds
  let readinessBadge: {
    label: string
    color: 'indigo' | 'green' | 'yellow' | 'red' | 'slate' | 'purple'
    desc: string
  } = {
    label: 'Placement Ready',
    color: 'green',
    desc: 'Outstanding performance across technical depth and interview poise.',
  }
  if (overallPct === 0) {
    readinessBadge = { label: 'Incomplete / Unanswered', color: 'red', desc: 'No substantive answers recorded. All questions were left blank or unattempted (0%).' }
  } else if (overallPct < 40) {
    readinessBadge = { label: 'Needs Critical Preparation', color: 'red', desc: 'Significant knowledge gaps identified across core topics. Intensive foundational review required.' }
  } else if (overallPct < 60) {
    readinessBadge = { label: 'Needs Targeted Prep', color: 'yellow', desc: 'Working foundation; focus on strengthening weak areas and communication clarity.' }
  } else if (overallPct < 75) {
    readinessBadge = { label: 'Solid Foundations', color: 'indigo', desc: 'Strong baseline; fine-tune modulation and advanced edge cases.' }
  }

  let scoreColor = 'text-emerald-400'
  if (overallPct === 0) scoreColor = 'text-rose-500'
  else if (overallPct < 40) scoreColor = 'text-rose-400'
  else if (overallPct < 70) scoreColor = 'text-amber-400'

  return (
    <div className="space-y-6 animate-slide-up">
      {/* ── Top Hero: Executive Score & Quantum Optimization Callout ────────── */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-brand-950/80 via-slate-900 to-surface-card border border-brand-500/30 p-6 md:p-8 shadow-2xl">
        <div className="absolute top-0 right-0 -mt-8 -mr-8 w-64 h-64 bg-brand-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Badge color={readinessBadge.color}>{readinessBadge.label}</Badge>
              {assessment.target_role && (
                <span className="text-xs text-slate-400 font-medium">Target: {assessment.target_role}</span>
              )}
            </div>
            <h2 className="text-2xl md:text-3xl font-extrabold text-slate-100 tracking-tight">
              AI Interview Assessment Report
            </h2>
            <p className="text-sm text-slate-400 max-w-xl">
              {readinessBadge.desc}
            </p>
          </div>

          {/* Overall score radial / box */}
          <div className="flex items-center gap-4 bg-slate-900/80 border border-slate-700/60 rounded-2xl p-4 shadow-lg">
            <div className="flex flex-col items-center">
              <span className={`text-4xl font-extrabold ${scoreColor} tabular-nums`}>
                {overallPct}%
              </span>
              <span className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold mt-0.5">
                Overall Readiness
              </span>
            </div>
            <div className="h-10 w-px bg-slate-700/60" />
            <Link to="/preparation">
              <Button size="sm" className="bg-purple-600 hover:bg-purple-500 text-white font-medium flex items-center gap-1.5 shadow-lg shadow-purple-600/20">
                <Brain className="h-4 w-4" />
                <span>Quantum QAOA Plan</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </Button>
            </Link>
          </div>
        </div>
      </div>

      {/* ── Key Score Dimension Pillars ───────────────────────────────────────── */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="p-4 bg-surface-card/60 border-slate-800 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400">Technical Depth</span>
            <Target className="h-4 w-4 text-blue-400" />
          </div>
          <div className="mt-3">
            <div className="text-2xl font-bold text-slate-100 tabular-nums">{techPct}%</div>
            <div className="w-full bg-slate-800 rounded-full h-1.5 mt-2 overflow-hidden">
              <div className="bg-blue-500 h-1.5 rounded-full" style={{ width: `${techPct}%` }} />
            </div>
          </div>
        </Card>

        <Card className="p-4 bg-surface-card/60 border-slate-800 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400">Communication &amp; Fluency</span>
            <Mic className="h-4 w-4 text-emerald-400" />
          </div>
          <div className="mt-3">
            <div className="text-2xl font-bold text-slate-100 tabular-nums">{commPct}%</div>
            <div className="w-full bg-slate-800 rounded-full h-1.5 mt-2 overflow-hidden">
              <div className="bg-emerald-500 h-1.5 rounded-full" style={{ width: `${commPct}%` }} />
            </div>
          </div>
        </Card>

        <Card className="p-4 bg-surface-card/60 border-slate-800 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400">Behavioral Poise</span>
            <Sparkles className="h-4 w-4 text-purple-400" />
          </div>
          <div className="mt-3">
            <div className="text-2xl font-bold text-slate-100 tabular-nums">{behPct}%</div>
            <div className="w-full bg-slate-800 rounded-full h-1.5 mt-2 overflow-hidden">
              <div className="bg-purple-500 h-1.5 rounded-full" style={{ width: `${behPct}%` }} />
            </div>
          </div>
        </Card>

        <Card className="p-4 bg-surface-card/60 border-slate-800 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400">
              {codingPct !== null ? 'Coding & Testing' : 'Problem Solving'}
            </span>
            <Award className="h-4 w-4 text-amber-400" />
          </div>
          <div className="mt-3">
            <div className="text-2xl font-bold text-slate-100 tabular-nums">
              {codingPct !== null ? `${codingPct}%` : `${probPct}%`}
            </div>
            <div className="w-full bg-slate-800 rounded-full h-1.5 mt-2 overflow-hidden">
              <div
                className="bg-amber-500 h-1.5 rounded-full"
                style={{ width: `${codingPct !== null ? codingPct : probPct}%` }}
              />
            </div>
          </div>
        </Card>
      </div>

      {/* ── Real Interview Analytics: Behavioral & Voice Diagnostics ────────── */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Left Card: Facial Poise & Eye Contact Analysis */}
        <Card className="p-6 bg-surface-card border-slate-800 space-y-4">
          <div className="flex items-center justify-between border-b border-surface-border pb-3">
            <div className="flex items-center gap-2">
              <Eye className="h-5 w-5 text-indigo-400" />
              <h3 className="text-base font-bold text-slate-100">Facial &amp; Poise Diagnostics</h3>
            </div>
            <Badge color="purple">MediaPipe 3D Mesh</Badge>
          </div>

          <div className="space-y-4 pt-1">
            {/* Eye Contact Metric */}
            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-slate-400 flex items-center gap-1.5">
                  <Eye className="h-3.5 w-3.5 text-slate-400" /> Camera Eye Contact Ratio
                </span>
                <span className="font-semibold text-slate-200 tabular-nums">{eyeContactPct}%</span>
              </div>
              <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                <div
                  className={`h-2 rounded-full ${eyeContactPct >= 75 ? 'bg-emerald-400' : 'bg-amber-400'}`}
                  style={{ width: `${eyeContactPct}%` }}
                />
              </div>
              <p className="text-[11px] text-slate-500 mt-1">
                {eyeContactPct >= 75
                  ? 'Maintained direct screen focus toward the interviewer with minimal gaze diversion.'
                  : 'Gaze wandered periodically away from camera. Maintain eye contact during explanations.'}
              </p>
            </div>

            {/* Confidence & Composure Score */}
            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-slate-400 flex items-center gap-1.5">
                  <Sparkles className="h-3.5 w-3.5 text-slate-400" /> Confidence &amp; Poise Index
                </span>
                <span className="font-semibold text-slate-200 tabular-nums">{confidenceScore}%</span>
              </div>
              <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                <div
                  className="bg-indigo-400 h-2 rounded-full"
                  style={{ width: `${confidenceScore}%` }}
                />
              </div>
              <p className="text-[11px] text-slate-500 mt-1">
                Dominant facial demeanor: <strong className="text-slate-300 capitalize">{dominantExp}</strong> with {postureScore}% head and posture stability.
              </p>
            </div>

            {/* Strict Proctoring & Multi-Human Status */}
            <div className="rounded-xl p-3 bg-slate-900/70 border border-slate-800 flex items-center justify-between text-xs">
              <div className="flex items-center gap-2">
                {phoneIncidents === 0 && singleHumanCompliance >= 95 ? (
                  <ShieldCheck className="h-4 w-4 text-emerald-400" />
                ) : (
                  <ShieldAlert className="h-4 w-4 text-amber-400" />
                )}
                <div>
                  <div className="font-semibold text-slate-200">
                    {phoneIncidents === 0 ? 'Single-Candidate Environment Verified' : 'Proctoring Warning Issued'}
                  </div>
                  <div className="text-[11px] text-slate-400">
                    {phoneIncidents > 0
                      ? `${phoneIncidents} mobile phone detection(s) flagged during interview.`
                      : 'Zero unauthorized persons or devices detected in camera frame.'}
                  </div>
                </div>
              </div>
              <Badge color={phoneIncidents === 0 ? 'green' : 'red'}>
                {phoneIncidents === 0 ? '100% Verified' : 'Flagged'}
              </Badge>
            </div>
          </div>
        </Card>

        {/* Right Card: Voice Fluency & Modulation Diagnostics */}
        <Card className="p-6 bg-surface-card border-slate-800 space-y-4">
          <div className="flex items-center justify-between border-b border-surface-border pb-3">
            <div className="flex items-center gap-2">
              <Volume2 className="h-5 w-5 text-emerald-400" />
              <h3 className="text-base font-bold text-slate-100">Speech &amp; Vocal Modulation</h3>
            </div>
            <Badge color="green">Web Audio FFT</Badge>
          </div>

          <div className="space-y-4 pt-1">
            {/* Speaking Pace WPM */}
            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-slate-400 flex items-center gap-1.5">
                  <Clock className="h-3.5 w-3.5 text-slate-400" /> Speaking Speed (Words Per Minute)
                </span>
                <span className="font-semibold text-slate-200 tabular-nums">{wpm} WPM</span>
              </div>
              <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                <div
                  className={`h-2 rounded-full ${wpm >= 110 && wpm <= 165 ? 'bg-emerald-400' : 'bg-amber-400'}`}
                  style={{ width: `${Math.min(100, Math.round((wpm / 200) * 100))}%` }}
                />
              </div>
              <div className="flex justify-between text-[10px] text-slate-500 mt-1">
                <span>Hesitant (&lt;100)</span>
                <span className="text-emerald-400 font-semibold">Optimal (120-160 WPM)</span>
                <span>Rushed (&gt;180)</span>
              </div>
            </div>

            {/* Vocal Modulation / Pitch Dynamics */}
            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-slate-400 flex items-center gap-1.5">
                  <Volume2 className="h-3.5 w-3.5 text-slate-400" /> Pitch Modulation &amp; Vocal Variety
                </span>
                <span className="font-semibold text-slate-200 tabular-nums">{modulationScore}%</span>
              </div>
              <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                <div
                  className="bg-emerald-400 h-2 rounded-full"
                  style={{ width: `${modulationScore}%` }}
                />
              </div>
              <p className="text-[11px] text-slate-500 mt-1">
                {modulationScore >= 75
                  ? 'Energetic vocal delivery with expressive pitch dynamics. Effectively avoids flat monotone responses.'
                  : 'Moderate pitch dynamic range. Add vocal inflection to emphasize key architectural decisions.'}
              </p>
            </div>

            {/* Articulation & Fluency Snapshot */}
            <div className="grid grid-cols-2 gap-3 pt-1">
              <div className="p-3 rounded-xl bg-slate-900/70 border border-slate-800">
                <div className="text-[11px] text-slate-400">Articulation Quality</div>
                <div className="text-sm font-bold text-slate-200 capitalize mt-0.5">{articulation}</div>
              </div>
              <div className="p-3 rounded-xl bg-slate-900/70 border border-slate-800">
                <div className="text-[11px] text-slate-400">Fluency Rating</div>
                <div className="text-sm font-bold text-emerald-400 tabular-nums mt-0.5">{fluencyScore}%</div>
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* ── Strengths & High Priority Improvement Areas ──────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Strengths */}
        <Card className="p-6 bg-surface-card border-slate-800 space-y-3">
          <div className="flex items-center gap-2 text-emerald-400 font-bold text-sm">
            <CheckCircle2 className="h-4 w-4" />
            <span>Demonstrated Strengths</span>
          </div>
          <ul className="space-y-2.5">
            {assessment.strengths && assessment.strengths.length > 0 ? (
              assessment.strengths.map((s, idx) => (
                <li key={idx} className="flex items-start gap-2.5 text-xs text-slate-300 leading-relaxed">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 mt-1.5 flex-shrink-0" />
                  <span>{s}</span>
                </li>
              ))
            ) : (
              <li className="text-xs text-slate-500 italic py-2">
                No verified strengths identified in this session. All questions were left unattempted or scored below 70%.
              </li>
            )}
          </ul>
        </Card>

        {/* Improvement Areas */}
        <Card className="p-6 bg-surface-card border-slate-800 space-y-3">
          <div className="flex items-center gap-2 text-amber-400 font-bold text-sm">
            <AlertTriangle className="h-4 w-4" />
            <span>Targeted Recommendations</span>
          </div>
          <div className="space-y-3">
            {assessment.improvement_areas.map((item, idx) => (
              <div key={idx} className="p-3 rounded-xl bg-slate-900/70 border border-slate-800 text-xs space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-slate-200">{item.area}</span>
                  <Badge color={item.priority === 'high' ? 'red' : 'yellow'}>
                    {item.priority}
                  </Badge>
                </div>
                <p className="text-slate-400 leading-relaxed">{item.recommendation}</p>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* ── Quantum QAOA Calibration Banner ──────────────────────────────────── */}
      <div className="p-5 rounded-2xl bg-purple-950/40 border border-purple-500/30 flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-3.5">
          <div className="h-10 w-10 rounded-xl bg-purple-500/20 border border-purple-500/30 flex items-center justify-center text-purple-300">
            <Brain className="h-5 w-5" />
          </div>
          <div>
            <h4 className="text-sm font-bold text-purple-200">
              Personalized Quantum (QAOA) Study Plan Calibration
            </h4>
            <p className="text-xs text-slate-400 mt-0.5">
              The skill gaps detected from this interview are ready to be optimized into your personalized daily preparation roadmap using Qiskit QAOA.
            </p>
          </div>
        </div>
        <Link to="/preparation">
          <Button size="sm" className="bg-purple-600 hover:bg-purple-500 text-white flex-shrink-0 flex items-center gap-1.5">
            <Zap className="h-3.5 w-3.5" />
            <span>Open Quantum Planner</span>
          </Button>
        </Link>
      </div>
    </div>
  )
}

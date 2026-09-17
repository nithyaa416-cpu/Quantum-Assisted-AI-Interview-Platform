/**
 * Skill gap visualisation.
 * Shows required skills for the primary role split into
 * "already have" (green) vs "missing" (red/amber) buckets,
 * plus a coverage ring.
 */
import { CheckCircle2, XCircle, Target } from 'lucide-react'
import { clsx } from 'clsx'
import type { SkillGapResult } from '@/types'
import { ScoreRing } from '@/components/ui/ScoreRing'

interface SkillGapChartProps {
  gap: SkillGapResult
}

export function SkillGapChart({ gap }: SkillGapChartProps) {
  const coverage = gap.coverage / 100

  return (
    <div className="space-y-6">
      {/* Summary row */}
      <div className="flex items-center gap-6 p-4 rounded-2xl bg-surface border border-surface-border">
        <ScoreRing score={coverage} size={80} label="Coverage" color="#6366f1" />
        <div className="flex-1 min-w-0 space-y-1.5">
          <p className="text-base font-semibold text-slate-100">
            Skill Coverage for {gap.role.role_name}
          </p>
          <div className="flex flex-wrap gap-3 text-sm">
            <span className="flex items-center gap-1.5 text-emerald-400">
              <CheckCircle2 className="h-4 w-4" />
              {gap.present_skills.length} skills present
            </span>
            <span className="flex items-center gap-1.5 text-red-400">
              <XCircle className="h-4 w-4" />
              {gap.missing_skills.length} skills missing
            </span>
          </div>
          <div className="w-full bg-surface-border rounded-full h-2 mt-2">
            <div
              className="bg-brand-500 h-2 rounded-full transition-all duration-700"
              style={{ width: `${gap.coverage}%` }}
            />
          </div>
          <p className="text-xs text-slate-500">
            {gap.gap_percentage.toFixed(1)}% gap to close
          </p>
        </div>
      </div>

      {/* Present skills */}
      {gap.present_skills.length > 0 && (
        <div>
          <p className="text-xs font-medium text-emerald-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
            <CheckCircle2 className="h-3.5 w-3.5" /> Skills You Have ({gap.present_skills.length})
          </p>
          <div className="flex flex-wrap gap-2">
            {gap.present_skills.map(s => (
              <span key={s} className="px-2.5 py-1 rounded-lg bg-emerald-500/10 text-emerald-300 text-xs border border-emerald-500/20">
                {s}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Missing skills */}
      {gap.missing_skills.length > 0 && (
        <div>
          <p className="text-xs font-medium text-red-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
            <XCircle className="h-3.5 w-3.5" /> Skills to Develop ({gap.missing_skills.length})
          </p>
          <div className="flex flex-wrap gap-2">
            {gap.missing_skills.map(s => (
              <span key={s} className="px-2.5 py-1 rounded-lg bg-red-500/10 text-red-300 text-xs border border-red-500/20">
                {s}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Interview topics */}
      {gap.interview_topics.length > 0 && (
        <div>
          <p className="text-xs font-medium text-brand-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
            <Target className="h-3.5 w-3.5" /> Interview Topics ({gap.interview_topics.length})
          </p>
          <div className="flex flex-wrap gap-2">
            {gap.interview_topics.map(t => (
              <span key={t} className="px-2.5 py-1 rounded-lg bg-brand-500/10 text-brand-300 text-xs border border-brand-500/20">
                {t}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

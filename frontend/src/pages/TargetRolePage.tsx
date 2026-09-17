import { useState } from 'react'
import {
  Target, Star, Trash2, Crown, Plus,
  BookOpen, Code2, ChevronDown, ChevronUp, AlertCircle,
} from 'lucide-react'
import { clsx } from 'clsx'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { EmptyState } from '@/components/ui/EmptyState'
import { Spinner } from '@/components/ui/Spinner'
import { DomainBadge } from '@/components/target-role/DomainBadge'
import { RoleCataloguePicker } from '@/components/target-role/RoleCataloguePicker'
import { SkillGapChart } from '@/components/target-role/SkillGapChart'
import {
  useTargetRoles, useSkillGap,
  useCreateTargetRole, useDeleteTargetRole, useSetPrimaryRole,
} from '@/hooks/useTargetRoles'
import type { TargetRoleDetail, RoleCatalogueEntry } from '@/types'

// ── Role card ─────────────────────────────────────────────────────────────────
function RoleCard({
  role,
  onSetPrimary,
  onDelete,
  onViewGap,
  isGapSelected,
}: {
  role: TargetRoleDetail
  onSetPrimary: () => void
  onDelete: () => void
  onViewGap: () => void
  isGapSelected: boolean
}) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className={clsx(
      'card p-5 transition-all duration-200',
      role.is_primary && 'ring-1 ring-brand-500/40',
    )}>
      {/* Header row */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3 min-w-0">
          <div className={clsx(
            'p-2 rounded-xl flex-shrink-0',
            role.is_primary ? 'bg-brand-500/15' : 'bg-surface-hover',
          )}>
            <Target className={clsx('h-5 w-5', role.is_primary ? 'text-brand-400' : 'text-slate-400')} />
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <h3 className="text-sm font-semibold text-slate-100">{role.role_name}</h3>
              {role.is_primary && (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-brand-500/15 text-brand-300 text-xs border border-brand-500/25">
                  <Crown className="h-3 w-3" /> Primary
                </span>
              )}
            </div>
            <div className="flex items-center gap-2 mt-1">
              <DomainBadge domain={role.domain} />
              <span className="text-xs text-slate-600">
                Added {new Date(role.created_at).toLocaleDateString()}
              </span>
            </div>
            {role.role_description && (
              <p className="text-xs text-slate-500 mt-1.5 leading-relaxed">{role.role_description}</p>
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-1 flex-shrink-0">
          {!role.is_primary && (
            <button
              onClick={onSetPrimary}
              title="Set as primary"
              className="p-2 rounded-lg text-slate-400 hover:text-brand-400 hover:bg-brand-400/10 transition-colors"
            >
              <Star className="h-4 w-4" />
            </button>
          )}
          <button
            onClick={onViewGap}
            title="View skill gap"
            className={clsx(
              'p-2 rounded-lg transition-colors',
              isGapSelected
                ? 'bg-brand-500/15 text-brand-400'
                : 'text-slate-400 hover:text-brand-400 hover:bg-brand-400/10',
            )}
          >
            <BookOpen className="h-4 w-4" />
          </button>
          <button
            onClick={onDelete}
            title="Remove role"
            className="p-2 rounded-lg text-slate-400 hover:text-red-400 hover:bg-red-400/10 transition-colors"
          >
            <Trash2 className="h-4 w-4" />
          </button>
          <button
            onClick={() => setExpanded(v => !v)}
            className="p-2 rounded-lg text-slate-400 hover:text-slate-200 transition-colors"
          >
            {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </button>
        </div>
      </div>

      {/* Expandable detail */}
      {expanded && (
        <div className="mt-4 pt-4 border-t border-surface-border space-y-4 animate-fade-in">
          {role.required_skills.length > 0 && (
            <div>
              <p className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-2">
                Required Skills
              </p>
              <div className="flex flex-wrap gap-1.5">
                {role.required_skills.map(s => (
                  <span key={s} className="px-2 py-0.5 rounded-md bg-surface text-slate-300 text-xs border border-surface-border">
                    {s}
                  </span>
                ))}
              </div>
            </div>
          )}

          {role.interview_topics.length > 0 && (
            <div>
              <p className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <BookOpen className="h-3 w-3" /> Interview Topics
              </p>
              <div className="flex flex-wrap gap-1.5">
                {role.interview_topics.map(t => (
                  <span key={t} className="px-2 py-0.5 rounded-md bg-brand-500/10 text-brand-300 text-xs border border-brand-500/20">
                    {t}
                  </span>
                ))}
              </div>
            </div>
          )}

          {role.coding_topics.length > 0 && (
            <div>
              <p className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <Code2 className="h-3 w-3" /> Coding Topics
              </p>
              <div className="flex flex-wrap gap-1.5">
                {role.coding_topics.map(t => (
                  <span key={t} className="px-2 py-0.5 rounded-md bg-purple-500/10 text-purple-300 text-xs border border-purple-500/20">
                    {t}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ── Add role panel ────────────────────────────────────────────────────────────
function AddRolePanel({ onClose }: { onClose: () => void }) {
  const [selected, setSelected] = useState<{ name: string; domain: string } | null>(null)
  const { mutate: create, isPending } = useCreateTargetRole()

  const handleSelect = (role: RoleCatalogueEntry | null, customName?: string) => {
    if (role) {
      setSelected({ name: role.display_name, domain: role.domain })
    } else if (customName) {
      setSelected({ name: customName, domain: 'other' })
    }
  }

  const handleAdd = () => {
    if (!selected) return
    create(
      { role_name: selected.name, domain: selected.domain },
      { onSuccess: () => { setSelected(null); onClose() } },
    )
  }

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-5">
        <h2 className="text-base font-semibold text-slate-100 flex items-center gap-2">
          <Plus className="h-4 w-4 text-brand-400" />
          Add Target Role
        </h2>
        <button
          onClick={onClose}
          className="text-xs text-slate-500 hover:text-slate-300 transition-colors px-3 py-1.5 rounded-lg border border-surface-border"
        >
          Cancel
        </button>
      </div>

      <RoleCataloguePicker
        onSelect={handleSelect}
        selectedName={selected?.name}
        disabled={isPending}
      />

      {selected && (
        <div className="mt-4 pt-4 border-t border-surface-border">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-sm text-slate-300">Selected:</span>
              <span className="text-sm font-semibold text-brand-300">{selected.name}</span>
              <DomainBadge domain={selected.domain} />
            </div>
            <Button
              onClick={handleAdd}
              loading={isPending}
              icon={<Plus className="h-4 w-4" />}
              size="sm"
            >
              Add Role
            </Button>
          </div>
        </div>
      )}
    </Card>
  )
}

// ── Skill gap panel ───────────────────────────────────────────────────────────
function SkillGapPanel({ roleId }: { roleId: string }) {
  const { data: gap, isLoading, isError } = useSkillGap(roleId)

  if (isLoading) return (
    <Card className="p-6">
      <div className="flex justify-center py-6"><Spinner /></div>
    </Card>
  )

  if (isError || !gap) return (
    <Card className="p-6">
      <div className="flex items-center gap-2 text-amber-400 text-sm">
        <AlertCircle className="h-4 w-4" />
        Could not load skill gap analysis. Upload your resume first so skills can be compared.
      </div>
    </Card>
  )

  return (
    <Card className="p-6">
      <h2 className="text-base font-semibold text-slate-100 mb-5 flex items-center gap-2">
        <BookOpen className="h-4 w-4 text-brand-400" />
        Skill Gap Analysis
      </h2>
      <SkillGapChart gap={gap} />
    </Card>
  )
}

// ── Main page ─────────────────────────────────────────────────────────────────
export default function TargetRolePage() {
  const { data: roles = [], isLoading } = useTargetRoles()
  const { mutate: deleteRole } = useDeleteTargetRole()
  const { mutate: setPrimary } = useSetPrimaryRole()

  const [showAddPanel, setShowAddPanel] = useState(false)
  const [selectedGapRoleId, setSelectedGapRoleId] = useState<string | null>(null)

  const handleDelete = (id: string, name: string) => {
    if (!confirm(`Remove "${name}" from your target roles?`)) return
    if (selectedGapRoleId === id) setSelectedGapRoleId(null)
    deleteRole(id)
  }

  const handleViewGap = (id: string) =>
    setSelectedGapRoleId(prev => prev === id ? null : id)

  const primaryRole = roles.find(r => r.is_primary)

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-slide-up">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Target Roles</h1>
          <p className="text-slate-400 text-sm mt-1">
            Set the roles you're preparing for. The AI interviewer tailors questions to your primary role.
          </p>
        </div>
        {!showAddPanel && (
          <Button
            onClick={() => setShowAddPanel(true)}
            icon={<Plus className="h-4 w-4" />}
          >
            Add Role
          </Button>
        )}
      </div>

      {/* Primary role banner */}
      {primaryRole && !showAddPanel && (
        <div className="flex items-center gap-4 p-4 rounded-2xl bg-brand-500/10 border border-brand-500/25">
          <div className="p-2.5 rounded-xl bg-brand-500/20">
            <Crown className="h-5 w-5 text-brand-400" />
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-xs text-brand-400 font-medium uppercase tracking-wider">Primary Role</p>
            <p className="text-sm font-semibold text-slate-100 mt-0.5">{primaryRole.role_name}</p>
            <p className="text-xs text-slate-500 mt-0.5">
              AI interviews, coding rounds, and skill gap analysis are based on this role.
            </p>
          </div>
          <DomainBadge domain={primaryRole.domain} />
        </div>
      )}

      {/* Add role panel */}
      {showAddPanel && (
        <AddRolePanel onClose={() => setShowAddPanel(false)} />
      )}

      {/* Role list */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-base font-semibold text-slate-100">
            Your Roles
            {roles.length > 0 && (
              <span className="ml-2 text-sm font-normal text-slate-500">({roles.length})</span>
            )}
          </h2>
          {roles.length > 0 && (
            <p className="text-xs text-slate-500 flex items-center gap-1">
              <Star className="h-3 w-3 text-brand-400" /> Click star to set primary · book icon for skill gap
            </p>
          )}
        </div>

        {isLoading ? (
          <div className="flex justify-center py-12"><Spinner /></div>
        ) : roles.length === 0 ? (
          <Card className="p-6">
            <EmptyState
              title="No target roles yet"
              description="Add the roles you're preparing for. The AI will personalise your interviews and skill gap analysis."
              icon={<Target className="h-7 w-7" />}
              action={
                <Button
                  onClick={() => setShowAddPanel(true)}
                  icon={<Plus className="h-4 w-4" />}
                  size="sm"
                >
                  Add your first role
                </Button>
              }
            />
          </Card>
        ) : (
          <div className="space-y-3">
            {roles.map(role => (
              <RoleCard
                key={role.id}
                role={role}
                onSetPrimary={() => setPrimary(role.id)}
                onDelete={() => handleDelete(role.id, role.role_name)}
                onViewGap={() => handleViewGap(role.id)}
                isGapSelected={selectedGapRoleId === role.id}
              />
            ))}
          </div>
        )}
      </div>

      {/* Skill gap panel */}
      {selectedGapRoleId && (
        <SkillGapPanel roleId={selectedGapRoleId} />
      )}

      {/* How it's used section */}
      {roles.length > 0 && !showAddPanel && (
        <Card className="p-5">
          <p className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-3">
            How your target role is used
          </p>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            {[
              { icon: '🤖', title: 'AI Interviewer',    desc: 'Questions tailored to your role' },
              { icon: '💻', title: 'Coding Rounds',      desc: 'Problems relevant to your stack' },
              { icon: '📋', title: 'HR Questions',       desc: 'Behavioural focus per domain' },
              { icon: '📊', title: 'Skill Gap Analysis', desc: 'Required vs your current skills' },
              { icon: '🗺️', title: 'Prep Plan',          desc: 'Quantum-optimised study path' },
              { icon: '📝', title: 'Assessment Report',  desc: 'Feedback scoped to your role' },
            ].map(item => (
              <div key={item.title} className="flex items-start gap-2.5 p-3 rounded-xl bg-surface border border-surface-border">
                <span className="text-lg">{item.icon}</span>
                <div>
                  <p className="text-xs font-semibold text-slate-200">{item.title}</p>
                  <p className="text-xs text-slate-500 mt-0.5">{item.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  )
}

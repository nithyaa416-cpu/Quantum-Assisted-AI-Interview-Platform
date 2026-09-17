import { useState } from 'react'
import { Plus, X, Tag } from 'lucide-react'
import { clsx } from 'clsx'
import type { ResumeSkill } from '@/types'

const CATEGORY_COLORS: Record<string, string> = {
  language:     'bg-blue-500/15    text-blue-300    border-blue-500/25',
  frontend:     'bg-cyan-500/15    text-cyan-300    border-cyan-500/25',
  backend:      'bg-violet-500/15  text-violet-300  border-violet-500/25',
  database:     'bg-amber-500/15   text-amber-300   border-amber-500/25',
  devops_cloud: 'bg-orange-500/15  text-orange-300  border-orange-500/25',
  ml_ai:        'bg-pink-500/15    text-pink-300    border-pink-500/25',
  quantum:      'bg-purple-500/15  text-purple-300  border-purple-500/25',
  tools:        'bg-slate-500/15   text-slate-300   border-slate-500/25',
  soft_skill:   'bg-green-500/15   text-green-300   border-green-500/25',
  other:        'bg-slate-500/15   text-slate-400   border-slate-500/25',
}

interface SkillsEditorProps {
  skills: ResumeSkill[]
  onChange: (skills: ResumeSkill[]) => void
  readOnly?: boolean
}

export function SkillsEditor({ skills, onChange, readOnly = false }: SkillsEditorProps) {
  const [input, setInput] = useState('')

  const addSkill = () => {
    const name = input.trim()
    if (!name || skills.some((s) => s.name.toLowerCase() === name.toLowerCase())) {
      setInput('')
      return
    }
    onChange([...skills, { name, category: 'other', confidence: 'high' }])
    setInput('')
  }

  const removeSkill = (name: string) =>
    onChange(skills.filter((s) => s.name !== name))

  // Group by category
  const grouped = skills.reduce<Record<string, ResumeSkill[]>>((acc, s) => {
    const cat = s.category || 'other'
    acc[cat] = [...(acc[cat] ?? []), s]
    return acc
  }, {})

  return (
    <div className="space-y-4">
      {!readOnly && (
        <div className="flex gap-2">
          <input
            className="input-base flex-1 py-2 text-sm"
            placeholder="Add a skill (e.g. Python, Kubernetes)…"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') { e.preventDefault(); addSkill() }
            }}
          />
          <button
            type="button"
            onClick={addSkill}
            className="p-2.5 rounded-xl bg-brand-600 hover:bg-brand-700 text-white transition-colors"
          >
            <Plus className="h-4 w-4" />
          </button>
        </div>
      )}

      {Object.keys(grouped).length === 0 ? (
        <div className="flex items-center gap-2 py-4 text-slate-500 text-sm">
          <Tag className="h-4 w-4" />
          No skills extracted yet.
        </div>
      ) : (
        <div className="space-y-3">
          {Object.entries(grouped).map(([cat, catSkills]) => (
            <div key={cat}>
              <p className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-2">
                {cat.replace('_', ' ')}
              </p>
              <div className="flex flex-wrap gap-2">
                {catSkills.map((skill) => (
                  <span
                    key={skill.name}
                    className={clsx(
                      'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium border',
                      CATEGORY_COLORS[skill.category] ?? CATEGORY_COLORS.other,
                    )}
                  >
                    {skill.name}
                    {!readOnly && (
                      <button
                        type="button"
                        onClick={() => removeSkill(skill.name)}
                        className="opacity-60 hover:opacity-100 transition-opacity ml-0.5"
                      >
                        <X className="h-2.5 w-2.5" />
                      </button>
                    )}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      <p className="text-xs text-slate-600">
        {skills.length} skill{skills.length !== 1 ? 's' : ''} detected
      </p>
    </div>
  )
}

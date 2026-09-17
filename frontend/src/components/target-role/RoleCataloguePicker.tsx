/**
 * Role catalogue picker.
 * Shows a searchable grid of all supported roles.
 * Student can click a role to select it, or type a custom role name.
 */
import { useState } from 'react'
import { Search, Plus, Sparkles } from 'lucide-react'
import { clsx } from 'clsx'
import { useRoleCatalogue } from '@/hooks/useTargetRoles'
import { DomainBadge } from './DomainBadge'
import { Spinner } from '@/components/ui/Spinner'
import type { RoleCatalogueEntry } from '@/types'

const DOMAIN_FILTERS = [
  { value: '',                  label: 'All'        },
  { value: 'software_engineering', label: 'Software'   },
  { value: 'backend',           label: 'Backend'    },
  { value: 'frontend',          label: 'Frontend'   },
  { value: 'fullstack',         label: 'Full Stack' },
  { value: 'data_science',      label: 'Data'       },
  { value: 'machine_learning',  label: 'ML / AI'    },
  { value: 'devops',            label: 'DevOps'     },
  { value: 'mobile',            label: 'Mobile'     },
]

interface RoleCataloguePickerProps {
  onSelect: (role: RoleCatalogueEntry | null, customName?: string) => void
  selectedName?: string
  disabled?: boolean
}

export function RoleCataloguePicker({ onSelect, selectedName, disabled }: RoleCataloguePickerProps) {
  const [search, setSearch]         = useState('')
  const [domainFilter, setDomain]   = useState('')

  const { data, isLoading } = useRoleCatalogue(
    search || domainFilter
      ? { q: search || undefined, domain: domainFilter || undefined }
      : undefined
  )

  const roles = data?.roles ?? []

  const handleSelect = (role: RoleCatalogueEntry) => {
    if (disabled) return
    onSelect(role)
  }

  const handleCustom = () => {
    if (!search.trim() || disabled) return
    onSelect(null, search.trim())
    setSearch('')
  }

  const isCustomInput = search.trim() &&
    !roles.some(r => r.display_name.toLowerCase() === search.trim().toLowerCase())

  return (
    <div className="space-y-4">
      {/* Search input */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
        <input
          className="input-base pl-9 py-2.5 text-sm"
          placeholder="Search roles or type a custom role…"
          value={search}
          onChange={e => setSearch(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && isCustomInput && handleCustom()}
          disabled={disabled}
        />
      </div>

      {/* Domain filter pills */}
      <div className="flex flex-wrap gap-1.5">
        {DOMAIN_FILTERS.map(f => (
          <button
            key={f.value}
            onClick={() => setDomain(f.value)}
            disabled={disabled}
            className={clsx(
              'px-3 py-1 rounded-full text-xs font-medium transition-colors border',
              domainFilter === f.value
                ? 'bg-brand-600 text-white border-brand-600'
                : 'bg-surface border-surface-border text-slate-400 hover:text-slate-200 hover:border-slate-500',
            )}
          >
            {f.label}
          </button>
        ))}
      </div>

      {/* Custom role prompt */}
      {isCustomInput && (
        <button
          onClick={handleCustom}
          disabled={disabled}
          className="w-full flex items-center gap-2 p-3 rounded-xl border border-dashed border-brand-500/40 bg-brand-500/5 hover:bg-brand-500/10 transition-colors text-sm text-brand-400"
        >
          <Plus className="h-4 w-4 flex-shrink-0" />
          <span>Add custom role: <strong>"{search.trim()}"</strong></span>
        </button>
      )}

      {/* Catalogue grid */}
      {isLoading ? (
        <div className="flex justify-center py-8"><Spinner /></div>
      ) : roles.length === 0 && !isCustomInput ? (
        <p className="text-center text-slate-500 text-sm py-6">No roles found.</p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-96 overflow-y-auto pr-1">
          {roles.map(role => {
            const isSelected = role.display_name === selectedName
            return (
              <button
                key={role.display_name}
                onClick={() => handleSelect(role)}
                disabled={disabled}
                className={clsx(
                  'flex flex-col items-start gap-1.5 p-3.5 rounded-xl border text-left transition-all duration-150',
                  isSelected
                    ? 'bg-brand-600/15 border-brand-500/50 ring-1 ring-brand-500/30'
                    : 'bg-surface border-surface-border hover:bg-surface-hover hover:border-slate-500',
                  disabled && 'opacity-50 cursor-not-allowed',
                )}
              >
                <div className="flex items-start justify-between gap-2 w-full">
                  <span className="text-sm font-medium text-slate-200 leading-snug">
                    {role.display_name}
                  </span>
                  {isSelected && <Sparkles className="h-3.5 w-3.5 text-brand-400 flex-shrink-0 mt-0.5" />}
                </div>
                <DomainBadge domain={role.domain} />
                <p className="text-xs text-slate-500 leading-relaxed line-clamp-2">
                  {role.description}
                </p>
              </button>
            )
          })}
        </div>
      )}
    </div>
  )
}

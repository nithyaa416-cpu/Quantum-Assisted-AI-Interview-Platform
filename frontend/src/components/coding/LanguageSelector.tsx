/**
 * LanguageSelector — dropdown to pick Python / Java / C++.
 *
 * When the user switches language:
 *  - Syntax highlighting updates immediately.
 *  - If code has NOT been edited from the starter, starter code loads.
 *  - If code HAS been edited, a confirmation dialog is shown first.
 */
import { ChevronDown, Code2 } from 'lucide-react'
import { clsx } from 'clsx'
import { CODING_LANGUAGES } from '@/types/coding'
import type { CodingLanguage } from '@/types/coding'

interface LanguageSelectorProps {
  selected: CodingLanguage
  onChange: (lang: CodingLanguage) => void
  disabled?: boolean
}

export function LanguageSelector({ selected, onChange, disabled }: LanguageSelectorProps) {
  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const lang = CODING_LANGUAGES.find(l => l.id === e.target.value)
    if (lang) onChange(lang)
  }

  return (
    <div className="relative flex items-center gap-2">
      <Code2 className="h-4 w-4 text-slate-500 flex-shrink-0" />
      <div className="relative">
        <select
          value={selected.id}
          onChange={handleChange}
          disabled={disabled}
          className={clsx(
            'appearance-none bg-surface border border-surface-border rounded-lg',
            'pl-3 pr-8 py-1.5 text-sm font-medium text-slate-200',
            'focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500',
            'transition-colors cursor-pointer',
            disabled && 'opacity-50 cursor-not-allowed',
          )}
        >
          {CODING_LANGUAGES.map((lang) => (
            <option key={lang.id} value={lang.id}>
              {lang.name}
            </option>
          ))}
        </select>
        <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-400 pointer-events-none" />
      </div>
    </div>
  )
}

import { ReactNode } from 'react'
import { clsx } from 'clsx'

type BadgeColor = 'indigo' | 'green' | 'yellow' | 'red' | 'slate' | 'purple'

const colorMap: Record<BadgeColor, string> = {
  indigo: 'bg-brand-500/15 text-brand-300 ring-1 ring-brand-500/30',
  green:  'bg-emerald-500/15 text-emerald-300 ring-1 ring-emerald-500/30',
  yellow: 'bg-amber-500/15 text-amber-300 ring-1 ring-amber-500/30',
  red:    'bg-red-500/15 text-red-300 ring-1 ring-red-500/30',
  slate:  'bg-slate-500/15 text-slate-300 ring-1 ring-slate-500/30',
  purple: 'bg-purple-500/15 text-purple-300 ring-1 ring-purple-500/30',
}

interface BadgeProps {
  color?: BadgeColor
  children: ReactNode
  className?: string
}

export function Badge({ color = 'indigo', children, className }: BadgeProps) {
  return (
    <span className={clsx('badge', colorMap[color], className)}>
      {children}
    </span>
  )
}

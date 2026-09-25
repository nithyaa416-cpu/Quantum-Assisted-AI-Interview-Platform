import { clsx } from 'clsx'
import { CheckCircle2, Clock, Loader2, XCircle } from 'lucide-react'
import type { ParseStatus } from '@/types'

interface ParseStatusBadgeProps {
  status: ParseStatus
  className?: string
}

const config = {
  pending:    { icon: Clock,        color: 'text-brand-400  bg-brand-400/10  border-brand-400/20',  label: 'Ready for Interview' },
  processing: { icon: Loader2,      color: 'text-blue-400   bg-blue-400/10   border-blue-400/20',   label: 'Extracting' },
  completed:  { icon: CheckCircle2, color: 'text-emerald-400 bg-emerald-400/10 border-emerald-400/20', label: 'Parsed' },
  failed:     { icon: XCircle,      color: 'text-red-400    bg-red-400/10    border-red-400/20',    label: 'Failed' },
}

export function ParseStatusBadge({ status, className }: ParseStatusBadgeProps) {
  const { icon: Icon, color, label } = config[status] ?? config.pending
  return (
    <span className={clsx(
      'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border',
      color, className,
    )}>
      <Icon className={clsx('h-3 w-3', status === 'processing' && 'animate-spin')} />
      {label}
    </span>
  )
}

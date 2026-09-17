import { clsx } from 'clsx'

const DOMAIN_CONFIG: Record<string, { label: string; color: string }> = {
  software_engineering: { label: 'Software Eng.',  color: 'bg-blue-500/15   text-blue-300   border-blue-500/25'   },
  data_science:         { label: 'Data Science',   color: 'bg-amber-500/15  text-amber-300  border-amber-500/25'  },
  machine_learning:     { label: 'ML / AI',         color: 'bg-pink-500/15   text-pink-300   border-pink-500/25'   },
  devops:               { label: 'DevOps / Cloud',  color: 'bg-orange-500/15 text-orange-300 border-orange-500/25' },
  frontend:             { label: 'Frontend',        color: 'bg-cyan-500/15   text-cyan-300   border-cyan-500/25'   },
  backend:              { label: 'Backend',         color: 'bg-violet-500/15 text-violet-300 border-violet-500/25' },
  fullstack:            { label: 'Full Stack',      color: 'bg-indigo-500/15 text-indigo-300 border-indigo-500/25' },
  mobile:               { label: 'Mobile',          color: 'bg-green-500/15  text-green-300  border-green-500/25'  },
  cybersecurity:        { label: 'Cybersecurity',   color: 'bg-red-500/15    text-red-300    border-red-500/25'    },
  product_management:   { label: 'Product Mgmt.',   color: 'bg-teal-500/15   text-teal-300   border-teal-500/25'   },
  other:                { label: 'Other',            color: 'bg-slate-500/15  text-slate-300  border-slate-500/25'  },
}

interface DomainBadgeProps {
  domain: string
  className?: string
}

export function DomainBadge({ domain, className }: DomainBadgeProps) {
  const cfg = DOMAIN_CONFIG[domain] ?? DOMAIN_CONFIG.other
  return (
    <span className={clsx(
      'inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border',
      cfg.color, className,
    )}>
      {cfg.label}
    </span>
  )
}

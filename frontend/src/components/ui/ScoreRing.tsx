interface ScoreRingProps {
  score: number        // 0–1
  size?: number
  label?: string
  color?: string
}

export function ScoreRing({ score, size = 80, label, color = '#6366f1' }: ScoreRingProps) {
  const pct   = Math.min(Math.max(score, 0), 1)
  const r     = (size - 8) / 2
  const circ  = 2 * Math.PI * r
  const dash  = pct * circ

  return (
    <div className="flex flex-col items-center gap-1">
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="#1e293b" strokeWidth={8} />
        <circle
          cx={size/2} cy={size/2} r={r}
          fill="none"
          stroke={color}
          strokeWidth={8}
          strokeDasharray={`${dash} ${circ}`}
          strokeLinecap="round"
          transform={`rotate(-90 ${size/2} ${size/2})`}
          style={{ transition: 'stroke-dasharray 0.6s ease' }}
        />
        <text x="50%" y="50%" dominantBaseline="middle" textAnchor="middle" fontSize={size * 0.22} fontWeight="700" fill="#f1f5f9">
          {Math.round(pct * 100)}
        </text>
      </svg>
      {label && <span className="text-xs text-slate-400 text-center">{label}</span>}
    </div>
  )
}

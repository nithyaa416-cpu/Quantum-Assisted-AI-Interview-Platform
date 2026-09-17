import { Brain, Zap } from 'lucide-react'
import { Card } from '@/components/ui/Card'
import { EmptyState } from '@/components/ui/EmptyState'
import { Badge } from '@/components/ui/Badge'

export default function PreparationPage() {
  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-slide-up">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Preparation Plan</h1>
          <p className="text-slate-400 text-sm mt-1">Your quantum-optimised interview study roadmap.</p>
        </div>
        <Badge color="purple">Phase 3</Badge>
      </div>

      <Card className="p-6">
        <EmptyState
          title="QAOA Prep Planner coming in Phase 3"
          description="After uploading your resume, the QAOA algorithm will generate a personalised study plan based on your skill gaps, target role, and available preparation time."
          icon={<Brain className="h-7 w-7" />}
          action={
            <div className="flex items-center gap-2 text-xs text-slate-500">
              <Zap className="h-3.5 w-3.5 text-brand-400" />
              Powered by Qiskit · Quantum Approximate Optimisation Algorithm
            </div>
          }
        />
      </Card>
    </div>
  )
}

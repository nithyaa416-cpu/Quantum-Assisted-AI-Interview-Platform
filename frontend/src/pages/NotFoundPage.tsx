import { Link } from 'react-router-dom'
import { Home, AlertTriangle } from 'lucide-react'
import { Button } from '@/components/ui/Button'

export default function NotFoundPage() {
  return (
    <div className="min-h-screen bg-surface flex items-center justify-center p-6">
      <div className="text-center max-w-md animate-slide-up">
        <div className="flex justify-center mb-6">
          <div className="p-4 rounded-2xl bg-surface-card border border-surface-border">
            <AlertTriangle className="h-10 w-10 text-amber-400" />
          </div>
        </div>
        <h1 className="text-5xl font-bold text-slate-100 mb-2">404</h1>
        <h2 className="text-xl font-semibold text-slate-200 mb-3">Page not found</h2>
        <p className="text-slate-400 text-sm mb-8">
          The page you're looking for doesn't exist or has been moved.
        </p>
        <Link to="/dashboard">
          <Button icon={<Home className="h-4 w-4" />}>Back to Dashboard</Button>
        </Link>
      </div>
    </div>
  )
}

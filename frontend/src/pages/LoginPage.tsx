import { useState } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import toast from 'react-hot-toast'
import { Mail, Lock, Eye, EyeOff, AlertCircle, KeyRound, CheckCircle2 } from 'lucide-react'
import { AuthShell } from '@/components/auth/AuthShell'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { authService } from '@/services/authService'
import { useAuthStore } from '@/store/authStore'
import type { LoginFormData } from '@/types'
import { getApiErrorMessage } from '@/utils/errors'
import api from '@/services/api'

// ── Password reset panel (inline, no email required) ────────────────────────
function ResetPasswordPanel({ onCancel }: { onCancel: () => void }) {
  const [step, setStep]         = useState<'find' | 'reset' | 'done'>('find')
  const [email, setEmail]       = useState('')
  const [newPwd, setNewPwd]     = useState('')
  const [confirm, setConfirm]   = useState('')
  const [loading, setLoading]   = useState(false)
  const [error, setError]       = useState<string | null>(null)
  const [showPwd, setShowPwd]   = useState(false)

  const handleFind = async () => {
    if (!email.trim()) { setError('Enter your email address.'); return }
    setLoading(true); setError(null)
    try {
      // Check if email exists by attempting a login with dummy password —
      // 401 means account exists, 400 means email not found
      await api.post('/api/auth/login', { email: email.trim(), password: '___dummy___' })
    } catch (err: any) {
      const code = err?.response?.data?.error?.code
      const msg  = err?.response?.data?.error?.message ?? ''
      // If error is AUTH_FAILED, email exists → proceed to reset
      if (code === 'AUTH_FAILED' || msg.toLowerCase().includes('invalid')) {
        setStep('reset')
      } else {
        setError('No account found with that email address.')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleReset = async () => {
    if (newPwd.length < 8)         { setError('Password must be at least 8 characters.'); return }
    if (!/\d/.test(newPwd))        { setError('Password must contain at least one number.'); return }
    if (newPwd !== confirm)        { setError('Passwords do not match.'); return }
    if (/^[a-zA-Z0-9]*$/.test(newPwd) && newPwd.length < 10) {
      setError('Password is too simple. Add a special character or make it longer.')
      return
    }

    setLoading(true); setError(null)
    try {
      await api.post('/api/auth/reset-password/', { email: email.trim(), new_password: newPwd })
      setStep('done')
    } catch (err: any) {
      setError(getApiErrorMessage(err, 'Reset failed. Please try again.'))
    } finally {
      setLoading(false)
    }
  }

  if (step === 'done') return (
    <div className="space-y-4">
      <div className="flex flex-col items-center gap-3 py-4">
        <div className="h-12 w-12 rounded-full bg-emerald-500/15 flex items-center justify-center">
          <CheckCircle2 className="h-6 w-6 text-emerald-400" />
        </div>
        <p className="text-slate-200 font-medium text-center">Password reset successfully!</p>
        <p className="text-slate-500 text-sm text-center">You can now sign in with your new password.</p>
      </div>
      <button onClick={onCancel} className="w-full py-2.5 text-sm text-brand-400 hover:text-brand-300 transition-colors">
        ← Back to sign in
      </button>
    </div>
  )

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 mb-2">
        <KeyRound className="h-5 w-5 text-brand-400" />
        <h3 className="text-base font-semibold text-slate-100">Reset Password</h3>
      </div>

      {error && (
        <div className="flex items-start gap-2 p-3 rounded-xl bg-red-500/10 border border-red-500/25 text-red-400 text-sm">
          <AlertCircle className="h-4 w-4 flex-shrink-0 mt-0.5" />
          {error}
        </div>
      )}

      {step === 'find' && (
        <>
          <p className="text-slate-400 text-sm">Enter the email address you registered with.</p>
          <div>
            <label className="label">Email address</label>
            <input
              type="email"
              className="input-base"
              placeholder="you@example.com"
              value={email}
              onChange={e => setEmail(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleFind()}
              autoFocus
            />
          </div>
          <button
            onClick={handleFind}
            disabled={loading}
            className="btn-primary w-full"
          >
            {loading ? 'Checking…' : 'Continue'}
          </button>
        </>
      )}

      {step === 'reset' && (
        <>
          <p className="text-slate-400 text-sm">
            Account found for <span className="text-brand-400">{email}</span>. Set a new password.
          </p>
          <div>
            <label className="label">New password</label>
            <div className="relative">
              <input
                type={showPwd ? 'text' : 'password'}
                className="input-base pr-10"
                placeholder="Min 8 chars, at least 1 number"
                value={newPwd}
                onChange={e => setNewPwd(e.target.value)}
                autoFocus
              />
              <button type="button" onClick={() => setShowPwd(v => !v)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300">
                {showPwd ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
          </div>
          <div>
            <label className="label">Confirm new password</label>
            <input
              type={showPwd ? 'text' : 'password'}
              className="input-base"
              placeholder="Re-enter your password"
              value={confirm}
              onChange={e => setConfirm(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleReset()}
            />
          </div>
          <button onClick={handleReset} disabled={loading} className="btn-primary w-full">
            {loading ? 'Resetting…' : 'Reset Password'}
          </button>
        </>
      )}

      <button onClick={onCancel} className="w-full text-xs text-slate-500 hover:text-slate-300 transition-colors py-1">
        ← Back to sign in
      </button>
    </div>
  )
}

// ── Main login page ───────────────────────────────────────────────────────────
export default function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const setAuth  = useAuthStore((s) => s.setAuth)
  const from     = (location.state as { from?: { pathname: string } })?.from?.pathname ?? '/dashboard'

  const [showPassword, setShowPassword] = useState(false)
  const [serverError,  setServerError]  = useState<string | null>(null)
  const [showReset,    setShowReset]    = useState(false)

  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<LoginFormData>()

  const onSubmit = async (data: LoginFormData) => {
    setServerError(null)
    try {
      const { user, tokens } = await authService.login(data)
      setAuth(user, tokens.access, tokens.refresh)
      toast.success(`Welcome back, ${user.full_name.split(' ')[0]}!`)
      navigate(from, { replace: true })
    } catch (err) {
      setServerError(getApiErrorMessage(err, 'Invalid email or password.'))
    }
  }

  return (
    <AuthShell title="Welcome back" subtitle="Sign in to your QAIP account">
      {showReset ? (
        <ResetPasswordPanel onCancel={() => { setShowReset(false); setServerError(null) }} />
      ) : (
        <>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5" noValidate>
            {/* Error banner */}
            {serverError && (
              <div className="space-y-2">
                <div className="flex items-start gap-2.5 p-3.5 rounded-xl bg-red-500/10 border border-red-500/25 text-red-400 text-sm">
                  <AlertCircle className="h-4 w-4 flex-shrink-0 mt-0.5" />
                  <div>
                    <p>{serverError}</p>
                    <button
                      type="button"
                      onClick={() => setShowReset(true)}
                      className="mt-1 text-brand-400 hover:text-brand-300 text-xs underline transition-colors"
                    >
                      Forgot your password? Reset it here →
                    </button>
                  </div>
                </div>
              </div>
            )}

            <Input
              label="Email address"
              type="email"
              placeholder="you@example.com"
              icon={<Mail className="h-4 w-4" />}
              error={errors.email?.message}
              autoComplete="email"
              {...register('email', {
                required: 'Email is required.',
                pattern: { value: /^\S+@\S+\.\S+$/, message: 'Enter a valid email.' },
              })}
            />

            <div>
              <Input
                label="Password"
                type={showPassword ? 'text' : 'password'}
                placeholder="••••••••"
                icon={<Lock className="h-4 w-4" />}
                error={errors.password?.message}
                autoComplete="current-password"
                {...register('password', { required: 'Password is required.' })}
              />
              <div className="flex items-center justify-between mt-1.5">
                <button
                  type="button"
                  onClick={() => setShowPassword(v => !v)}
                  className="flex items-center gap-1 text-xs text-slate-500 hover:text-slate-300 transition-colors"
                >
                  {showPassword ? <EyeOff className="h-3 w-3" /> : <Eye className="h-3 w-3" />}
                  {showPassword ? 'Hide' : 'Show'} password
                </button>
                <button
                  type="button"
                  onClick={() => setShowReset(true)}
                  className="text-xs text-slate-500 hover:text-brand-400 transition-colors"
                >
                  Forgot password?
                </button>
              </div>
            </div>

            <Button type="submit" loading={isSubmitting} className="w-full mt-2">
              Sign in
            </Button>
          </form>

          <p className="mt-6 text-center text-sm text-slate-500">
            Don't have an account?{' '}
            <Link to="/register" className="text-brand-400 hover:text-brand-300 font-medium transition-colors">
              Create one
            </Link>
          </p>
        </>
      )}
    </AuthShell>
  )
}

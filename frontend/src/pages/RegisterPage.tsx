import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import toast from 'react-hot-toast'
import { Mail, Lock, User, Eye, EyeOff, CheckCircle2, AlertCircle } from 'lucide-react'
import { AuthShell } from '@/components/auth/AuthShell'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { authService } from '@/services/authService'
import { useAuthStore } from '@/store/authStore'
import type { RegisterFormData } from '@/types'
import { getFieldErrors, getApiErrorMessage } from '@/utils/errors'

const passwordRules = [
  { label: 'At least 8 characters',        test: (p: string) => p.length >= 8 },
  { label: 'Contains a number',             test: (p: string) => /\d/.test(p) },
  { label: 'Not all numeric',               test: (p: string) => !/^\d+$/.test(p) },
  { label: 'Not a commonly used password',  test: (p: string) => p.length >= 10 || /[^a-zA-Z0-9]/.test(p) },
]

export default function RegisterPage() {
  const navigate = useNavigate()
  const setAuth = useAuthStore((s) => s.setAuth)
  const [showPassword, setShowPassword] = useState(false)
  const [serverError, setServerError] = useState<string | null>(null)

  const {
    register,
    handleSubmit,
    watch,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<RegisterFormData>()

  const password = watch('password', '')

  const onSubmit = async (data: RegisterFormData) => {
    setServerError(null)
    try {
      const { user, tokens } = await authService.register(data)
      setAuth(user, tokens.access, tokens.refresh)
      toast.success(`Account created! Welcome, ${user.full_name.split(' ')[0]}!`)
      navigate('/dashboard', { replace: true })
    } catch (err) {
      // Map backend field errors onto form fields so they show inline
      const fieldErrors = getFieldErrors(err)

      if (fieldErrors.email) {
        setError('email', { message: fieldErrors.email })
      }
      if (fieldErrors.password) {
        setError('password', { message: fieldErrors.password })
      }
      if (fieldErrors.confirm_password) {
        setError('confirm_password', { message: fieldErrors.confirm_password })
      }
      if (fieldErrors.full_name) {
        setError('full_name', { message: fieldErrors.full_name })
      }

      // Show a general server error banner if no field errors were mapped
      const hasFieldErrors = Object.keys(fieldErrors).length > 0
      if (!hasFieldErrors) {
        setServerError(getApiErrorMessage(err, 'Registration failed. Please try again.'))
      }
    }
  }

  return (
    <AuthShell title="Create your account" subtitle="Start your interview preparation journey">
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-5" noValidate>

        {/* Server-level error banner */}
        {serverError && (
          <div className="flex items-start gap-2.5 p-3.5 rounded-xl bg-red-500/10 border border-red-500/25 text-red-400 text-sm">
            <AlertCircle className="h-4 w-4 flex-shrink-0 mt-0.5" />
            {serverError}
          </div>
        )}
        <Input
          label="Full name"
          type="text"
          placeholder="Arjun Kumar"
          icon={<User className="h-4 w-4" />}
          error={errors.full_name?.message}
          autoComplete="name"
          {...register('full_name', {
            required: 'Full name is required.',
            minLength: { value: 2, message: 'Name must be at least 2 characters.' },
          })}
        />

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
            placeholder="Min 8 chars, avoid common words"
            icon={<Lock className="h-4 w-4" />}
            error={errors.password?.message}
            autoComplete="new-password"
            {...register('password', {
              required: 'Password is required.',
              minLength: { value: 8, message: 'At least 8 characters required.' },
              validate: (v) => /\d/.test(v) || 'Password must contain at least one number.',
            })}
          />
          <button
            type="button"
            onClick={() => setShowPassword((v) => !v)}
            className="mt-1.5 flex items-center gap-1 text-xs text-slate-500 hover:text-slate-300 transition-colors"
          >
            {showPassword ? <EyeOff className="h-3 w-3" /> : <Eye className="h-3 w-3" />}
            {showPassword ? 'Hide' : 'Show'} password
          </button>

          {/* Live password strength checklist */}
          {password && (
            <ul className="mt-2 space-y-1">
              {passwordRules.map((rule) => (
                <li key={rule.label} className="flex items-center gap-1.5 text-xs">
                  <CheckCircle2
                    className={`h-3.5 w-3.5 ${rule.test(password) ? 'text-emerald-400' : 'text-slate-600'}`}
                  />
                  <span className={rule.test(password) ? 'text-emerald-400' : 'text-slate-500'}>
                    {rule.label}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>

        <Input
          label="Confirm password"
          type={showPassword ? 'text' : 'password'}
          placeholder="Re-enter your password"
          icon={<Lock className="h-4 w-4" />}
          error={errors.confirm_password?.message}
          autoComplete="new-password"
          {...register('confirm_password', {
            required: 'Please confirm your password.',
            validate: (v) => v === password || 'Passwords do not match.',
          })}
        />

        <Button type="submit" loading={isSubmitting} className="w-full mt-2">
          Create account
        </Button>
      </form>

      <p className="mt-6 text-center text-sm text-slate-500">
        Already have an account?{' '}
        <Link to="/login" className="text-brand-400 hover:text-brand-300 font-medium transition-colors">
          Sign in
        </Link>
      </p>
    </AuthShell>
  )
}

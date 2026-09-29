import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import toast from 'react-hot-toast'
import {
  Mail, Lock, User, Eye, EyeOff, CheckCircle2,
  AlertCircle, KeyRound, ArrowLeft, RefreshCw,
} from 'lucide-react'
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

  // OTP flow state
  const [step, setStep] = useState<'details' | 'otp'>('details')
  const [isSendingOtp, setIsSendingOtp] = useState(false)
  const [countdown, setCountdown] = useState(0)

  const {
    register,
    handleSubmit,
    watch,
    setError,
    trigger,
    getValues,
    formState: { errors, isSubmitting },
  } = useForm<RegisterFormData>()

  const password = watch('password', '')
  const email = watch('email', '')

  // Countdown timer for OTP resend cooldown
  useEffect(() => {
    if (countdown <= 0) return
    const timer = setInterval(() => {
      setCountdown((prev) => (prev > 0 ? prev - 1 : 0))
    }, 1000)
    return () => clearInterval(timer)
  }, [countdown])

  // Request or resend OTP
  const handleSendOtp = async () => {
    setServerError(null)

    // Validate details form first
    const isValid = await trigger(['full_name', 'email', 'password', 'confirm_password'])
    if (!isValid) return

    const currentEmail = getValues('email')
    setIsSendingOtp(true)
    try {
      const msg = await authService.sendOtp(currentEmail)
      toast.success(msg || 'Verification code sent to your email!')
      setStep('otp')
      setCountdown(60)
    } catch (err) {
      const fieldErrors = getFieldErrors(err)
      if (fieldErrors.email) {
        setError('email', { message: fieldErrors.email })
      } else {
        setServerError(getApiErrorMessage(err, 'Failed to send verification code.'))
      }
    } finally {
      setIsSendingOtp(false)
    }
  }

  // Final submission with OTP
  const onSubmit = async (data: RegisterFormData) => {
    setServerError(null)

    if (step === 'details') {
      await handleSendOtp()
      return
    }

    try {
      await authService.register(data)
      toast.success('Registration successful! Please sign in with your password.')
      navigate('/login', { replace: true, state: { email: data.email, registered: true } })
    } catch (err) {
      const fieldErrors = getFieldErrors(err)

      if (fieldErrors.otp) {
        setError('otp', { message: fieldErrors.otp })
      }
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

      const hasFieldErrors = Object.keys(fieldErrors).length > 0
      if (!hasFieldErrors) {
        setServerError(getApiErrorMessage(err, 'Registration failed. Please try again.'))
      }
    }
  }

  return (
    <AuthShell
      title={step === 'details' ? 'Create your account' : 'Verify your email'}
      subtitle={
        step === 'details'
          ? 'Start your interview preparation journey'
          : `We've sent a 6-digit code to ${email}`
      }
    >
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-5" noValidate>

        {/* Server-level error banner */}
        {serverError && (
          <div className="flex items-start gap-2.5 p-3.5 rounded-xl bg-red-500/10 border border-red-500/25 text-red-400 text-sm">
            <AlertCircle className="h-4 w-4 flex-shrink-0 mt-0.5" />
            {serverError}
          </div>
        )}

        {/* Stage 1: Account Details */}
        {step === 'details' ? (
          <>
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

            <Button
              type="button"
              onClick={handleSendOtp}
              loading={isSendingOtp}
              className="w-full mt-2"
            >
              Continue & Send Code
            </Button>
          </>
        ) : (
          /* Stage 2: OTP Verification */
          <div className="space-y-5 animate-fade-in">
            <div className="p-3.5 rounded-xl bg-surface-hover/70 border border-slate-700/60 text-xs text-slate-300 flex items-center justify-between">
              <span className="truncate">{email}</span>
              <button
                type="button"
                onClick={() => setStep('details')}
                className="text-brand-400 hover:text-brand-300 font-medium inline-flex items-center gap-1 ml-2 flex-shrink-0"
              >
                <ArrowLeft className="h-3 w-3" /> Change
              </button>
            </div>

            <Input
              label="6-Digit Verification Code"
              type="text"
              maxLength={6}
              placeholder="123456"
              icon={<KeyRound className="h-4 w-4" />}
              error={errors.otp?.message}
              autoFocus
              className="tracking-widest text-center text-lg font-mono font-semibold"
              {...register('otp', {
                required: 'Please enter the 6-digit verification code.',
                pattern: { value: /^\d{6}$/, message: 'Must be a 6-digit code.' },
              })}
            />

            <div className="flex items-center justify-between text-xs text-slate-400">
              <span>Didn't receive code?</span>
              {countdown > 0 ? (
                <span className="text-slate-500">Resend in {countdown}s</span>
              ) : (
                <button
                  type="button"
                  onClick={handleSendOtp}
                  disabled={isSendingOtp}
                  className="text-brand-400 hover:text-brand-300 font-medium flex items-center gap-1 disabled:opacity-50"
                >
                  <RefreshCw className={`h-3 w-3 ${isSendingOtp ? 'animate-spin' : ''}`} />
                  Resend Code
                </button>
              )}
            </div>

            <Button type="submit" loading={isSubmitting} className="w-full mt-2">
              Verify & Create Account
            </Button>

            <button
              type="button"
              onClick={() => setStep('details')}
              className="w-full text-center text-xs text-slate-500 hover:text-slate-300 transition-colors"
            >
              ← Back to registration details
            </button>
          </div>
        )}
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


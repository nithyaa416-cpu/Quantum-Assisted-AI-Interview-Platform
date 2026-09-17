import { useEffect, useState } from 'react'
import { useForm, Controller } from 'react-hook-form'
import {
  User, GraduationCap, Phone, Link2, Github,
  Plus, X, Save, BookOpen,
} from 'lucide-react'
import { Card } from '@/components/ui/Card'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { Spinner } from '@/components/ui/Spinner'
import { useProfile, useUpdateProfile } from '@/hooks/useProfile'
import type { ProfileUpdatePayload } from '@/types'

// ── Tag input (skills / target roles) ────────────────────────────────────────
interface TagInputProps {
  value: string[]
  onChange: (v: string[]) => void
  placeholder?: string
}
function TagInput({ value, onChange, placeholder = 'Add…' }: TagInputProps) {
  const [text, setText] = useState('')

  const add = () => {
    const t = text.trim()
    if (t && !value.includes(t)) onChange([...value, t])
    setText('')
  }

  return (
    <div>
      <div className="flex flex-wrap gap-2 mb-2 min-h-[32px]">
        {value.map((tag) => (
          <span
            key={tag}
            className="flex items-center gap-1 px-2.5 py-1 bg-brand-500/10 text-brand-300 text-xs rounded-lg border border-brand-500/20"
          >
            {tag}
            <button type="button" onClick={() => onChange(value.filter((t) => t !== tag))}>
              <X className="h-3 w-3 hover:text-red-400 transition-colors" />
            </button>
          </span>
        ))}
      </div>
      <div className="flex gap-2">
        <input
          className="input-base flex-1 py-2 text-sm"
          placeholder={placeholder}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') { e.preventDefault(); add() }
            if (e.key === ',')     { e.preventDefault(); add() }
          }}
        />
        <button
          type="button"
          onClick={add}
          className="p-2.5 rounded-xl bg-brand-600 hover:bg-brand-700 text-white transition-colors"
        >
          <Plus className="h-4 w-4" />
        </button>
      </div>
      <p className="text-xs text-slate-600 mt-1">Press Enter or comma to add</p>
    </div>
  )
}

// ── Section wrapper ───────────────────────────────────────────────────────────
function Section({ title, icon, children }: { title: string; icon: React.ReactNode; children: React.ReactNode }) {
  return (
    <Card className="p-6">
      <div className="flex items-center gap-2 mb-5">
        <span className="text-brand-400">{icon}</span>
        <h2 className="text-base font-semibold text-slate-100">{title}</h2>
      </div>
      {children}
    </Card>
  )
}

// ── Main page ─────────────────────────────────────────────────────────────────
export default function ProfilePage() {
  const { data: profile, isLoading } = useProfile()
  const { mutate: updateProfile, isPending } = useUpdateProfile()

  const {
    register,
    handleSubmit,
    control,
    reset,
    formState: { errors, isDirty },
  } = useForm<ProfileUpdatePayload>()

  // Populate form when profile loads
  useEffect(() => {
    if (profile) {
      reset({
        college:         profile.college,
        graduation_year: profile.graduation_year ?? undefined,
        phone:           profile.phone,
        bio:             profile.bio,
        skills:          profile.skills,
        target_roles:    profile.target_roles,
        linkedin_url:    profile.linkedin_url,
        github_url:      profile.github_url,
      })
    }
  }, [profile, reset])

  const onSubmit = (data: ProfileUpdatePayload) => updateProfile(data)

  if (isLoading) {
    return (
      <div className="flex justify-center py-20">
        <Spinner size="lg" />
      </div>
    )
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="max-w-4xl mx-auto space-y-6 animate-slide-up">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">My Profile</h1>
          <p className="text-slate-400 text-sm mt-1">
            Keep your profile updated so the AI can tailor your interviews.
          </p>
        </div>
        <Button
          type="submit"
          loading={isPending}
          disabled={!isDirty && !isPending}
          icon={<Save className="h-4 w-4" />}
        >
          Save changes
        </Button>
      </div>

      {/* Personal info */}
      <Section title="Personal Information" icon={<User className="h-5 w-5" />}>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
          {/* Read-only: name & email from user model */}
          <div>
            <label className="label">Full name</label>
            <p className="input-base opacity-50 cursor-not-allowed">{profile?.full_name}</p>
          </div>
          <div>
            <label className="label">Email address</label>
            <p className="input-base opacity-50 cursor-not-allowed">{profile?.email}</p>
          </div>

          <Input
            label="Phone number"
            type="tel"
            placeholder="+91 98765 43210"
            icon={<Phone className="h-4 w-4" />}
            error={errors.phone?.message}
            {...register('phone', {
              pattern: { value: /^[+\d\s()-]{7,20}$/, message: 'Enter a valid phone number.' },
            })}
          />

          <Input
            label="Graduation year"
            type="number"
            placeholder="2025"
            icon={<GraduationCap className="h-4 w-4" />}
            error={errors.graduation_year?.message}
            {...register('graduation_year', {
              valueAsNumber: true,
              min: { value: 1990, message: 'Year must be after 1990.' },
              max: { value: 2100, message: 'Year must be before 2100.' },
            })}
          />

          <div className="sm:col-span-2">
            <Input
              label="College / University"
              type="text"
              placeholder="IIT Bombay"
              icon={<BookOpen className="h-4 w-4" />}
              error={errors.college?.message}
              {...register('college', {
                maxLength: { value: 255, message: 'Too long.' },
              })}
            />
          </div>

          <div className="sm:col-span-2">
            <label className="label">Bio</label>
            <textarea
              rows={3}
              placeholder="Tell us about yourself — your interests, goals, and experience…"
              className="input-base resize-none"
              {...register('bio')}
            />
          </div>
        </div>
      </Section>

      {/* Skills */}
      <Section title="Technical Skills" icon={<BookOpen className="h-5 w-5" />}>
        <p className="text-xs text-slate-500 mb-3">
          These are used by the AI to generate relevant interview questions.
        </p>
        <Controller
          name="skills"
          control={control}
          defaultValue={[]}
          render={({ field }) => (
            <TagInput
              value={field.value ?? []}
              onChange={field.onChange}
              placeholder="e.g. Python, Django, SQL…"
            />
          )}
        />
      </Section>

      {/* Target roles */}
      <Section title="Target Roles" icon={<User className="h-5 w-5" />}>
        <p className="text-xs text-slate-500 mb-3">
          What roles are you targeting for placement? The AI tailors questions accordingly.
        </p>
        <Controller
          name="target_roles"
          control={control}
          defaultValue={[]}
          render={({ field }) => (
            <TagInput
              value={field.value ?? []}
              onChange={field.onChange}
              placeholder="e.g. Software Engineer, Backend Developer…"
            />
          )}
        />
      </Section>

      {/* Social links */}
      <Section title="Links" icon={<Link2 className="h-5 w-5" />}>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
          <Input
            label="LinkedIn URL"
            type="url"
            placeholder="https://linkedin.com/in/yourname"
            icon={<Link2 className="h-4 w-4" />}
            error={errors.linkedin_url?.message}
            {...register('linkedin_url', {
              pattern: { value: /^https?:\/\/.+/, message: 'Enter a valid URL.' },
            })}
          />
          <Input
            label="GitHub URL"
            type="url"
            placeholder="https://github.com/yourname"
            icon={<Github className="h-4 w-4" />}
            error={errors.github_url?.message}
            {...register('github_url', {
              pattern: { value: /^https?:\/\/.+/, message: 'Enter a valid URL.' },
            })}
          />
        </div>
      </Section>

      {/* Last updated */}
      {profile?.updated_at && (
        <p className="text-xs text-slate-600 text-right">
          Last updated: {new Date(profile.updated_at).toLocaleString()}
        </p>
      )}
    </form>
  )
}

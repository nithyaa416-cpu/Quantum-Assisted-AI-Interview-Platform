import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  FileText, Trash2, RefreshCw, Eye,
  ChevronRight, BookOpen, Briefcase, GraduationCap, Award,
} from 'lucide-react'
import toast from 'react-hot-toast'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { EmptyState } from '@/components/ui/EmptyState'
import { Spinner } from '@/components/ui/Spinner'
import { UploadDropzone } from '@/components/resume/UploadDropzone'
import { ParseStatusBadge } from '@/components/resume/ParseStatusBadge'
import { SkillsEditor } from '@/components/resume/SkillsEditor'
import {
  useResumes, useUploadResume, useDeleteResume,
  useReParse, useResumeDetail, useResumeStatus,
} from '@/hooks/useResumes'
import type { ResumeListItem } from '@/types'

// ── Resume card in the list ────────────────────────────────────────────────────
function ResumeCard({
  resume, onView, onDelete, onReParse,
}: {
  resume: ResumeListItem
  onView: () => void
  onDelete: () => void
  onReParse: () => void
}) {
  // Poll status while processing
  useResumeStatus(
    resume.parse_status === 'pending' || resume.parse_status === 'processing'
      ? resume.id : null
  )

  return (
    <div className="card p-4 flex items-center justify-between gap-4">
      <div className="flex items-center gap-3 min-w-0">
        <div className="p-2.5 rounded-xl bg-surface-hover flex-shrink-0">
          <FileText className="h-5 w-5 text-brand-400" />
        </div>
        <div className="min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <p className="text-sm font-medium text-slate-200 truncate max-w-[200px]">
              {resume.original_filename}
            </p>
            {resume.is_active && <Badge color="green">Active</Badge>}
            <Badge color="slate">v{resume.version}</Badge>
          </div>
          <div className="flex items-center gap-3 mt-1">
            <ParseStatusBadge status={resume.parse_status} />
            {resume.is_parsed && (
              <span className="text-xs text-slate-500">
                {resume.skills_count} skills
              </span>
            )}
            <span className="text-xs text-slate-600">
              {new Date(resume.created_at).toLocaleDateString()}
            </span>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-1 flex-shrink-0">
        {resume.parse_status === 'failed' && (
          <button
            onClick={onReParse}
            className="p-2 rounded-lg text-amber-400 hover:bg-amber-400/10 transition-colors"
            title="Re-parse"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
        )}
        {resume.is_parsed && (
          <button
            onClick={onView}
            className="p-2 rounded-lg text-brand-400 hover:bg-brand-400/10 transition-colors"
            title="View details"
          >
            <Eye className="h-4 w-4" />
          </button>
        )}
        <button
          onClick={onDelete}
          className="p-2 rounded-lg text-slate-500 hover:text-red-400 hover:bg-red-400/10 transition-colors"
          title="Delete"
        >
          <Trash2 className="h-4 w-4" />
        </button>
        {resume.is_parsed && (
          <button
            onClick={onView}
            className="p-2 rounded-lg text-slate-400 hover:text-slate-200 transition-colors"
          >
            <ChevronRight className="h-4 w-4" />
          </button>
        )}
      </div>
    </div>
  )
}

// ── Detail panel for a selected resume ────────────────────────────────────────
function ResumeDetailPanel({ id, onClose }: { id: string; onClose: () => void }) {
  const { data: resume, isLoading } = useResumeDetail(id)
  const [activeTab, setActiveTab] = useState<'skills' | 'projects' | 'education' | 'experience'>('skills')

  if (isLoading) return <div className="flex justify-center py-12"><Spinner /></div>
  if (!resume)   return null

  const tabs = [
    { id: 'skills'     as const, label: 'Skills',     icon: Award,         count: resume.skills.length },
    { id: 'projects'   as const, label: 'Projects',   icon: Briefcase,     count: resume.projects.length },
    { id: 'education'  as const, label: 'Education',  icon: GraduationCap, count: resume.education.length },
    { id: 'experience' as const, label: 'Experience', icon: BookOpen,      count: resume.experience.length },
  ]

  return (
    <div className="space-y-5 animate-slide-up">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold text-slate-100">{resume.original_filename}</h2>
          <div className="flex items-center gap-2 mt-1">
            <ParseStatusBadge status={resume.parse_status} />
            {resume.parsed_at && (
              <span className="text-xs text-slate-500">
                Parsed {new Date(resume.parsed_at).toLocaleString()}
              </span>
            )}
          </div>
        </div>
        <button
          onClick={onClose}
          className="text-xs text-slate-500 hover:text-slate-300 transition-colors px-3 py-1.5 rounded-lg border border-surface-border"
        >
          ← Back
        </button>
      </div>

      {/* Summary */}
      {resume.summary && (
        <Card className="p-4">
          <p className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-2">Summary</p>
          <p className="text-sm text-slate-300 leading-relaxed">{resume.summary}</p>
        </Card>
      )}

      {/* Contact info */}
      {resume.contact?.email && (
        <Card className="p-4">
          <p className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-3">Contact Info</p>
          <div className="grid grid-cols-2 gap-2 text-sm">
            {resume.contact.name  && <ContactRow label="Name"     value={resume.contact.name} />}
            {resume.contact.email && <ContactRow label="Email"    value={resume.contact.email} />}
            {resume.contact.phone && <ContactRow label="Phone"    value={resume.contact.phone} />}
            {resume.contact.linkedin && <ContactRow label="LinkedIn" value={resume.contact.linkedin} link />}
            {resume.contact.github   && <ContactRow label="GitHub"   value={resume.contact.github} link />}
          </div>
        </Card>
      )}

      {/* Tabs */}
      <Card className="p-0 overflow-hidden">
        <div className="flex border-b border-surface-border overflow-x-auto">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-3 text-sm font-medium whitespace-nowrap transition-colors border-b-2 ${
                activeTab === tab.id
                  ? 'border-brand-500 text-brand-400'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <tab.icon className="h-4 w-4" />
              {tab.label}
              <span className="text-xs bg-surface-hover px-1.5 py-0.5 rounded-full">
                {tab.count}
              </span>
            </button>
          ))}
        </div>

        <div className="p-5">
          {activeTab === 'skills' && (
            <SkillsEditor skills={resume.skills} onChange={() => {}} readOnly />
          )}

          {activeTab === 'projects' && (
            <div className="space-y-4">
              {resume.projects.length === 0 ? (
                <p className="text-sm text-slate-500">No projects extracted.</p>
              ) : (
                resume.projects.map((p, i) => (
                  <div key={i} className="p-4 rounded-xl bg-surface border border-surface-border">
                    <div className="flex items-start justify-between gap-2">
                      <h4 className="text-sm font-semibold text-slate-200">{p.title}</h4>
                      {p.url && (
                        <a href={p.url} target="_blank" rel="noreferrer"
                          className="text-xs text-brand-400 hover:text-brand-300 flex-shrink-0">
                          Link →
                        </a>
                      )}
                    </div>
                    {p.description && <p className="text-xs text-slate-400 mt-1.5 leading-relaxed">{p.description}</p>}
                    {p.technologies.length > 0 && (
                      <div className="flex flex-wrap gap-1.5 mt-2">
                        {p.technologies.map((t) => (
                          <span key={t} className="px-2 py-0.5 rounded-md bg-brand-500/10 text-brand-300 text-xs border border-brand-500/20">
                            {t}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          )}

          {activeTab === 'education' && (
            <div className="space-y-3">
              {resume.education.length === 0 ? (
                <p className="text-sm text-slate-500">No education extracted.</p>
              ) : (
                resume.education.map((e, i) => (
                  <div key={i} className="p-4 rounded-xl bg-surface border border-surface-border">
                    <p className="text-sm font-semibold text-slate-200">{e.degree || 'Degree'}</p>
                    {e.institution && <p className="text-xs text-slate-400 mt-0.5">{e.institution}</p>}
                    <div className="flex items-center gap-3 mt-1.5 text-xs text-slate-500">
                      {(e.start_year || e.end_year) && (
                        <span>{e.start_year}{e.start_year && e.end_year ? ' – ' : ''}{e.end_year}</span>
                      )}
                      {e.gpa && <span className="text-emerald-400">GPA: {e.gpa}</span>}
                    </div>
                  </div>
                ))
              )}
            </div>
          )}

          {activeTab === 'experience' && (
            <div className="space-y-3">
              {resume.experience.length === 0 ? (
                <p className="text-sm text-slate-500">No experience extracted.</p>
              ) : (
                resume.experience.map((e, i) => (
                  <div key={i} className="p-4 rounded-xl bg-surface border border-surface-border">
                    <p className="text-sm font-semibold text-slate-200">{e.role || 'Role'}</p>
                    {e.company && <p className="text-xs text-slate-400">{e.company}</p>}
                    {e.date_range && <p className="text-xs text-slate-500 mt-0.5">{e.date_range}</p>}
                    {e.description.length > 0 && (
                      <ul className="mt-2 space-y-1">
                        {e.description.slice(0, 3).map((d, j) => (
                          <li key={j} className="text-xs text-slate-400 flex gap-1.5">
                            <span className="text-brand-500 mt-0.5">•</span>
                            {d}
                          </li>
                        ))}
                      </ul>
                    )}
                    {e.technologies.length > 0 && (
                      <div className="flex flex-wrap gap-1.5 mt-2">
                        {e.technologies.slice(0, 6).map((t) => (
                          <span key={t} className="px-2 py-0.5 rounded-md bg-surface-hover text-slate-400 text-xs">
                            {t}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      </Card>
    </div>
  )
}

function ContactRow({ label, value, link }: { label: string; value: string; link?: boolean }) {
  return (
    <div>
      <p className="text-xs text-slate-500">{label}</p>
      {link ? (
        <a href={value} target="_blank" rel="noreferrer"
          className="text-xs text-brand-400 hover:text-brand-300 break-all">
          {value}
        </a>
      ) : (
        <p className="text-xs text-slate-300 break-all">{value}</p>
      )}
    </div>
  )
}

// ── Main page ─────────────────────────────────────────────────────────────────
export default function ResumesPage() {
  const { data: resumes = [], isLoading } = useResumes()
  const { mutate: upload, isPending: uploading } = useUploadResume()
  const { mutate: deleteResume } = useDeleteResume()
  const { mutate: reParse } = useReParse()
  const [selectedId, setSelectedId] = useState<string | null>(null)

  const handleUpload = (file: File) => upload(file)

  const handleDelete = (id: string) => {
    if (!confirm('Delete this resume?')) return
    if (selectedId === id) setSelectedId(null)
    deleteResume(id)
  }

  if (selectedId) {
    return (
      <div className="max-w-4xl mx-auto">
        <ResumeDetailPanel id={selectedId} onClose={() => setSelectedId(null)} />
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-slide-up">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-100">Resumes</h1>
        <p className="text-slate-400 text-sm mt-1">
          Upload your resume to automatically extract skills, projects, education, and experience.
        </p>
      </div>

      {/* Upload card */}
      <Card className="p-6">
        <h2 className="text-base font-semibold text-slate-100 mb-4">Upload New Resume</h2>
        <UploadDropzone onFile={handleUpload} isUploading={uploading} />
        <div className="mt-3 flex flex-wrap gap-4 text-xs text-slate-500">
          <span>✓ PDF format</span>
          <span>✓ Skills auto-extracted</span>
          <span>✓ Projects detected</span>
          <span>✓ Education & experience parsed</span>
        </div>
      </Card>

      {/* Resume list */}
      <div>
        <h2 className="text-base font-semibold text-slate-100 mb-3">
          Your Resumes
          {resumes.length > 0 && (
            <span className="ml-2 text-sm font-normal text-slate-500">
              ({resumes.length})
            </span>
          )}
        </h2>

        {isLoading ? (
          <div className="flex justify-center py-12"><Spinner /></div>
        ) : resumes.length === 0 ? (
          <Card className="p-6">
            <EmptyState
              title="No resumes uploaded yet"
              description="Upload your resume above to get started."
              icon={<FileText className="h-7 w-7" />}
            />
          </Card>
        ) : (
          <div className="space-y-3">
            {resumes.map((r) => (
              <ResumeCard
                key={r.id}
                resume={r}
                onView={() => setSelectedId(r.id)}
                onDelete={() => handleDelete(r.id)}
                onReParse={() => reParse(r.id)}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

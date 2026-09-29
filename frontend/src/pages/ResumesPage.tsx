import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  FileText, Trash2, RefreshCw, Eye,
  ChevronRight, BookOpen, Briefcase, GraduationCap, Award,
  ExternalLink, X,
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

// ── Resume Reader Modal ────────────────────────────────────────────────────────
function ResumeReaderModal({
  resumeId,
  onClose,
  onOpenDetails,
}: {
  resumeId: string | null
  onClose: () => void
  onOpenDetails?: () => void
}) {
  const { data: resume, isLoading } = useResumeDetail(resumeId)
  const [viewMode, setViewMode] = useState<'document' | 'text'>('document')

  if (!resumeId) return null

  const isPdf = resume?.original_filename?.toLowerCase().endsWith('.pdf') ?? false
  const fileUrl = resume?.file_url

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-5 bg-black/80 backdrop-blur-sm animate-fade-in">
      <div className="bg-surface-card border border-surface-border rounded-2xl w-full max-w-5xl max-h-[92vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-surface-border bg-surface/60">
          <div className="flex items-center gap-3 min-w-0">
            <div className="p-2 rounded-xl bg-brand-500/10 text-brand-400 flex-shrink-0">
              <FileText className="h-5 w-5" />
            </div>
            <div className="min-w-0">
              <h3 className="text-base font-semibold text-slate-100 truncate" title={resume?.original_filename}>
                {resume?.original_filename || 'Reading Resume'}
              </h3>
              <div className="flex items-center gap-2 mt-0.5">
                {resume?.is_active && <Badge color="green">Active</Badge>}
                <Badge color="slate">v{resume?.version || 1}</Badge>
                {resume?.parse_status && <ParseStatusBadge status={resume.parse_status} />}
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* View Mode Toggle */}
            <div className="flex rounded-lg bg-surface border border-slate-700/60 p-0.5 text-xs">
              <button
                type="button"
                onClick={() => setViewMode('document')}
                className={`px-3 py-1.5 rounded-md font-medium transition-colors ${
                  viewMode === 'document' ? 'bg-brand-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Document
              </button>
              <button
                type="button"
                onClick={() => setViewMode('text')}
                className={`px-3 py-1.5 rounded-md font-medium transition-colors ${
                  viewMode === 'text' ? 'bg-brand-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Extracted Text
              </button>
            </div>

            {fileUrl && (
              <a
                href={fileUrl}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-700 text-xs font-medium text-slate-300 hover:text-white hover:bg-surface-hover transition-colors"
                title="Open original file in new browser tab"
              >
                <ExternalLink className="h-3.5 w-3.5" />
                <span className="hidden sm:inline">Open Tab</span>
              </a>
            )}

            {onOpenDetails && (
              <button
                type="button"
                onClick={() => {
                  onClose()
                  onOpenDetails()
                }}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-brand-500/30 text-xs font-medium text-brand-300 hover:bg-brand-500/10 transition-colors"
                title="View full parsed sections"
              >
                <span className="hidden sm:inline">Extracted Sections</span> →
              </button>
            )}

            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-surface-hover transition-colors ml-1"
              title="Close"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 bg-slate-950/60">
          {isLoading ? (
            <div className="flex flex-col items-center justify-center py-24 text-slate-400 gap-3">
              <Spinner size="lg" />
              <p className="text-sm">Loading resume…</p>
            </div>
          ) : viewMode === 'document' ? (
            isPdf && fileUrl ? (
              <div className="w-full h-[70vh] rounded-xl overflow-hidden border border-slate-800 bg-slate-900 shadow-inner flex flex-col">
                <iframe
                  src={`${fileUrl}#toolbar=1&navpanes=0`}
                  title={resume?.original_filename}
                  className="w-full h-full border-0 rounded-xl"
                />
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-16 px-4 text-center space-y-4">
                <div className="h-16 w-16 rounded-2xl bg-brand-500/10 border border-brand-500/20 flex items-center justify-center text-brand-400">
                  <FileText className="h-8 w-8" />
                </div>
                <div>
                  <h4 className="text-base font-semibold text-slate-200">
                    {resume?.original_filename}
                  </h4>
                  <p className="text-xs text-slate-400 mt-1 max-w-md">
                    This file is in Word (.docx/.doc) or text format. You can read the extracted text below or open/download the original file.
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <button
                    type="button"
                    onClick={() => setViewMode('text')}
                    className="px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-medium transition-colors"
                  >
                    Read Extracted Text
                  </button>
                  {fileUrl && (
                    <a
                      href={fileUrl}
                      target="_blank"
                      rel="noreferrer"
                      className="px-4 py-2 rounded-xl bg-surface border border-slate-700 hover:bg-surface-hover text-slate-200 text-xs font-medium transition-colors"
                    >
                      Download Original
                    </a>
                  )}
                </div>
              </div>
            )
          ) : (
            /* Text reader view */
            <div className="space-y-4 max-w-4xl mx-auto">
              {resume?.summary && (
                <div className="p-4 rounded-xl bg-surface/70 border border-surface-border">
                  <span className="text-xs font-medium text-brand-400 uppercase tracking-wider block mb-1.5">Executive Summary</span>
                  <p className="text-sm text-slate-300 leading-relaxed">{resume.summary}</p>
                </div>
              )}

              <div className="p-5 rounded-xl bg-surface/40 border border-surface-border font-mono text-xs sm:text-sm text-slate-300 whitespace-pre-wrap leading-relaxed select-text overflow-x-auto shadow-inner">
                {resume?.raw_text ? (
                  resume.raw_text
                ) : (
                  <div className="py-12 text-center text-slate-500 font-sans">
                    <p>No extracted text available yet.</p>
                    <p className="text-xs text-slate-600 mt-1">Full text is extracted automatically during interview setup.</p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// ── Resume card in the list ────────────────────────────────────────────────────
function ResumeCard({
  resume, onRead, onViewDetails, onDelete, onReParse,
}: {
  resume: ResumeListItem
  onRead: () => void
  onViewDetails: () => void
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
        <div className="p-2.5 rounded-xl bg-surface-hover flex-shrink-0 cursor-pointer" onClick={onRead}>
          <FileText className="h-5 w-5 text-brand-400" />
        </div>
        <div className="min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <button
              type="button"
              onClick={onRead}
              className="text-sm font-medium text-slate-200 hover:text-brand-300 truncate max-w-[220px] text-left transition-colors cursor-pointer"
              title={`Read ${resume.original_filename}`}
            >
              {resume.original_filename}
            </button>
            {resume.is_active && <Badge color="green">Active</Badge>}
            <Badge color="slate">v{resume.version}</Badge>

            {/* View option for reading resume beside resume name */}
            <button
              type="button"
              onClick={onRead}
              className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-lg text-xs font-medium bg-brand-500/15 hover:bg-brand-500/25 text-brand-300 border border-brand-500/30 transition-all cursor-pointer shadow-sm hover:scale-[1.02] active:scale-[0.98]"
              title="Read resume document"
            >
              <Eye className="h-3 w-3" />
              View
            </button>
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
        <button
          onClick={onRead}
          className="p-2 rounded-lg text-brand-400 hover:bg-brand-400/10 transition-colors"
          title="Read resume"
        >
          <Eye className="h-4 w-4" />
        </button>
        <button
          onClick={onDelete}
          className="p-2 rounded-lg text-slate-500 hover:text-red-400 hover:bg-red-400/10 transition-colors"
          title="Delete"
        >
          <Trash2 className="h-4 w-4" />
        </button>
        <button
          onClick={onViewDetails}
          className="p-2 rounded-lg text-slate-400 hover:text-slate-200 transition-colors"
          title="Extracted breakdown"
        >
          <ChevronRight className="h-4 w-4" />
        </button>
      </div>
    </div>
  )
}

// ── Detail panel for a selected resume ────────────────────────────────────────
function ResumeDetailPanel({
  id, onClose, onReadDocument,
}: {
  id: string
  onClose: () => void
  onReadDocument: (id: string) => void
}) {
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
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => onReadDocument(resume.id)}
            className="inline-flex items-center gap-1.5 text-xs text-brand-300 hover:text-white bg-brand-500/15 hover:bg-brand-500/25 px-3 py-1.5 rounded-lg border border-brand-500/30 transition-colors shadow-sm"
          >
            <Eye className="h-3.5 w-3.5" />
            Read Document
          </button>
          <button
            onClick={onClose}
            className="text-xs text-slate-500 hover:text-slate-300 transition-colors px-3 py-1.5 rounded-lg border border-surface-border"
          >
            ← Back
          </button>
        </div>
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
  const [readingId, setReadingId]   = useState<string | null>(null)

  const handleUpload = (file: File) => upload(file)

  const handleDelete = (id: string) => {
    if (!confirm('Delete this resume?')) return
    if (selectedId === id) setSelectedId(null)
    if (readingId === id) setReadingId(null)
    deleteResume(id)
  }

  return (
    <>
      {/* Resume Reader Modal */}
      <ResumeReaderModal
        resumeId={readingId}
        onClose={() => setReadingId(null)}
        onOpenDetails={() => {
          const id = readingId
          setReadingId(null)
          setSelectedId(id)
        }}
      />

      {selectedId ? (
        <div className="max-w-4xl mx-auto">
          <ResumeDetailPanel
            id={selectedId}
            onClose={() => setSelectedId(null)}
            onReadDocument={(id) => setReadingId(id)}
          />
        </div>
      ) : (
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
              <span>✓ PDF, DOCX, DOC format</span>
              <span>✓ Instant Document Reader</span>
              <span>✓ Projects & Skills detected</span>
              <span>✓ Safe & isolated to your account</span>
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
                    onRead={() => setReadingId(r.id)}
                    onViewDetails={() => setSelectedId(r.id)}
                    onDelete={() => handleDelete(r.id)}
                    onReParse={() => reParse(r.id)}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </>
  )
}

import { useCallback, useState } from 'react'
import { Upload, FileText, AlertCircle } from 'lucide-react'
import { clsx } from 'clsx'

interface UploadDropzoneProps {
  onFile: (file: File) => void
  isUploading: boolean
}

export function UploadDropzone({ onFile, isUploading }: UploadDropzoneProps) {
  const [isDragging, setIsDragging] = useState(false)
  const [error, setError]           = useState<string | null>(null)

  const validate = (file: File): string | null => {
    const validExtensions = ['.pdf', '.docx', '.doc']
    const name = file.name.toLowerCase()
    if (!validExtensions.some(ext => name.endsWith(ext)))
      return 'Supported formats: PDF, DOCX, DOC.'
    if (file.size > 10 * 1024 * 1024)
      return 'File size must be under 10 MB.'
    return null
  }

  const handle = useCallback((file: File) => {
    const err = validate(file)
    if (err) { setError(err); return }
    setError(null)
    onFile(file)
  }, [onFile])

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) handle(file)
  }

  const onInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) handle(file)
    e.target.value = ''
  }

  return (
    <div className="space-y-3">
      <label
        className={clsx(
          'flex flex-col items-center justify-center w-full h-48 rounded-2xl border-2 border-dashed cursor-pointer transition-all duration-200',
          isDragging
            ? 'border-brand-400 bg-brand-500/10'
            : 'border-surface-border bg-surface hover:border-brand-500/50 hover:bg-surface-hover',
          isUploading && 'opacity-50 cursor-not-allowed pointer-events-none',
        )}
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true) }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={onDrop}
      >
        <input
          type="file"
          accept=".pdf,.docx,.doc,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/msword"
          className="hidden"
          onChange={onInputChange}
          disabled={isUploading}
        />
        <div className="flex flex-col items-center gap-3 text-center px-4">
          {isUploading ? (
            <>
              <div className="h-10 w-10 rounded-2xl bg-brand-500/10 flex items-center justify-center">
                <FileText className="h-5 w-5 text-brand-400 animate-pulse" />
              </div>
              <p className="text-sm text-brand-400 font-medium">Uploading…</p>
            </>
          ) : (
            <>
              <div className={clsx(
                'h-12 w-12 rounded-2xl flex items-center justify-center transition-colors',
                isDragging ? 'bg-brand-500/20' : 'bg-surface-hover',
              )}>
                <Upload className={clsx('h-6 w-6', isDragging ? 'text-brand-400' : 'text-slate-400')} />
              </div>
              <div>
                <p className="text-sm font-medium text-slate-200">
                  {isDragging ? 'Drop your resume here' : 'Drag & drop your resume'}
                </p>
                <p className="text-xs text-slate-500 mt-0.5">
                  or <span className="text-brand-400">click to browse</span>
                </p>
                <p className="text-xs text-slate-600 mt-1.5">PDF, DOCX, DOC · Max 10 MB</p>
              </div>
            </>
          )}
        </div>
      </label>

      {error && (
        <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-xs">
          <AlertCircle className="h-3.5 w-3.5 flex-shrink-0" />
          {error}
        </div>
      )}
    </div>
  )
}

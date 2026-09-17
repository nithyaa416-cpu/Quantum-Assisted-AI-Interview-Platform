/**
 * Voice-first answer area for the AI Interview module.
 *
 * Primary flow:
 *   1. Student clicks the big mic button → recording starts
 *   2. Live transcript appears as speech is detected
 *   3. Student clicks Stop → transcript is editable for corrections
 *   4. Student clicks Submit → answer is sent
 *
 * Fallback: if browser doesn't support Speech Recognition, a plain
 * textarea is shown automatically.
 */
import { useState, useRef, useEffect, useCallback } from 'react'
import { Mic, MicOff, Send, RotateCcw, Edit3, CheckCircle2, AlertCircle } from 'lucide-react'
import { clsx } from 'clsx'
import { Button } from '@/components/ui/Button'

interface AnswerAreaProps {
  onSubmit: (answer: string, durationSeconds: number) => void
  isSubmitting: boolean
  questionId: string       // resets state when question changes
}

type RecordState = 'idle' | 'recording' | 'done'

const MIN_WORDS = 5

const hasSpeechAPI = (): boolean =>
  typeof window !== 'undefined' &&
  ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)

// ── Audio waveform visualiser ──────────────────────────────────────────────
function WaveAnimation() {
  return (
    <div className="flex items-center justify-center gap-1 h-8">
      {[0.3, 0.7, 1.0, 0.8, 0.5, 0.9, 0.6, 0.4, 0.8, 0.3].map((h, i) => (
        <div
          key={i}
          className="w-1 rounded-full bg-red-400"
          style={{
            height: `${h * 28}px`,
            animation: `wave 0.8s ease-in-out ${i * 0.08}s infinite alternate`,
          }}
        />
      ))}
      <style>{`
        @keyframes wave {
          from { transform: scaleY(0.4); opacity: 0.6; }
          to   { transform: scaleY(1);   opacity: 1;   }
        }
      `}</style>
    </div>
  )
}

// ── Main component ─────────────────────────────────────────────────────────
export function AnswerArea({ onSubmit, isSubmitting, questionId }: AnswerAreaProps) {
  const [recordState, setRecordState] = useState<RecordState>('idle')
  const [transcript,  setTranscript]  = useState('')
  const [interim,     setInterim]     = useState('')   // live in-progress words
  const [isEditing,   setIsEditing]   = useState(false)
  const [startTime,   setStartTime]   = useState<number>(0)
  const [errorMsg,    setErrorMsg]    = useState<string | null>(null)
  const [supported,   setSupported]   = useState<boolean | null>(null)

  const recognitionRef  = useRef<any>(null)
  const textareaRef     = useRef<HTMLTextAreaElement>(null)

  // Detect browser support on mount
  useEffect(() => {
    setSupported(hasSpeechAPI())
  }, [])

  // Reset everything when question changes
  useEffect(() => {
    stopRecording()
    setTranscript('')
    setInterim('')
    setIsEditing(false)
    setRecordState('idle')
    setErrorMsg(null)
  }, [questionId])

  const stopRecording = useCallback(() => {
    if (recognitionRef.current) {
      try { recognitionRef.current.stop() } catch {}
      recognitionRef.current = null
    }
  }, [])

  const startRecording = () => {
    setErrorMsg(null)
    const SR: any = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
    const rec = new SR()

    rec.continuous     = true
    rec.interimResults = true
    rec.lang           = 'en-US'
    rec.maxAlternatives = 1

    rec.onstart = () => {
      setRecordState('recording')
      setStartTime(Date.now())
    }

    rec.onresult = (event: any) => {
      let finalText  = ''
      let interimText = ''
      for (let i = 0; i < event.results.length; i++) {
        const res = event.results[i]
        if (res.isFinal) {
          finalText += res[0].transcript + ' '
        } else {
          interimText += res[0].transcript
        }
      }
      if (finalText) setTranscript(prev => (prev + finalText).trim())
      setInterim(interimText)
    }

    rec.onerror = (event: any) => {
      if (event.error === 'no-speech') {
        setErrorMsg('No speech detected. Please speak louder or check your microphone.')
      } else if (event.error === 'not-allowed' || event.error === 'permission-denied') {
        setErrorMsg('Microphone access denied. See fix instructions below.')
        setSupported(false)   // drop to text fallback
      } else if (event.error === 'audio-capture') {
        setErrorMsg('audio-capture')   // handled specially in the UI
        setRecordState('idle')
      } else {
        setErrorMsg(`Microphone unavailable (${event.error}). Please type your answer.`)
        setSupported(false)
      }
      setRecordState('idle')
    }

    rec.onend = () => {
      setInterim('')
      setRecordState(prev => prev === 'recording' ? 'done' : prev)
    }

    recognitionRef.current = rec
    rec.start()
  }

  const handleToggleRecording = () => {
    if (recordState === 'recording') {
      stopRecording()
      setRecordState('done')
    } else {
      setTranscript('')
      setInterim('')
      startRecording()
    }
  }

  const handleSubmit = () => {
    const full = (transcript + ' ' + interim).trim()
    if (!full || full.split(/\s+/).filter(Boolean).length < MIN_WORDS) return
    const duration = startTime ? Math.round((Date.now() - startTime) / 1000) : 0
    onSubmit(full, duration)
  }

  const handleReset = () => {
    stopRecording()
    setTranscript('')
    setInterim('')
    setRecordState('idle')
    setIsEditing(false)
    setErrorMsg(null)
  }

  const fullText  = (transcript + (interim ? ' ' + interim : '')).trim()
  const wordCount = fullText.split(/\s+/).filter(Boolean).length
  const canSubmit = wordCount >= MIN_WORDS && !isSubmitting && recordState !== 'recording'

  // ── Fallback: plain textarea if no Speech API ─────────────────────────────
  if (supported === false) {
    return <TextFallback onSubmit={onSubmit} isSubmitting={isSubmitting} questionId={questionId} />
  }

  return (
    <div className="card overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-5 pt-5 pb-3">
        <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
          <Mic className="h-4 w-4 text-brand-400" />
          Speak Your Answer
        </h3>
        <div className="flex items-center gap-2">
          {wordCount > 0 && (
            <span className={clsx(
              'text-xs tabular-nums',
              wordCount < MIN_WORDS ? 'text-amber-400' : 'text-emerald-400',
            )}>
              {wordCount} word{wordCount !== 1 ? 's' : ''}
              {wordCount < MIN_WORDS ? ` (need ${MIN_WORDS})` : ' ✓'}
            </span>
          )}
          {recordState !== 'idle' && (
            <button
              onClick={handleReset}
              className="flex items-center gap-1 text-xs text-slate-500 hover:text-slate-300 transition-colors"
            >
              <RotateCcw className="h-3 w-3" /> Reset
            </button>
          )}
        </div>
      </div>

      {/* Main recording area */}
      <div className="px-5 pb-5 space-y-4">

        {/* Error banner */}
        {errorMsg && errorMsg !== 'audio-capture' && (
          <div className="flex items-start gap-2 p-3 rounded-xl bg-red-500/10 border border-red-500/25 text-red-400 text-xs">
            <AlertCircle className="h-4 w-4 flex-shrink-0 mt-0.5" />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* audio-capture: dedicated fix guide */}
        {errorMsg === 'audio-capture' && (
          <div className="rounded-xl border border-amber-500/30 bg-amber-500/5 p-4 space-y-3 text-sm">
            <div className="flex items-start gap-2">
              <AlertCircle className="h-4 w-4 text-amber-400 flex-shrink-0 mt-0.5" />
              <p className="text-amber-300 font-medium">Microphone not detected</p>
            </div>
            <p className="text-slate-400 text-xs leading-relaxed">
              Your browser cannot access the microphone. This is usually a permission issue. Follow the steps for your browser:
            </p>
            <div className="space-y-2 text-xs text-slate-400">
              <div className="flex items-start gap-2">
                <span className="text-brand-400 font-bold flex-shrink-0">Chrome:</span>
                <span>Click the 🔒 lock icon in the address bar → Site settings → Microphone → Allow</span>
              </div>
              <div className="flex items-start gap-2">
                <span className="text-brand-400 font-bold flex-shrink-0">Edge:</span>
                <span>Click the 🔒 lock icon → Permissions for this site → Microphone → Allow</span>
              </div>
              <div className="flex items-start gap-2">
                <span className="text-brand-400 font-bold flex-shrink-0">Windows:</span>
                <span>Settings → Privacy → Microphone → Allow apps to access microphone → ON</span>
              </div>
            </div>
            <div className="flex gap-2 pt-1">
              <button
                onClick={() => { setErrorMsg(null); setRecordState('idle') }}
                className="flex-1 py-2 rounded-lg bg-brand-600 hover:bg-brand-700 text-white text-xs font-medium transition-colors"
              >
                Try Again
              </button>
              <button
                onClick={() => { setErrorMsg(null); setSupported(false) }}
                className="flex-1 py-2 rounded-lg bg-surface-hover text-slate-300 text-xs font-medium hover:text-slate-100 transition-colors border border-surface-border"
              >
                Type Instead
              </button>
            </div>
          </div>
        )}

        {/* Big mic button — the main CTA */}
        <div className="flex flex-col items-center gap-4 py-4">
          <button
            onClick={handleToggleRecording}
            disabled={isSubmitting || recordState === 'done'}
            className={clsx(
              'relative h-24 w-24 rounded-full flex items-center justify-center transition-all duration-300 focus:outline-none',
              'focus-visible:ring-2 focus-visible:ring-brand-400 focus-visible:ring-offset-2 focus-visible:ring-offset-surface',
              recordState === 'recording'
                ? 'bg-red-500 hover:bg-red-600 shadow-[0_0_0_8px_rgba(239,68,68,0.15),0_0_0_16px_rgba(239,68,68,0.07)]'
                : recordState === 'done'
                ? 'bg-emerald-600 cursor-default'
                : 'bg-brand-600 hover:bg-brand-700 hover:shadow-[0_0_0_8px_rgba(99,102,241,0.15)]',
              isSubmitting && 'opacity-50 cursor-not-allowed',
            )}
          >
            {recordState === 'recording' ? (
              <MicOff className="h-9 w-9 text-white" />
            ) : recordState === 'done' ? (
              <CheckCircle2 className="h-9 w-9 text-white" />
            ) : (
              <Mic className="h-9 w-9 text-white" />
            )}
          </button>

          {/* State label */}
          <div className="text-center space-y-1">
            {recordState === 'idle' && (
              <>
                <p className="text-sm font-medium text-slate-200">Tap to Start Speaking</p>
                <p className="text-xs text-slate-500">Your answer will be transcribed in real time</p>
              </>
            )}
            {recordState === 'recording' && (
              <>
                <p className="text-sm font-semibold text-red-400 flex items-center gap-1.5 justify-center">
                  <span className="h-2 w-2 rounded-full bg-red-400 animate-pulse" />
                  Recording… Tap to Stop
                </p>
                <WaveAnimation />
              </>
            )}
            {recordState === 'done' && (
              <p className="text-sm font-medium text-emerald-400">
                Recording complete — review and submit below
              </p>
            )}
          </div>
        </div>

        {/* Live transcript display */}
        {(transcript || interim) && (
          <div className={clsx(
            'rounded-xl border p-4 min-h-[80px] transition-all duration-200',
            isEditing
              ? 'bg-surface border-brand-500/50'
              : 'bg-surface border-surface-border',
          )}>
            {isEditing ? (
              <textarea
                ref={textareaRef}
                value={transcript}
                onChange={e => setTranscript(e.target.value)}
                rows={4}
                autoFocus
                className="w-full bg-transparent text-slate-100 text-sm leading-relaxed resize-none focus:outline-none"
                placeholder="Edit your transcript…"
              />
            ) : (
              <p className="text-sm text-slate-200 leading-relaxed">
                {transcript}
                {interim && (
                  <span className="text-slate-500 italic"> {interim}</span>
                )}
                {recordState === 'recording' && (
                  <span className="inline-block h-4 w-0.5 bg-red-400 animate-pulse ml-0.5 align-middle" />
                )}
              </p>
            )}
          </div>
        )}

        {/* Edit / action row */}
        {recordState === 'done' && transcript && (
          <div className="flex items-center justify-between gap-3">
            <button
              onClick={() => {
                setIsEditing(v => !v)
                if (!isEditing) setTimeout(() => textareaRef.current?.focus(), 50)
              }}
              className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 transition-colors"
            >
              <Edit3 className="h-3.5 w-3.5" />
              {isEditing ? 'Done editing' : 'Edit transcript'}
            </button>

            <Button
              onClick={handleSubmit}
              disabled={!canSubmit}
              loading={isSubmitting}
              icon={<Send className="h-4 w-4" />}
            >
              Submit Answer
            </Button>
          </div>
        )}

        {/* Hint: switch to typing */}
        {recordState === 'idle' && !errorMsg && (
          <p className="text-center text-xs text-slate-600">
            Prefer typing?{' '}
            <button
              onClick={() => setSupported(false)}
              className="text-brand-500 hover:text-brand-400 underline transition-colors"
            >
              Switch to text input
            </button>
          </p>
        )}
      </div>
    </div>
  )
}

// ── Text fallback ──────────────────────────────────────────────────────────
function TextFallback({
  onSubmit, isSubmitting, questionId,
}: {
  onSubmit: (a: string, d: number) => void
  isSubmitting: boolean
  questionId: string
}) {
  const [text, setText]       = useState('')
  const [start]               = useState(Date.now())
  const [showVoice, setVoice] = useState(false)
  const ref = useRef<HTMLTextAreaElement>(null)

  useEffect(() => { setText(''); ref.current?.focus() }, [questionId])
  useEffect(() => {
    if (ref.current) {
      ref.current.style.height = 'auto'
      ref.current.style.height = `${Math.min(ref.current.scrollHeight, 240)}px`
    }
  }, [text])

  if (showVoice) return (
    <AnswerArea onSubmit={onSubmit} isSubmitting={isSubmitting} questionId={questionId} />
  )

  const words     = text.trim().split(/\s+/).filter(Boolean).length
  const canSubmit = words >= MIN_WORDS && !isSubmitting

  return (
    <div className="card p-5 space-y-3">
      <div className="flex items-center justify-between">
        <label className="text-sm font-semibold text-slate-200">Type Your Answer</label>
        <span className={clsx('text-xs', words < MIN_WORDS ? 'text-amber-400' : 'text-emerald-400')}>
          {words} word{words !== 1 ? 's' : ''}{words < MIN_WORDS ? ` (need ${MIN_WORDS})` : ' ✓'}
        </span>
      </div>

      <textarea
        ref={ref}
        value={text}
        onChange={e => setText(e.target.value)}
        onKeyDown={e => { if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) { e.preventDefault(); if (canSubmit) onSubmit(text.trim(), Math.round((Date.now() - start) / 1000)) }}}
        placeholder="Type your answer here… Ctrl+Enter to submit."
        disabled={isSubmitting}
        rows={4}
        className="w-full bg-surface border border-surface-border rounded-xl px-4 py-3 text-slate-100 placeholder-slate-600 text-sm leading-relaxed resize-none focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition-colors disabled:opacity-50"
      />

      <div className="flex items-center justify-between">
        <button
          onClick={() => setVoice(true)}
          className="flex items-center gap-1.5 text-xs text-brand-500 hover:text-brand-400 transition-colors"
        >
          <Mic className="h-3.5 w-3.5" /> Switch to voice
        </button>
        <Button onClick={() => { if (canSubmit) onSubmit(text.trim(), Math.round((Date.now() - start) / 1000)) }} disabled={!canSubmit} loading={isSubmitting} icon={<Send className="h-4 w-4" />} size="sm">
          Submit
        </Button>
      </div>
    </div>
  )
}

import { useState, useEffect, useRef } from 'react'
import {
  Camera, Mic, Maximize2, FileText, CheckCircle2,
  AlertTriangle, ArrowRight, ShieldCheck, RefreshCw
} from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { useResumes } from '@/hooks/useResumes'
import { registerMediaStream, unregisterMediaStream } from '@/utils/mediaStreamManager'
import type { StartInterviewPayload } from '@/types'

interface InterviewPrerequisitesProps {
  onReadyToEnter: (payload: StartInterviewPayload) => void
  isLoading?: boolean
  selectedRole?: string
  initialPayload: StartInterviewPayload
}

export function InterviewPrerequisites({
  onReadyToEnter,
  isLoading = false,
  selectedRole,
  initialPayload,
}: InterviewPrerequisitesProps) {
  const [cameraPassed, setCameraPassed] = useState<boolean | null>(null)
  const [micPassed, setMicPassed] = useState<boolean | null>(null)
  const [audioLevel, setAudioLevel] = useState<number>(0)
  const [fullscreenAgreed, setFullscreenAgreed] = useState(false)
  const [integrityAgreed, setIntegrityAgreed] = useState(false)

  const videoRef = useRef<HTMLVideoElement>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const audioContextRef = useRef<AudioContext | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const animFrameRef = useRef<number | null>(null)

  const { data: resumes } = useResumes()
  const activeResume = resumes?.find((r) => r.is_active) || resumes?.[0]

  useEffect(() => {
    let localStream: MediaStream | null = null

    const checkDevices = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { width: { ideal: 1280 }, height: { ideal: 720 } },
          audio: true,
        })
        localStream = stream
        streamRef.current = stream
        registerMediaStream(stream)

        setCameraPassed(true)
        setMicPassed(true)

        if (videoRef.current) {
          videoRef.current.srcObject = stream
        }

        // Web Audio analyser for live mic test
        try {
          const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext
          if (AudioContextClass) {
            const ctx = new AudioContextClass()
            audioContextRef.current = ctx
            const source = ctx.createMediaStreamSource(stream)
            const analyser = ctx.createAnalyser()
            analyser.fftSize = 64
            source.connect(analyser)
            analyserRef.current = analyser

            const pcm = new Uint8Array(analyser.frequencyBinCount)
            const tick = () => {
              if (analyserRef.current) {
                analyserRef.current.getByteFrequencyData(pcm)
                let sum = 0
                for (let i = 0; i < pcm.length; i++) sum += pcm[i]
                const avg = sum / pcm.length
                setAudioLevel(Math.min(100, Math.round((avg / 128) * 100)))
              }
              animFrameRef.current = requestAnimationFrame(tick)
            }
            tick()
          }
        } catch (e) {
          console.warn('AudioContext failed:', e)
        }
      } catch (err) {
        console.warn('Media check failed:', err)
        setCameraPassed(false)
        setMicPassed(false)
      }
    }

    checkDevices()

    return () => {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current)
      if (audioContextRef.current) {
        try { audioContextRef.current.close() } catch {}
      }
      if (localStream) {
        try {
          unregisterMediaStream(localStream)
          localStream.getTracks().forEach((t) => {
            t.stop()
            t.enabled = false
          })
        } catch {}
      }
    }
  }, [])

  const allPassed =
    cameraPassed === true &&
    micPassed === true &&
    fullscreenAgreed &&
    integrityAgreed

  const handleStart = async () => {
    // Stop preliminary device check stream before handing off to the meeting room
    if (streamRef.current) {
      try {
        unregisterMediaStream(streamRef.current)
        streamRef.current.getTracks().forEach((t) => {
          t.stop()
          t.enabled = false
        })
      } catch {}
      streamRef.current = null
    }
    // Enter fullscreen
    try {
      if (!document.fullscreenElement) {
        await document.documentElement.requestFullscreen()
      }
    } catch {}

    onReadyToEnter({
      ...initialPayload,
      resume_id: activeResume?.id || initialPayload.resume_id,
    })
  }

  return (
    <div className="max-w-4xl mx-auto py-6 px-4 animate-fade-in space-y-6">
      {/* Header */}
      <div className="text-center space-y-2">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-500/10 border border-brand-500/20 text-brand-400 text-xs font-semibold uppercase tracking-wider">
          <ShieldCheck className="h-4 w-4" />
          <span>Mandatory Pre-Interview Verification</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-100">
          Candidate Readiness &amp; Hardware Check
        </h1>
        <p className="text-sm text-slate-400 max-w-xl mx-auto">
          This is an official, proctored AI examination. You cannot mute your microphone or turn off your camera during the session. Please verify your equipment below before entering.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-start">
        {/* Left: Live Video & Audio Preview */}
        <div className="space-y-4">
          <div className="relative aspect-video rounded-2xl overflow-hidden bg-slate-900 border border-slate-800 shadow-xl flex items-center justify-center">
            {cameraPassed ? (
              <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                className="w-full h-full object-cover scale-x-[-1]"
              />
            ) : (
              <div className="flex flex-col items-center justify-center p-6 text-center space-y-2">
                <Camera className="h-10 w-10 text-red-400" />
                <p className="text-xs text-red-300 font-medium">Camera access blocked or not detected</p>
                <p className="text-[11px] text-slate-400">Please allow camera permissions in your browser bar.</p>
              </div>
            )}

            {/* Audio bar preview */}
            <div className="absolute bottom-3 inset-x-3 flex items-center justify-between px-3 py-2 rounded-xl bg-black/70 backdrop-blur-md border border-white/10 text-xs">
              <div className="flex items-center gap-2">
                <Mic className="h-4 w-4 text-emerald-400" />
                <span className="text-slate-200">Microphone Input:</span>
              </div>
              <div className="flex items-center gap-1 w-28 bg-slate-800 h-2.5 rounded-full overflow-hidden p-0.5">
                <div
                  className="bg-emerald-400 h-full rounded-full transition-all duration-75"
                  style={{ width: `${Math.max(5, audioLevel)}%` }}
                />
              </div>
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 text-xs text-slate-400 flex items-center justify-between">
            <span>Camera &amp; Mic Hardware Status</span>
            <span className={`font-semibold flex items-center gap-1 ${cameraPassed && micPassed ? 'text-emerald-400' : 'text-red-400'}`}>
              {cameraPassed && micPassed ? (
                <>
                  <CheckCircle2 className="h-3.5 w-3.5" /> Hardware Online
                </>
              ) : (
                <>
                  <AlertTriangle className="h-3.5 w-3.5" /> Permission Required
                </>
              )}
            </span>
          </div>
        </div>

        {/* Right: Prerequisite Checklist & Rules */}
        <div className="space-y-4">
          <div className="rounded-2xl bg-surface-card border border-surface-border p-5 space-y-4 shadow-xl">
            <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider">
              Examination Prerequisites
            </h3>

            {/* Item 1: Camera */}
            <div className="flex items-start gap-3 p-3 rounded-xl bg-surface/60 border border-slate-800/80">
              <div className={`p-2 rounded-lg ${cameraPassed ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'}`}>
                <Camera className="h-4 w-4" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-semibold text-slate-200">Webcam Feed</h4>
                  {cameraPassed ? (
                    <span className="text-[11px] font-bold text-emerald-400">PASSED</span>
                  ) : (
                    <span className="text-[11px] font-bold text-red-400">FAILED</span>
                  )}
                </div>
                <p className="text-[11px] text-slate-400 mt-0.5">
                  Continuous video monitoring is mandatory throughout the interview.
                </p>
              </div>
            </div>

            {/* Item 2: Microphone */}
            <div className="flex items-start gap-3 p-3 rounded-xl bg-surface/60 border border-slate-800/80">
              <div className={`p-2 rounded-lg ${micPassed ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'}`}>
                <Mic className="h-4 w-4" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-semibold text-slate-200">Microphone</h4>
                  {micPassed ? (
                    <span className="text-[11px] font-bold text-emerald-400">PASSED</span>
                  ) : (
                    <span className="text-[11px] font-bold text-red-400">FAILED</span>
                  )}
                </div>
                <p className="text-[11px] text-slate-400 mt-0.5">
                  Microphone will remain permanently active to record and transcribe your answers.
                </p>
              </div>
            </div>

            {/* Item 3: Resume */}
            <div className="flex items-start gap-3 p-3 rounded-xl bg-surface/60 border border-slate-800/80">
              <div className="p-2 rounded-lg bg-brand-500/10 text-brand-400">
                <FileText className="h-4 w-4" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-semibold text-slate-200">Linked Candidate Resume</h4>
                  <span className="text-[11px] font-bold text-brand-400">VERIFIED</span>
                </div>
                <p className="text-[11px] text-slate-400 mt-0.5 truncate">
                  {activeResume ? activeResume.original_filename : 'Default Candidate Profile'}
                </p>
              </div>
            </div>

            {/* Checkbox 1: Fullscreen */}
            <label className="flex items-start gap-2.5 p-3 rounded-xl bg-slate-900 border border-slate-800 cursor-pointer hover:bg-slate-850 transition-colors">
              <input
                type="checkbox"
                checked={fullscreenAgreed}
                onChange={(e) => setFullscreenAgreed(e.target.checked)}
                className="mt-0.5 rounded border-slate-700 text-brand-600 focus:ring-brand-500 h-4 w-4 bg-slate-950"
              />
              <span className="text-xs text-slate-300 leading-snug">
                I understand the examination will run in <strong>Strict Full-Screen Mode</strong>. Tab switching or exiting full-screen triggers a proctoring violation.
              </span>
            </label>

            {/* Checkbox 2: Integrity & No Edit */}
            <label className="flex items-start gap-2.5 p-3 rounded-xl bg-slate-900 border border-slate-800 cursor-pointer hover:bg-slate-850 transition-colors">
              <input
                type="checkbox"
                checked={integrityAgreed}
                onChange={(e) => setIntegrityAgreed(e.target.checked)}
                className="mt-0.5 rounded border-slate-700 text-brand-600 focus:ring-brand-500 h-4 w-4 bg-slate-950"
              />
              <span className="text-xs text-slate-300 leading-snug">
                I understand this is a voice-driven verbal examination. Answers are transcribed as spoken and cannot be manually typed or modified.
              </span>
            </label>
          </div>

          {/* Action button */}
          <Button
            onClick={handleStart}
            disabled={!allPassed || isLoading}
            loading={isLoading}
            className="w-full bg-brand-600 hover:bg-brand-500 text-white font-bold py-3 text-sm rounded-xl shadow-lg shadow-brand-500/20"
            icon={<ArrowRight className="h-4 w-4" />}
          >
            Enter Proctored Interview Room
          </Button>

          {!allPassed && (
            <p className="text-center text-[11px] text-slate-500">
              Complete hardware checks and check both agreements to proceed.
            </p>
          )}
        </div>
      </div>
    </div>
  )
}

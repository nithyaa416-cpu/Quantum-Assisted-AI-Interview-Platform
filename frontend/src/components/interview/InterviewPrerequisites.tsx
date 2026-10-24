import { useState, useEffect, useRef, useCallback } from 'react'
import {
  Camera, Mic, Maximize2, FileText, CheckCircle2,
  AlertTriangle, ArrowRight, ShieldCheck, RefreshCw,
  Eye, Smile, UserCheck, Scan, Sparkles, Check, X,
} from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { useResumes } from '@/hooks/useResumes'
import { registerMediaStream, unregisterMediaStream } from '@/utils/mediaStreamManager'
import { mediaPipeService, type FacialVerificationStatus } from '@/utils/mediaPipeService'
import { unlockBrowserAudio } from '@/utils/audioSpeechManager'
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

  // MediaPipe AI Biometrics state
  const [facialStatus, setFacialStatus] = useState<FacialVerificationStatus | null>(null)
  const [isScanningLandmarks, setIsScanningLandmarks] = useState(true)
  const [hasVerifiedOnce, setHasVerifiedOnce] = useState(false)

  const videoRef = useRef<HTMLVideoElement>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const audioContextRef = useRef<AudioContext | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const animFrameRef = useRef<number | null>(null)

  const { data: resumes } = useResumes()
  const activeResume = resumes?.find((r) => r.is_active) || resumes?.[0]

  // Real-time callback from MediaPipe FaceMesh
  const handleFacialResult = useCallback((status: FacialVerificationStatus) => {
    setFacialStatus(status)
    setIsScanningLandmarks(false)
    if (status.allFeaturesVerified) {
      setHasVerifiedOnce(true)
    }
  }, [])

  useEffect(() => {
    let localStream: MediaStream | null = null

    const checkDevices = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { width: { ideal: 1280 }, height: { ideal: 720 } },
          audio: {
            echoCancellation: true,
            noiseSuppression: true,
            autoGainControl: true,
          },
        })
        localStream = stream
        streamRef.current = stream
        registerMediaStream(stream)

        setCameraPassed(true)
        setMicPassed(true)

        if (videoRef.current) {
          videoRef.current.srcObject = stream
          // Initialize and start MediaPipe FaceMesh tracking
          mediaPipeService.init().then(() => {
            if (videoRef.current) {
              mediaPipeService.startTracking(videoRef.current, handleFacialResult)
            }
          })
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
      mediaPipeService.stopTracking(handleFacialResult)
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
  }, [handleFacialResult])

  // Facial verification rules
  const faceDetected = Boolean(facialStatus && facialStatus.hasSingleFace)
  const eyesVerified = Boolean(facialStatus && facialStatus.eyesVisible && facialStatus.leftEyeOpen && facialStatus.rightEyeOpen)
  const noseVerified = Boolean(facialStatus && facialStatus.noseVisible)
  const mouthVerified = Boolean(facialStatus && facialStatus.mouthVisible)
  const framingVerified = Boolean(facialStatus && facialStatus.isCentered && facialStatus.isGoodDistance)
  const facingCameraVerified = Boolean(facialStatus && facialStatus.headPose.isFacingCamera)

  // Candidate is biometrically verified when features pass (or already confirmed once in this preview)
  const isBiometricVerified = Boolean(
    (faceDetected && eyesVerified && noseVerified && mouthVerified && framingVerified) ||
    hasVerifiedOnce
  )

  const allPassed =
    cameraPassed === true &&
    micPassed === true &&
    isBiometricVerified &&
    fullscreenAgreed &&
    integrityAgreed

  const handleStart = async () => {
    // 1. Immediately unlock browser audio during this user click event
    unlockBrowserAudio()

    // Stop preliminary device check stream before handing off to the meeting room
    mediaPipeService.stopTracking(handleFacialResult)
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
        {/* Left: Live Video & Audio Preview with MediaPipe HUD */}
        <div className="space-y-4">
          <div className="relative aspect-video rounded-2xl overflow-hidden bg-slate-900 border border-slate-800 shadow-xl flex items-center justify-center">
            {cameraPassed ? (
              <>
                <video
                  ref={videoRef}
                  autoPlay
                  playsInline
                  muted
                  className="w-full h-full object-cover scale-x-[-1]"
                />

                {/* Biometric Face Target Frame Overlay */}
                <div className="absolute inset-0 pointer-events-none flex items-center justify-center p-8">
                  <div
                    className={`relative w-48 h-56 sm:w-56 sm:h-64 rounded-3xl border-2 transition-all duration-300 ${
                      isBiometricVerified
                        ? 'border-emerald-400/80 shadow-[0_0_30px_rgba(52,211,153,0.25)]'
                        : faceDetected
                        ? 'border-amber-400/70 shadow-[0_0_20px_rgba(251,191,36,0.2)]'
                        : 'border-slate-600/50 border-dashed'
                    }`}
                  >
                    {/* Reticle corner markers */}
                    <div className="absolute -top-1.5 -left-1.5 w-4 h-4 border-t-2 border-l-2 border-emerald-400" />
                    <div className="absolute -top-1.5 -right-1.5 w-4 h-4 border-t-2 border-r-2 border-emerald-400" />
                    <div className="absolute -bottom-1.5 -left-1.5 w-4 h-4 border-b-2 border-l-2 border-emerald-400" />
                    <div className="absolute -bottom-1.5 -right-1.5 w-4 h-4 border-b-2 border-r-2 border-emerald-400" />

                    {/* Centering crosshairs */}
                    <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-3 h-3">
                      <div className="absolute top-1/2 left-0 w-full h-[1px] bg-emerald-400/50" />
                      <div className="absolute left-1/2 top-0 h-full w-[1px] bg-emerald-400/50" />
                    </div>
                  </div>
                </div>

                {/* Live MediaPipe Biometric HUD Tag */}
                <div className="absolute top-3 left-3 right-3 flex items-center justify-between gap-2 pointer-events-none">
                  <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-black/75 backdrop-blur-md border border-white/10 text-[11px]">
                    <Scan className={`h-3.5 w-3.5 ${isBiometricVerified ? 'text-emerald-400 animate-pulse' : 'text-amber-400'}`} />
                    <span className="font-semibold text-slate-200">
                      {isBiometricVerified ? 'Face & Features Verified' : 'Scanning Face & Landmarks…'}
                    </span>
                  </div>

                  <div className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-black/75 backdrop-blur-md border border-white/10 text-[10px] text-slate-300">
                    <span className={`w-1.5 h-1.5 rounded-full ${faceDetected ? 'bg-emerald-400' : 'bg-red-400'}`} />
                    <span>{faceDetected ? '1 Face Locked' : 'No Face'}</span>
                  </div>
                </div>

                {/* Warning message overlay if camera misaligned */}
                {facialStatus?.warningMessage && !isBiometricVerified && (
                  <div className="absolute top-12 inset-x-3 pointer-events-none">
                    <div className="bg-amber-500/90 backdrop-blur-md text-black font-semibold text-xs px-3 py-1.5 rounded-xl text-center shadow-lg animate-bounce">
                      {facialStatus.warningMessage}
                    </div>
                  </div>
                )}
              </>
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
            <span>Hardware & Biometrics Status</span>
            <span className={`font-semibold flex items-center gap-1 ${cameraPassed && micPassed && isBiometricVerified ? 'text-emerald-400' : 'text-amber-400'}`}>
              {cameraPassed && micPassed && isBiometricVerified ? (
                <>
                  <CheckCircle2 className="h-3.5 w-3.5" /> All Checks Passed
                </>
              ) : (
                <>
                  <AlertTriangle className="h-3.5 w-3.5" /> Face Verification Pending
                </>
              )}
            </span>
          </div>
        </div>

        {/* Right: Prerequisite Checklist & Biometric Verification */}
        <div className="space-y-4">
          <div className="rounded-2xl bg-surface-card border border-surface-border p-5 space-y-4 shadow-xl">
            <div className="flex items-center justify-between pb-1 border-b border-surface-border">
              <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider">
                Biometric & Hardware Checklist
              </h3>
              <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase ${
                isBiometricVerified
                  ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                  : 'bg-amber-500/15 text-amber-400 border border-amber-500/30'
              }`}>
                {isBiometricVerified ? 'Biometrics Verified' : 'Scanning'}
              </span>
            </div>

            {/* MediaPipe Face Check 1: Human Face Presence */}
            <div className="flex items-start gap-3 p-3 rounded-xl bg-surface/60 border border-slate-800/80">
              <div className={`p-2 rounded-lg ${faceDetected ? 'bg-emerald-500/10 text-emerald-400' : 'bg-amber-500/10 text-amber-400'}`}>
                <UserCheck className="h-4 w-4" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-semibold text-slate-200">Human Face Detection</h4>
                  {faceDetected ? (
                    <span className="text-[11px] font-bold text-emerald-400 flex items-center gap-1">
                      <Check className="h-3 w-3" /> VERIFIED
                    </span>
                  ) : (
                    <span className="text-[11px] font-bold text-amber-400">DETECTING</span>
                  )}
                </div>
                <p className="text-[11px] text-slate-400 mt-0.5">
                  Single candidate face must be clearly visible. No second person permitted.
                </p>
              </div>
            </div>

            {/* MediaPipe Face Check 2: Eyes Open & Eye Contact */}
            <div className="flex items-start gap-3 p-3 rounded-xl bg-surface/60 border border-slate-800/80">
              <div className={`p-2 rounded-lg ${eyesVerified ? 'bg-emerald-500/10 text-emerald-400' : 'bg-amber-500/10 text-amber-400'}`}>
                <Eye className="h-4 w-4" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-semibold text-slate-200">Eyes Open &amp; Visible</h4>
                  {eyesVerified ? (
                    <span className="text-[11px] font-bold text-emerald-400 flex items-center gap-1">
                      <Check className="h-3 w-3" /> VERIFIED
                    </span>
                  ) : (
                    <span className="text-[11px] font-bold text-amber-400">LOOK AT SCREEN</span>
                  )}
                </div>
                <p className="text-[11px] text-slate-400 mt-0.5">
                  Both eyes must be open and looking toward the screen for gaze estimation.
                </p>
              </div>
            </div>

            {/* MediaPipe Face Check 3: Nose & Facial Landmarks */}
            <div className="flex items-start gap-3 p-3 rounded-xl bg-surface/60 border border-slate-800/80">
              <div className={`p-2 rounded-lg ${noseVerified && mouthVerified ? 'bg-emerald-500/10 text-emerald-400' : 'bg-amber-500/10 text-amber-400'}`}>
                <Smile className="h-4 w-4" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-semibold text-slate-200">Nose &amp; Facial Structure</h4>
                  {noseVerified && mouthVerified ? (
                    <span className="text-[11px] font-bold text-emerald-400 flex items-center gap-1">
                      <Check className="h-3 w-3" /> 468 LANDMARKS
                    </span>
                  ) : (
                    <span className="text-[11px] font-bold text-amber-400">ALIGNING</span>
                  )}
                </div>
                <p className="text-[11px] text-slate-400 mt-0.5">
                  Nose bridge and mouth must remain unobscured for audio-visual proctoring.
                </p>
              </div>
            </div>

            {/* Hardware: Camera & Microphone */}
            <div className="grid grid-cols-2 gap-2">
              <div className="p-2.5 rounded-xl bg-surface/60 border border-slate-800/80 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Camera className={`h-3.5 w-3.5 ${cameraPassed ? 'text-emerald-400' : 'text-red-400'}`} />
                  <span className="text-xs text-slate-300">Camera</span>
                </div>
                <span className={`text-[10px] font-bold ${cameraPassed ? 'text-emerald-400' : 'text-red-400'}`}>
                  {cameraPassed ? 'ONLINE' : 'OFFLINE'}
                </span>
              </div>

              <div className="p-2.5 rounded-xl bg-surface/60 border border-slate-800/80 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Mic className={`h-3.5 w-3.5 ${micPassed ? 'text-emerald-400' : 'text-red-400'}`} />
                  <span className="text-xs text-slate-300">Microphone</span>
                </div>
                <span className={`text-[10px] font-bold ${micPassed ? 'text-emerald-400' : 'text-red-400'}`}>
                  {micPassed ? 'ONLINE' : 'OFFLINE'}
                </span>
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
            <p className="text-center text-[11px] text-slate-400">
              {!isBiometricVerified
                ? 'Align your face in the center frame with eyes & nose clearly visible.'
                : 'Check both examination agreements above to proceed.'}
            </p>
          )}
        </div>
      </div>
    </div>
  )
}

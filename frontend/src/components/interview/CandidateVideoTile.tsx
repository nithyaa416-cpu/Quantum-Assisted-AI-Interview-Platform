import { useEffect, useRef, useState, useCallback } from 'react'
import {
  Camera, Mic, ShieldAlert, ShieldCheck, Eye, EyeOff, Users,
  AlertTriangle, Smartphone, Sparkles
} from 'lucide-react'
import { registerMediaStream, unregisterMediaStream } from '@/utils/mediaStreamManager'
import { mediaPipeService, type FacialVerificationStatus } from '@/utils/mediaPipeService'
import { interviewAnalyticsCollector } from '@/utils/interviewAnalyticsCollector'

interface CandidateVideoTileProps {
  candidateName: string
  onHardwareError?: (err: string) => void
  onStreamReady?: (stream: MediaStream) => void
}

export function CandidateVideoTile({
  candidateName,
  onHardwareError,
  onStreamReady,
}: CandidateVideoTileProps) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const [stream, setStream] = useState<MediaStream | null>(null)
  const [hasPermission, setHasPermission] = useState<boolean | null>(null)
  const [audioLevel, setAudioLevel] = useState<number>(0)
  const [facialStatus, setFacialStatus] = useState<FacialVerificationStatus | null>(null)

  const audioContextRef = useRef<AudioContext | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const animFrameRef = useRef<number | null>(null)

  const onStreamReadyRef = useRef(onStreamReady)
  onStreamReadyRef.current = onStreamReady
  const onHardwareErrorRef = useRef(onHardwareError)
  onHardwareErrorRef.current = onHardwareError

  const handleFacialUpdate = useCallback((status: FacialVerificationStatus) => {
    setFacialStatus(status)
  }, [])

  useEffect(() => {
    let localStream: MediaStream | null = null

    const initMedia = async () => {
      try {
        const s = await navigator.mediaDevices.getUserMedia({
          video: { width: { ideal: 1280 }, height: { ideal: 720 } },
          audio: {
            echoCancellation: true,
            noiseSuppression: true,
            autoGainControl: true,
          },
        })
        localStream = s
        registerMediaStream(s)
        setStream(s)
        setHasPermission(true)
        onStreamReadyRef.current?.(s)

        if (videoRef.current) {
          videoRef.current.srcObject = s
          // Initialize MediaPipe face tracking & object detector
          mediaPipeService.init().then(() => {
            if (videoRef.current) {
              mediaPipeService.startTracking(videoRef.current, handleFacialUpdate)
            }
          })
        }

        // Live Audio Visualizer & Frequency Analyzer (Web Audio API)
        try {
          const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext
          if (AudioContextClass) {
            const ctx = new AudioContextClass()
            audioContextRef.current = ctx
            const source = ctx.createMediaStreamSource(s)
            const analyser = ctx.createAnalyser()
            analyser.fftSize = 64
            source.connect(analyser)
            analyserRef.current = analyser

            // Register with Interview Analytics Collector for voice modulation tracking
            interviewAnalyticsCollector.setAudioAnalyser(analyser)

            const pcmData = new Uint8Array(analyser.frequencyBinCount)
            const tick = () => {
              if (analyserRef.current) {
                analyserRef.current.getByteFrequencyData(pcmData)
                let sum = 0
                for (let i = 0; i < pcmData.length; i++) {
                  sum += pcmData[i]
                }
                const avg = sum / pcmData.length
                setAudioLevel(Math.min(100, Math.round((avg / 128) * 100)))
              }
              animFrameRef.current = requestAnimationFrame(tick)
            }
            tick()
          }
        } catch (e) {
          console.warn('AudioContext volume meter unavailable:', e)
        }
      } catch (err: any) {
        console.warn('Compulsory webcam/mic access failed:', err)
        setHasPermission(false)
        onHardwareErrorRef.current?.('Camera and microphone access are compulsory and must remain active.')
      }
    }

    initMedia()

    return () => {
      mediaPipeService.stopTracking(handleFacialUpdate)
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
  }, [handleFacialUpdate])

  const hasEyeContact = facialStatus ? facialStatus.eyeContact.hasEyeContact : true
  const eyeScore = facialStatus ? facialStatus.eyeContact.score : 100
  const faceCount = facialStatus ? facialStatus.faceCount : 1
  const phoneDetected = facialStatus ? facialStatus.phoneDetected : false
  const confidenceScore = facialStatus?.facialAnalysis?.confidenceScore ?? 85
  const expression = facialStatus?.facialAnalysis?.expression ?? 'neutral'

  return (
    <div className="relative w-full h-full rounded-2xl overflow-hidden bg-slate-900 border border-slate-800 shadow-2xl flex items-center justify-center">
      {hasPermission ? (
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          className="w-full h-full object-cover scale-x-[-1]"
        />
      ) : (
        <div className="flex flex-col items-center justify-center p-6 text-center space-y-3">
          <div className="w-16 h-16 rounded-2xl bg-red-500/10 border border-red-500/20 flex items-center justify-center text-red-400 animate-pulse">
            <ShieldAlert className="w-8 h-8" />
          </div>
          <div>
            <h4 className="text-sm font-bold text-red-300">Mandatory Camera Feed Offline</h4>
            <p className="text-[11px] text-slate-400 mt-1 max-w-xs">
              Continuous video feed is mandatory during this proctored examination. Please ensure your camera is connected.
            </p>
          </div>
        </div>
      )}

      {/* Top Left: Proctoring watermark */}
      <div className="absolute top-3 left-3 flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-black/65 backdrop-blur-md border border-white/10 text-[11px] text-slate-300">
        <ShieldCheck className="h-3.5 w-3.5 text-emerald-400" />
        <span>Strict AI Proctoring &bull; 1 Candidate Only</span>
      </div>

      {/* Top Right: Live Eye Contact & Poise HUD */}
      {facialStatus && (
        <div className="absolute top-3 right-3 flex items-center gap-2">
          {/* Facial Confidence Pill */}
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-black/75 backdrop-blur-md border border-white/10 text-[10px]">
            <Sparkles className="h-3 w-3 text-indigo-400" />
            <span className="font-semibold text-indigo-300">Poise: {confidenceScore}%</span>
            <span className="text-[9px] text-slate-400 capitalize">({expression})</span>
          </div>

          {/* Eye Contact Pill */}
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-black/75 backdrop-blur-md border border-white/10 text-[10px]">
            {hasEyeContact ? (
              <>
                <Eye className="h-3 w-3 text-emerald-400" />
                <span className="font-semibold text-emerald-300">Eye Contact {eyeScore}%</span>
              </>
            ) : (
              <>
                <EyeOff className="h-3 w-3 text-amber-400 animate-pulse" />
                <span className="font-semibold text-amber-300">Gaze Away ({facialStatus.eyeContact.gazeDirection})</span>
              </>
            )}
          </div>
        </div>
      )}

      {/* Mobile Phone Detected Critical Banner */}
      {phoneDetected && (
        <div className="absolute top-12 inset-x-3 z-30 pointer-events-none">
          <div className="bg-red-600/95 backdrop-blur-md text-white font-bold text-xs px-3 py-2.5 rounded-xl text-center shadow-2xl flex items-center justify-center gap-2 animate-bounce border border-red-400/40">
            <Smartphone className="w-4 h-4 text-amber-200" />
            <span>Mobile Phone Detected! Unauthorized devices are strictly prohibited.</span>
          </div>
        </div>
      )}

      {/* Multi-face alert warning */}
      {!phoneDetected && faceCount > 1 && (
        <div className="absolute top-12 inset-x-3 z-30 pointer-events-none">
          <div className="bg-red-600/95 backdrop-blur-md text-white font-bold text-xs px-3 py-2 rounded-xl text-center shadow-2xl flex items-center justify-center gap-2 animate-bounce border border-red-400/40">
            <Users className="w-4 h-4" />
            <span>Multiple Faces Detected ({faceCount})! Only the candidate is permitted.</span>
          </div>
        </div>
      )}

      {/* Candidate Absent alert */}
      {!phoneDetected && faceCount === 0 && (
        <div className="absolute top-12 inset-x-3 z-30 pointer-events-none">
          <div className="bg-amber-600/95 backdrop-blur-md text-white font-bold text-xs px-3 py-2 rounded-xl text-center shadow-2xl flex items-center justify-center gap-2 animate-pulse border border-amber-400/40">
            <AlertTriangle className="w-4 h-4" />
            <span>Candidate Absent! Please face the camera directly.</span>
          </div>
        </div>
      )}

      {/* Bottom candidate info bar */}
      <div className="absolute bottom-3 inset-x-3 flex items-center justify-between px-3 py-2 rounded-xl bg-black/70 backdrop-blur-md border border-white/10">
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-xs font-semibold text-slate-200 truncate">
            {candidateName} (Candidate)
          </span>
          <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 flex items-center gap-1">
            <Camera className="h-2.5 w-2.5" /> LIVE
          </span>
        </div>

        {/* Live audio level meter */}
        <div className="flex items-center gap-1.5" title="Live audio input">
          <div className="flex items-center gap-0.5">
            {[0.2, 0.4, 0.6, 0.8, 1.0].map((threshold, idx) => (
              <div
                key={idx}
                className={`w-1 rounded-full transition-all duration-75 ${
                  audioLevel / 100 >= threshold ? 'bg-emerald-400 h-3' : 'bg-slate-700 h-1.5'
                }`}
              />
            ))}
          </div>
          <Mic className="h-3 w-3 text-emerald-400 ml-0.5" />
          <span className="text-[10px] font-medium text-slate-300">MIC ON</span>
        </div>
      </div>
    </div>
  )
}

import { useEffect, useRef, useState } from 'react'
import { Camera, Mic, ShieldAlert, ShieldCheck } from 'lucide-react'
import { registerMediaStream, unregisterMediaStream } from '@/utils/mediaStreamManager'

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
  const audioContextRef = useRef<AudioContext | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const animFrameRef = useRef<number | null>(null)

  const onStreamReadyRef = useRef(onStreamReady)
  onStreamReadyRef.current = onStreamReady
  const onHardwareErrorRef = useRef(onHardwareError)
  onHardwareErrorRef.current = onHardwareError

  useEffect(() => {
    let localStream: MediaStream | null = null

    const initMedia = async () => {
      try {
        const s = await navigator.mediaDevices.getUserMedia({
          video: { width: { ideal: 1280 }, height: { ideal: 720 } },
          audio: true,
        })
        localStream = s
        registerMediaStream(s)
        setStream(s)
        setHasPermission(true)
        onStreamReadyRef.current?.(s)

        if (videoRef.current) {
          videoRef.current.srcObject = s
        }

        // Live Audio Visualizer (Web Audio API)
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

      {/* Security watermark */}
      <div className="absolute top-3 left-3 flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-black/65 backdrop-blur-md border border-white/10 text-[11px] text-slate-300">
        <ShieldCheck className="h-3.5 w-3.5 text-emerald-400" />
        <span>Monitored &bull; Camera &amp; Mic Locked ON</span>
      </div>

      {/* Bottom candidate info bar — no mute / no camera toggle buttons allowed */}
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

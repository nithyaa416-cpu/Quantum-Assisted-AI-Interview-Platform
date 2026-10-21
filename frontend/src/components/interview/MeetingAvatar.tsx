import { useEffect, useRef, useState, useCallback } from 'react'
import {
  Volume2, VolumeX, Bot, Sparkles, MessageSquare, RotateCcw
} from 'lucide-react'
import {
  stopAllAudioAndSpeech,
  getNewSpeechToken,
  isSpeechTokenValid,
  registerActiveAudio,
  registerActiveSourceNode,
  getSharedAudio,
  getGlobalAudioContext,
  unlockBrowserAudio,
} from '@/utils/audioSpeechManager'

export type AvatarState = 'speaking' | 'listening' | 'thinking' | 'idle'

interface MeetingAvatarProps {
  questionId: string
  questionText: string
  avatarState: AvatarState
  isMuted?: boolean
  onToggleMute?: () => void
  onSpeechEnd?: () => void
  showCaptions?: boolean
}

export function MeetingAvatar({
  questionId,
  questionText,
  avatarState,
  isMuted = false,
  onToggleMute,
  onSpeechEnd,
  showCaptions = true,
}: MeetingAvatarProps) {
  const [isSpeakingAudio, setIsSpeakingAudio] = useState(false)
  const [isAutoplayBlocked, setIsAutoplayBlocked] = useState(false)

  // Track the ID of the question that has successfully completed or is currently playing
  const completedQuestionIdRef = useRef<string | null>(null)
  const safetyTimerRef = useRef<any>(null)
  const currentUtteranceRef = useRef<SpeechSynthesisUtterance | null>(null)

  const onSpeechEndRef = useRef(onSpeechEnd)
  onSpeechEndRef.current = onSpeechEnd

  /**
   * Safe Web Speech API Fallback (with Chrome-specific keep-alive and anti-cancel delays)
   */
  const speakViaWebSpeech = useCallback((text: string, token: number, qId: string) => {
    if (!isSpeechTokenValid(token) || isMuted || typeof window === 'undefined' || !('speechSynthesis' in window)) {
      setIsSpeakingAudio(false)
      onSpeechEndRef.current?.()
      return
    }

    try {
      if (window.speechSynthesis.paused) {
        window.speechSynthesis.resume()
      }
      window.speechSynthesis.cancel()

      const utterance = new SpeechSynthesisUtterance(text)
      utterance.rate = 1.0
      utterance.pitch = 1.0
      utterance.lang = 'en-US'
      currentUtteranceRef.current = utterance

      const assignPreferredVoice = () => {
        const voices = window.speechSynthesis.getVoices()
        if (voices.length > 0) {
          const preferred = voices.find(
            (v) =>
              (v.name.includes('Google') ||
                v.name.includes('Natural') ||
                v.name.includes('Samantha') ||
                v.name.includes('Zira') ||
                v.name.includes('Aria') ||
                v.lang.startsWith('en')) &&
              !v.name.includes('David')
          )
          if (preferred) utterance.voice = preferred
        }
      }

      assignPreferredVoice()

      let keepaliveTimer: any = null

      const finishWebSpeech = () => {
        if (keepaliveTimer) clearInterval(keepaliveTimer)
        completedQuestionIdRef.current = qId
        setIsSpeakingAudio(false)
        onSpeechEndRef.current?.()
      }

      utterance.onstart = () => {
        if (!isSpeechTokenValid(token)) {
          window.speechSynthesis.cancel()
          finishWebSpeech()
          return
        }
        setIsAutoplayBlocked(false)
        setIsSpeakingAudio(true)

        // Chrome keepalive ping to prevent cut-off at 15s
        keepaliveTimer = setInterval(() => {
          if (window.speechSynthesis.speaking && !window.speechSynthesis.paused) {
            window.speechSynthesis.pause()
            window.speechSynthesis.resume()
          }
        }, 3500)
      }

      utterance.onend = () => {
        if (!isSpeechTokenValid(token)) return
        finishWebSpeech()
      }

      utterance.onerror = (e: any) => {
        if (keepaliveTimer) clearInterval(keepaliveTimer)
        console.warn('Web Speech API event:', e?.error)
        if (e?.error === 'not-allowed') {
          setIsAutoplayBlocked(true)
          completedQuestionIdRef.current = null
        }
        if (!isSpeechTokenValid(token)) return
        finishWebSpeech()
      }

      // 60ms delay ensures Chrome IPC cancel signal finishes before new speak starts
      setTimeout(() => {
        if (isSpeechTokenValid(token)) {
          window.speechSynthesis.speak(utterance)
        }
      }, 60)
    } catch (err) {
      console.warn('speakViaWebSpeech exception:', err)
      setIsSpeakingAudio(false)
      onSpeechEndRef.current?.()
    }
  }, [isMuted])

  /**
   * Main Question Speech Handler:
   * Strategy 1: Edge-TTS MP3 via Web Audio API (immune to autoplay block if AudioContext resumed)
   * Strategy 2: Edge-TTS MP3 via HTML5 Audio element
   * Strategy 3: Web Speech API synthesis
   */
  const speakQuestionOnce = useCallback(
    async (text: string, qId: string) => {
      if (isMuted || !text || text.includes('[CODING_PROBLEM]')) {
        setIsSpeakingAudio(false)
        completedQuestionIdRef.current = qId
        onSpeechEndRef.current?.()
        return
      }

      const token = getNewSpeechToken()

      if (safetyTimerRef.current) {
        clearTimeout(safetyTimerRef.current)
        safetyTimerRef.current = null
      }

      setIsSpeakingAudio(true)

      // Safety timeout: ensure mic activates even if speech engine stalls
      const words = text.split(/\s+/).filter(Boolean).length
      const maxDurationMs = Math.max(14000, words * 600)
      safetyTimerRef.current = setTimeout(() => {
        if (!isSpeechTokenValid(token)) return
        setIsSpeakingAudio(false)
        completedQuestionIdRef.current = qId
        onSpeechEndRef.current?.()
      }, maxDurationMs)

      // ── STRATEGY 1 & 2: Neural Edge-TTS ──
      try {
        const controller = new AbortController()
        const timeoutId = setTimeout(() => controller.abort(), 7000)

        // Fetch neural MP3 audio from backend
        const res = await fetch('/api/interview/tts/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text, voice: 'en-US-AriaNeural' }),
          signal: controller.signal,
        })
        clearTimeout(timeoutId)

        if (!res.ok) {
          throw new Error(`TTS server responded with ${res.status}`)
        }

        const arrayBuffer = await res.arrayBuffer()
        if (arrayBuffer.byteLength < 300) {
          throw new Error('TTS audio data is empty')
        }

        if (!isSpeechTokenValid(token)) return

        // 1. Try Web Audio API Buffer Playback First (bypasses HTML5 Audio autoplay policy)
        const ctx = getGlobalAudioContext()
        if (ctx && ctx.state === 'running') {
          try {
            // Need a slice because decodeAudioData detaches the buffer
            const audioBuffer = await ctx.decodeAudioData(arrayBuffer.slice(0))
            if (!isSpeechTokenValid(token)) return

            const sourceNode = ctx.createBufferSource()
            sourceNode.buffer = audioBuffer
            sourceNode.connect(ctx.destination)
            registerActiveSourceNode(sourceNode)

            sourceNode.onended = () => {
              if (!isSpeechTokenValid(token)) return
              if (safetyTimerRef.current) clearTimeout(safetyTimerRef.current)
              completedQuestionIdRef.current = qId
              setIsSpeakingAudio(false)
              onSpeechEndRef.current?.()
            }

            sourceNode.start(0)
            setIsAutoplayBlocked(false)
            setIsSpeakingAudio(true)
            return // Successfully playing through Web Audio API!
          } catch (webAudioErr) {
            console.debug('Web Audio buffer decode failed, trying HTML5 Audio:', webAudioErr)
          }
        }

        // 2. Try HTML5 Audio element
        const blob = new Blob([arrayBuffer], { type: 'audio/mpeg' })
        const blobUrl = URL.createObjectURL(blob)
        const audio = getSharedAudio()
        audio.src = blobUrl
        audio.volume = isMuted ? 0 : 1.0
        registerActiveAudio(audio)

        audio.onplay = () => {
          setIsAutoplayBlocked(false)
          setIsSpeakingAudio(true)
        }

        audio.onended = () => {
          URL.revokeObjectURL(blobUrl)
          if (!isSpeechTokenValid(token)) return
          if (safetyTimerRef.current) clearTimeout(safetyTimerRef.current)
          completedQuestionIdRef.current = qId
          setIsSpeakingAudio(false)
          onSpeechEndRef.current?.()
        }

        audio.onerror = () => {
          URL.revokeObjectURL(blobUrl)
          if (!isSpeechTokenValid(token)) return
          speakViaWebSpeech(text, token, qId)
        }

        try {
          await audio.play()
          setIsAutoplayBlocked(false)
          setIsSpeakingAudio(true)
          return
        } catch (playErr: any) {
          URL.revokeObjectURL(blobUrl)
          if (playErr?.name === 'NotAllowedError') {
            console.warn('Autoplay blocked by browser policy on HTML5 Audio.')
            setIsAutoplayBlocked(true)
            setIsSpeakingAudio(false)
            completedQuestionIdRef.current = null

            // Listen for ANY user gesture to instantly unblock
            const unblockAndPlay = () => {
              setIsAutoplayBlocked(false)
              unlockBrowserAudio()
              window.removeEventListener('click', unblockAndPlay)
              window.removeEventListener('keydown', unblockAndPlay)
              window.removeEventListener('pointerdown', unblockAndPlay)
              speakQuestionOnce(text, qId)
            }
            window.addEventListener('click', unblockAndPlay, { once: true })
            window.addEventListener('keydown', unblockAndPlay, { once: true })
            window.addEventListener('pointerdown', unblockAndPlay, { once: true })
            return
          }
          throw playErr
        }
      } catch (err: any) {
        if (!isSpeechTokenValid(token)) return
        console.warn('Edge-TTS unavailable, falling back to Web Speech synthesis:', err?.message)
        speakViaWebSpeech(text, token, qId)
      }
    },
    [isMuted, speakViaWebSpeech]
  )

  // Trigger speech when questionId or questionText changes
  useEffect(() => {
    if (!questionId || !questionText) return

    // Don't re-trigger if this exact question was already completed
    if (completedQuestionIdRef.current === questionId) {
      return
    }

    speakQuestionOnce(questionText, questionId)

    // On unmount (e.g. StrictMode unmount-remount), allow re-triggering if not finished
    return () => {
      if (completedQuestionIdRef.current !== questionId) {
        completedQuestionIdRef.current = null
      }
      if (safetyTimerRef.current) clearTimeout(safetyTimerRef.current)
      stopAllAudioAndSpeech()
    }
  }, [questionId, questionText, speakQuestionOnce])

  // Stop immediately if muted
  useEffect(() => {
    if (isMuted) {
      if (safetyTimerRef.current) clearTimeout(safetyTimerRef.current)
      stopAllAudioAndSpeech()
      setIsSpeakingAudio(false)
    }
  }, [isMuted])

  // Manual replay button handler
  const handleManualReplay = () => {
    unlockBrowserAudio()
    setIsAutoplayBlocked(false)
    if (questionText && questionId) {
      completedQuestionIdRef.current = null
      speakQuestionOnce(questionText, questionId)
    }
  }

  const effectiveState = isSpeakingAudio ? 'speaking' : avatarState

  return (
    <div className="relative w-full h-full rounded-2xl overflow-hidden bg-gradient-to-b from-slate-900 via-slate-950 to-slate-900 border border-slate-800 shadow-2xl flex flex-col items-center justify-center p-4 select-none">
      {/* Dynamic ambient lighting based on state */}
      <div
        className={`absolute inset-0 opacity-25 pointer-events-none transition-all duration-700 ${
          effectiveState === 'speaking'
            ? 'bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-brand-500/40 via-purple-500/10 to-transparent'
            : effectiveState === 'listening'
            ? 'bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-emerald-500/40 via-teal-500/10 to-transparent'
            : effectiveState === 'thinking'
            ? 'bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-amber-500/40 via-orange-500/10 to-transparent'
            : 'bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-slate-700/20 to-transparent'
        }`}
      />

      {/* Top Header on Avatar Tile */}
      <div className="absolute top-3 inset-x-3 flex items-center justify-between z-10">
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-black/60 backdrop-blur-md border border-white/10 text-xs text-slate-200">
          <Bot className="h-4 w-4 text-brand-400" />
          <span className="font-semibold text-slate-100">AI Examiner</span>
          <span className="text-slate-400 text-[11px]">&bull; Voice Active</span>
        </div>

        {/* Status indicator and Controls */}
        <div className="flex items-center gap-2">
          <div
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold uppercase tracking-wider backdrop-blur-md border ${
              effectiveState === 'speaking'
                ? 'bg-brand-500/20 text-brand-300 border-brand-500/40 animate-pulse'
                : effectiveState === 'listening'
                ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40 animate-pulse'
                : effectiveState === 'thinking'
                ? 'bg-amber-500/20 text-amber-300 border-amber-500/40 animate-pulse'
                : 'bg-slate-800/80 text-slate-400 border-slate-700'
            }`}
          >
            <span
              className={`w-2 h-2 rounded-full ${
                effectiveState === 'speaking'
                  ? 'bg-brand-400'
                  : effectiveState === 'listening'
                  ? 'bg-emerald-400'
                  : effectiveState === 'thinking'
                  ? 'bg-amber-400'
                  : 'bg-slate-500'
              }`}
            />
            {effectiveState === 'speaking'
              ? 'Asking Question'
              : effectiveState === 'listening'
              ? 'Listening to Candidate'
              : effectiveState === 'thinking'
              ? 'Analyzing Answer'
              : 'Standby'}
          </div>

          <button
            type="button"
            onClick={handleManualReplay}
            className="p-1.5 rounded-full bg-black/60 hover:bg-slate-800 border border-white/10 text-slate-300 hover:text-white transition-colors"
            title="Replay Question Audio"
          >
            <RotateCcw className="h-3.5 w-3.5" />
          </button>

          <button
            type="button"
            onClick={onToggleMute}
            className="p-1.5 rounded-full bg-black/60 hover:bg-slate-800 border border-white/10 text-slate-300 hover:text-white transition-colors"
            title={isMuted ? 'Unmute Audio' : 'Mute Audio'}
          >
            {isMuted ? <VolumeX className="h-3.5 w-3.5 text-red-400" /> : <Volume2 className="h-3.5 w-3.5 text-slate-300" />}
          </button>
        </div>
      </div>

      {/* Animated Avatar Graphic */}
      <div className="relative my-auto flex flex-col items-center justify-center">
        <div
          className={`absolute w-56 h-56 rounded-full transition-all duration-700 pointer-events-none ${
            effectiveState === 'speaking'
              ? 'border-2 border-brand-500/30 scale-110 animate-ping'
              : effectiveState === 'listening'
              ? 'border-2 border-emerald-500/30 scale-105 animate-pulse'
              : 'border border-slate-700/20'
          }`}
        />

        <div
          className={`relative w-40 h-40 sm:w-48 sm:h-48 rounded-full flex items-center justify-center p-2 transition-all duration-500 shadow-2xl ${
            effectiveState === 'speaking'
              ? 'bg-gradient-to-tr from-brand-600 via-indigo-500 to-purple-500 ring-4 ring-brand-400/40 shadow-brand-500/30'
              : effectiveState === 'listening'
              ? 'bg-gradient-to-tr from-emerald-600 via-teal-500 to-cyan-500 ring-4 ring-emerald-400/40 shadow-emerald-500/30'
              : effectiveState === 'thinking'
              ? 'bg-gradient-to-tr from-amber-600 via-orange-500 to-yellow-500 ring-4 ring-amber-400/40 shadow-amber-500/30'
              : 'bg-gradient-to-tr from-slate-700 via-slate-800 to-slate-900 ring-2 ring-slate-700'
          }`}
        >
          <div className="w-full h-full rounded-full bg-slate-950 flex flex-col items-center justify-center overflow-hidden border border-white/10 relative">
            <div className="relative flex flex-col items-center gap-3">
              {/* Eyes */}
              <div className="flex items-center gap-6">
                <div
                  className={`w-3.5 h-3.5 rounded-full transition-all duration-300 ${
                    effectiveState === 'speaking'
                      ? 'bg-brand-300 shadow-[0_0_12px_#38bdf8] scale-110'
                      : effectiveState === 'listening'
                      ? 'bg-emerald-300 shadow-[0_0_12px_#34d399]'
                      : 'bg-slate-400'
                  }`}
                />
                <div
                  className={`w-3.5 h-3.5 rounded-full transition-all duration-300 ${
                    effectiveState === 'speaking'
                      ? 'bg-brand-300 shadow-[0_0_12px_#38bdf8] scale-110'
                      : effectiveState === 'listening'
                      ? 'bg-emerald-300 shadow-[0_0_12px_#34d399]'
                      : 'bg-slate-400'
                  }`}
                />
              </div>

              {/* Mouth Waveform / Speaking Animation */}
              <div className="flex items-center gap-1 h-5">
                {effectiveState === 'speaking' ? (
                  [0.3, 0.8, 1.0, 0.7, 0.4].map((h, i) => (
                    <div
                      key={i}
                      className="w-1.5 rounded-full bg-brand-400 shadow-[0_0_8px_#38bdf8]"
                      style={{
                        height: `${h * 18}px`,
                        animation: `mouthPulse 0.4s ease-in-out ${i * 0.08}s infinite alternate`,
                      }}
                    />
                  ))
                ) : effectiveState === 'listening' ? (
                  <div className="w-8 h-1 rounded-full bg-emerald-400/80 animate-pulse shadow-[0_0_6px_#34d399]" />
                ) : effectiveState === 'thinking' ? (
                  <div className="flex gap-1">
                    {[0, 1, 2].map((i) => (
                      <div
                        key={i}
                        className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-bounce"
                        style={{ animationDelay: `${i * 0.15}s` }}
                      />
                    ))}
                  </div>
                ) : (
                  <div className="w-6 h-0.5 rounded-full bg-slate-600" />
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Autoplay blocked banner - allows candidate to enable audio with a single tap if browser blocked it */}
      {isAutoplayBlocked && (
        <div className="mb-3 z-30 animate-bounce">
          <button
            type="button"
            onClick={handleManualReplay}
            className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-brand-600 via-indigo-600 to-purple-600 hover:from-brand-500 hover:to-indigo-500 text-white text-xs font-bold shadow-2xl border border-white/20 flex items-center gap-2 cursor-pointer transition-transform hover:scale-105"
          >
            <Volume2 className="h-4 w-4 text-emerald-300 animate-pulse" />
            <span>🔊 Click to Hear Alex Speak Question</span>
          </button>
        </div>
      )}

      {/* Closed Captions Subtitles */}
      {showCaptions && questionText && (
        <div className="w-full max-w-xl px-4 py-3 rounded-xl bg-black/75 backdrop-blur-md border border-white/10 text-center shadow-lg transition-all z-10">
          <div className="flex items-center justify-center gap-1.5 text-[10px] uppercase font-bold tracking-wider text-brand-400 mb-1">
            <MessageSquare className="h-3 w-3" />
            <span>Question Prompt</span>
          </div>
          <p className="text-xs sm:text-sm font-medium text-slate-100 leading-relaxed">
            "{questionText}"
          </p>
        </div>
      )}

      <style>{`
        @keyframes mouthPulse {
          from { transform: scaleY(0.3); opacity: 0.7; }
          to   { transform: scaleY(1.3); opacity: 1; }
        }
      `}</style>
    </div>
  )
}

import { useEffect, useRef, useState, useCallback } from 'react'
import { Volume2, VolumeX, RotateCcw, Bot, MessageSquare } from 'lucide-react'
import {
  stopAllAudioAndSpeech,
  getNewSpeechToken,
  isSpeechTokenValid,
  registerActiveAudio,
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
  const spokenQuestionIdRef = useRef<string | null>(null)
  const safetyTimerRef = useRef<any>(null)

  const onSpeechEndRef = useRef(onSpeechEnd)
  onSpeechEndRef.current = onSpeechEnd

  const speakViaWebSpeech = useCallback((text: string, token: number) => {
    if (!isSpeechTokenValid(token) || isMuted || typeof window === 'undefined') {
      setIsSpeakingAudio(false)
      onSpeechEndRef.current?.()
      return
    }

    try {
      window.speechSynthesis.cancel()
      const utterance = new SpeechSynthesisUtterance(text)
      utterance.rate = 1.0
      utterance.pitch = 1.0

      const voices = window.speechSynthesis.getVoices()
      const preferred = voices.find(
        (v) =>
          (v.name.includes('Google') ||
            v.name.includes('Natural') ||
            v.name.includes('Samantha') ||
            v.name.includes('Zira') ||
            v.lang.startsWith('en')) &&
          !v.name.includes('David')
      )
      if (preferred) utterance.voice = preferred

      utterance.onstart = () => {
        if (!isSpeechTokenValid(token)) {
          window.speechSynthesis.cancel()
          return
        }
        setIsSpeakingAudio(true)
      }

      utterance.onend = () => {
        if (!isSpeechTokenValid(token)) return
        setIsSpeakingAudio(false)
        onSpeechEndRef.current?.()
      }

      utterance.onerror = () => {
        if (!isSpeechTokenValid(token)) return
        setIsSpeakingAudio(false)
        onSpeechEndRef.current?.()
      }

      window.speechSynthesis.speak(utterance)
    } catch {
      setIsSpeakingAudio(false)
      onSpeechEndRef.current?.()
    }
  }, [isMuted])

  const speakQuestionOnce = useCallback(
    async (text: string) => {
      // 1. Instantly invalidate all previous speech and stop any playing audio or speechSynthesis
      const token = getNewSpeechToken()
      if (safetyTimerRef.current) {
        clearTimeout(safetyTimerRef.current)
        safetyTimerRef.current = null
      }

      if (isMuted || !text) {
        setIsSpeakingAudio(false)
        onSpeechEndRef.current?.()
        return
      }

      setIsSpeakingAudio(true)

      // Fallback timer: ensure speech end fires within a reasonable window so listening is never blocked
      const fallbackDuration = Math.min(10000, Math.max(3000, text.split(/\s+/).length * 400))
      safetyTimerRef.current = setTimeout(() => {
        if (!isSpeechTokenValid(token)) return
        setIsSpeakingAudio(false)
        onSpeechEndRef.current?.()
      }, fallbackDuration)

      // Try edge-tts via backend API
      try {
        const audio = new Audio(`/api/interview/tts/?text=${encodeURIComponent(text)}`)
        registerActiveAudio(audio)

        audio.onended = () => {
          if (!isSpeechTokenValid(token)) return
          if (safetyTimerRef.current) clearTimeout(safetyTimerRef.current)
          setIsSpeakingAudio(false)
          onSpeechEndRef.current?.()
        }

        audio.onerror = (e) => {
          // If this token was invalidated (e.g. question advanced or stopped), DO NOT fallback!
          if (!isSpeechTokenValid(token)) return
          if (safetyTimerRef.current) clearTimeout(safetyTimerRef.current)
          console.warn('edge-tts failed, falling back to Web Speech API:', e)
          speakViaWebSpeech(text, token)
        }

        await audio.play()
      } catch (err: any) {
        // If aborted or invalidated by a newer question, do NOT fallback
        if (!isSpeechTokenValid(token)) return
        if (safetyTimerRef.current) clearTimeout(safetyTimerRef.current)
        console.warn('Audio play failed, falling back to Web Speech:', err)
        speakViaWebSpeech(text, token)
      }
    },
    [isMuted, speakViaWebSpeech]
  )

  // Trigger speech EXACTLY ONCE per questionId
  useEffect(() => {
    if (!questionId || !questionText) return

    // If this question has already been spoken, do NOT speak it again!
    if (spokenQuestionIdRef.current === questionId) {
      return
    }

    spokenQuestionIdRef.current = questionId
    speakQuestionOnce(questionText)
  }, [questionId, questionText, speakQuestionOnce])

  // Stop immediately if muted
  useEffect(() => {
    if (isMuted) {
      if (safetyTimerRef.current) clearTimeout(safetyTimerRef.current)
      stopAllAudioAndSpeech()
      setIsSpeakingAudio(false)
    }
  }, [isMuted])

  // Clean up on unmount
  useEffect(() => {
    return () => {
      if (safetyTimerRef.current) clearTimeout(safetyTimerRef.current)
      stopAllAudioAndSpeech()
    }
  }, [])

  // Manual replay button
  const handleManualReplay = () => {
    if (questionText) {
      speakQuestionOnce(questionText)
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
          <span className="text-slate-400 text-[11px]">&bull; Llama 3 Evaluation</span>
        </div>

        {/* Status indicator and Replay button */}
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
            title="Replay Question Audio (1 time)"
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

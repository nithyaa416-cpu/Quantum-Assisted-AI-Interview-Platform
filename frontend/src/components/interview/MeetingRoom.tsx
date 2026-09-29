import { useState, useEffect, useRef, useCallback } from 'react'
import {
  PhoneOff, Maximize2, Minimize2, MessageSquare,
  Sparkles, ChevronRight, Mic, Clock, Cpu, Volume2
} from 'lucide-react'
import toast from 'react-hot-toast'

import { MeetingAvatar, AvatarState } from './MeetingAvatar'
import { CandidateVideoTile } from './CandidateVideoTile'
import { ProctoringShield } from './ProctoringShield'
import { SessionTimer } from './InterviewTimer'
import { Button } from '@/components/ui/Button'
import { Spinner } from '@/components/ui/Spinner'
import { stopAllMediaStreams, getActiveMediaStream } from '@/utils/mediaStreamManager'
import { stopAllAudioAndSpeech } from '@/utils/audioSpeechManager'
import { interviewService } from '@/services/interviewService'
import type { InterviewSession, InterviewQuestion, SubmitResponseResult } from '@/types'

interface MeetingRoomProps {
  session: InterviewSession
  currentQuestion: InterviewQuestion | null
  lastFeedback: SubmitResponseResult | null
  isSubmitting: boolean
  isEnding: boolean
  onSubmitAnswer: (answer: string, durationSeconds: number) => Promise<void>
  onContinueNext: () => Promise<void>
  onEndInterview: () => Promise<void>
  candidateName: string
}

export function MeetingRoom({
  session,
  currentQuestion,
  lastFeedback,
  isSubmitting,
  isEnding,
  onSubmitAnswer,
  onContinueNext,
  onEndInterview,
  candidateName,
}: MeetingRoomProps) {
  const [showCaptions, setShowCaptions] = useState(true)
  const [isFullscreen, setIsFullscreen] = useState(Boolean(document.fullscreenElement))

  // Live Speech-to-Text states (Strictly Read-only, verbal hands-free)
  const [transcript, setTranscript] = useState('')
  const [interimTranscript, setInterimTranscript] = useState('')
  const [isListening, setIsListening] = useState(false)
  const [speechStartTime, setSpeechStartTime] = useState<number>(Date.now())
  const [avatarState, setAvatarState] = useState<AvatarState>('speaking')

  // Auto-Analyze & Silence Detection state
  const [silenceCountdown, setSilenceCountdown] = useState<number | null>(null)
  const silenceTimerRef = useRef<any>(null)
  const countdownIntervalRef = useRef<any>(null)

  // Auto-Advance countdown state (Hands-Free next question)
  const [autoAdvanceCountdown, setAutoAdvanceCountdown] = useState<number | null>(null)
  const autoAdvanceTimerRef = useRef<any>(null)

  // Robust listening control refs to eliminate stale closure bugs
  const shouldListenRef = useRef<boolean>(false)
  const isSubmittingRef = useRef<boolean>(false)
  isSubmittingRef.current = isSubmitting || Boolean(lastFeedback)
  const fullTranscriptRef = useRef<string>('')
  const recognitionRef = useRef<any>(null)

  // Callbacks refs to break circular dependency between effects and handlers
  const startListeningRef = useRef<() => void>(() => {})
  const stopListeningRef = useRef<() => void>(() => {})
  const handleSubmitRef = useRef<() => Promise<void>>(async () => {})

  // Faster-Whisper Audio Recording
  const mediaStreamRef = useRef<MediaStream | null>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])
  const [isWhisperProcessing, setIsWhisperProcessing] = useState(false)

  const clearSilenceTimers = useCallback(() => {
    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current)
      silenceTimerRef.current = null
    }
    if (countdownIntervalRef.current) {
      clearInterval(countdownIntervalRef.current)
      countdownIntervalRef.current = null
    }
    setSilenceCountdown(null)
  }, [])

  const clearAutoAdvanceTimer = useCallback(() => {
    if (autoAdvanceTimerRef.current) {
      clearInterval(autoAdvanceTimerRef.current)
      autoAdvanceTimerRef.current = null
    }
    setAutoAdvanceCountdown(null)
  }, [])

  // Stop all camera and audio streams on unmount to turn off webcam light immediately
  useEffect(() => {
    return () => {
      shouldListenRef.current = false
      stopAllAudioAndSpeech()
      stopAllMediaStreams()
      clearSilenceTimers()
      clearAutoAdvanceTimer()
      if (recognitionRef.current) {
        try { recognitionRef.current.stop() } catch {}
      }
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
        try { mediaRecorderRef.current.stop() } catch {}
      }
    }
  }, [clearAutoAdvanceTimer, clearSilenceTimers])

  // ── Start Audio Recording for Whisper STT ──────────────────────────────────
  const startAudioRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      return // Already recording continuous answer audio
    }

    if (!mediaStreamRef.current) {
      const activeStream = getActiveMediaStream()
      if (activeStream) {
        mediaStreamRef.current = activeStream
      }
    }

    if (!mediaStreamRef.current) return

    try {
      audioChunksRef.current = []
      const mimeTypes = ['audio/webm;codecs=opus', 'audio/webm', 'audio/ogg;codecs=opus', 'audio/mp4']
      const supportedMime = mimeTypes.find((type) => MediaRecorder.isTypeSupported(type)) || ''

      const recorder = supportedMime
        ? new MediaRecorder(mediaStreamRef.current, { mimeType: supportedMime })
        : new MediaRecorder(mediaStreamRef.current)

      recorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) {
          audioChunksRef.current.push(e.data)
        }
      }

      recorder.start(250) // collect chunks every 250ms
      mediaRecorderRef.current = recorder
    } catch (e) {
      console.warn('MediaRecorder error for Whisper:', e)
    }
  }, [])

  const stopAudioRecording = useCallback((): Promise<Blob | null> => {
    return new Promise((resolve) => {
      if (!mediaRecorderRef.current || mediaRecorderRef.current.state === 'inactive') {
        if (audioChunksRef.current.length > 0) {
          resolve(new Blob(audioChunksRef.current, { type: 'audio/webm' }))
        } else {
          resolve(null)
        }
        return
      }

      mediaRecorderRef.current.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' })
        resolve(audioBlob)
      }

      try {
        mediaRecorderRef.current.stop()
      } catch {
        resolve(null)
      }
    })
  }, [])

  const stopListening = useCallback(() => {
    shouldListenRef.current = false
    if (recognitionRef.current) {
      try {
        recognitionRef.current.onend = null
        recognitionRef.current.onerror = null
        recognitionRef.current.stop()
      } catch {}
      recognitionRef.current = null
    }
    setIsListening(false)
  }, [])
  stopListeningRef.current = stopListening

  // ── Hands-Free Silence Detection & Auto-Submit ──────────────────────────────
  // Gives candidate generous time to think (5s pause before auto-analyzing)
  const resetSilenceDetection = useCallback((currentText: string) => {
    clearSilenceTimers()

    const words = currentText.trim().split(/\s+/).filter(Boolean)
    // Only arm auto-submission if candidate has spoken at least 4 words
    if (words.length < 4) return

    let remaining = 5
    setSilenceCountdown(remaining)

    countdownIntervalRef.current = setInterval(() => {
      remaining -= 1
      if (remaining <= 0) {
        if (countdownIntervalRef.current) clearInterval(countdownIntervalRef.current)
      } else {
        setSilenceCountdown(remaining)
      }
    }, 1000)

    silenceTimerRef.current = setTimeout(() => {
      setSilenceCountdown(null)
      if (!isSubmittingRef.current && shouldListenRef.current) {
        handleSubmitRef.current()
      }
    }, 5000)
  }, [clearSilenceTimers])

  const startListening = useCallback(() => {
    shouldListenRef.current = true
    startAudioRecording()

    const SR: any = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
    if (!SR) {
      console.warn('SpeechRecognition API not available in this browser')
      setIsListening(true)
      return
    }

    try {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.onend = null
          recognitionRef.current.onerror = null
          recognitionRef.current.abort()
        } catch {}
        recognitionRef.current = null
      }

      const rec = new SR()
      rec.continuous = true
      rec.interimResults = true
      rec.lang = 'en-US'
      rec.maxAlternatives = 1

      rec.onstart = () => {
        setIsListening(true)
        setAvatarState('listening')
      }

      rec.onresult = (event: any) => {
        let finalChunk = ''
        let interimChunk = ''

        for (let i = event.resultIndex; i < event.results.length; i++) {
          const res = event.results[i]
          if (res.isFinal) {
            finalChunk += res[0].transcript + ' '
          } else {
            interimChunk += res[0].transcript
          }
        }

        if (finalChunk) {
          fullTranscriptRef.current = (fullTranscriptRef.current ? fullTranscriptRef.current.trim() + ' ' + finalChunk.trim() : finalChunk.trim())
          setTranscript(fullTranscriptRef.current)
        }
        setInterimTranscript(interimChunk)

        const totalSpoken = (fullTranscriptRef.current + ' ' + interimChunk).trim()
        // Arm or reset silence detection for auto-submission
        resetSilenceDetection(totalSpoken)
      }

      rec.onerror = (e: any) => {
        // 'no-speech' is expected when candidate pauses to think - do NOT stop listening!
        if (e.error !== 'no-speech') {
          console.warn('Speech recognition warning:', e.error)
        }
      }

      rec.onend = () => {
        // ALWAYS auto-restart with fresh recognition instance so pausing 2-4 seconds never kills the mic!
        if (shouldListenRef.current && !isSubmittingRef.current) {
          setTimeout(() => {
            if (shouldListenRef.current && !isSubmittingRef.current) {
              startListeningRef.current()
            }
          }, 100)
        } else {
          setIsListening(false)
        }
      }

      rec.start()
      recognitionRef.current = rec
    } catch (e) {
      console.warn('Failed to start speech recognition:', e)
    }
  }, [resetSilenceDetection, startAudioRecording])
  startListeningRef.current = startListening

  // ── Submission: High-Accuracy Whisper Transcription + Dynamic AI Follow-Up ───
  const handleSubmit = useCallback(async () => {
    stopAllAudioAndSpeech()
    clearSilenceTimers()
    shouldListenRef.current = false
    stopListening()
    setAvatarState('thinking')

    const rawSpoken = (fullTranscriptRef.current + ' ' + interimTranscript).trim()
    const wordList = rawSpoken.split(/\s+/).filter(Boolean)

    if (wordList.length < 3) {
      // Candidate paused too early before saying anything substantial; resume listening!
      setAvatarState('listening')
      startListeningRef.current()
      return
    }

    // Capture recorded audio and send to faster-whisper for exact technical terms
    let finalAnswerText = rawSpoken
    setIsWhisperProcessing(true)
    try {
      const audioBlob = await stopAudioRecording()
      if (audioBlob && audioBlob.size > 2000) {
        const whisperText = await interviewService.transcribeAudio(audioBlob)
        if (whisperText && whisperText.trim().split(/\s+/).length >= 3) {
          finalAnswerText = whisperText.trim()
          fullTranscriptRef.current = finalAnswerText
          setTranscript(finalAnswerText)
          setInterimTranscript('')
        }
      }
    } catch (err) {
      console.warn('Whisper refinement skipped, using live transcript:', err)
    } finally {
      setIsWhisperProcessing(false)
    }

    const durationSeconds = Math.max(5, Math.round((Date.now() - speechStartTime) / 1000))
    await onSubmitAnswer(finalAnswerText, durationSeconds)
  }, [clearSilenceTimers, interimTranscript, onSubmitAnswer, speechStartTime, stopAudioRecording, stopListening])
  handleSubmitRef.current = handleSubmit

  // When AI finishes speaking the question ONCE, start listening to candidate
  const handleAISpeechEnd = useCallback(() => {
    setAvatarState('listening')
    startListeningRef.current()
  }, [])

  // Reset states and auto-start listening when current question changes
  useEffect(() => {
    shouldListenRef.current = false
    stopListeningRef.current()
    stopAudioRecording()
    clearSilenceTimers()
    clearAutoAdvanceTimer()
    setTranscript('')
    setInterimTranscript('')
    fullTranscriptRef.current = ''
    setSpeechStartTime(Date.now())
    setAvatarState('speaking')

    // Automatically ensure the microphone turns on within 1.2s so the candidate
    // is heard immediately, even if audio playback takes time or they start speaking right away!
    const autoListenTimer = setTimeout(() => {
      startListeningRef.current()
    }, 1200)

    return () => clearTimeout(autoListenTimer)
  }, [clearAutoAdvanceTimer, clearSilenceTimers, currentQuestion?.id, stopAudioRecording])

  const handleContinue = useCallback(async () => {
    clearAutoAdvanceTimer()
    await onContinueNext()
    setAvatarState('speaking')
  }, [clearAutoAdvanceTimer, onContinueNext])

  // ── Hands-Free Auto-Advance: Countdown when feedback arrives ───────────────
  useEffect(() => {
    if (lastFeedback) {
      shouldListenRef.current = false
      clearSilenceTimers()
      stopListening()
      stopAudioRecording()

      // Start 3.5-second countdown to automatically advance to next question
      setAutoAdvanceCountdown(3)
      let secondsLeft = 3
      autoAdvanceTimerRef.current = setInterval(() => {
        secondsLeft -= 1
        if (secondsLeft <= 0) {
          clearAutoAdvanceTimer()
          handleContinue()
        } else {
          setAutoAdvanceCountdown(secondsLeft)
        }
      }, 1000)
    } else {
      clearAutoAdvanceTimer()
    }
    return () => {
      clearAutoAdvanceTimer()
    }
  }, [clearAutoAdvanceTimer, clearSilenceTimers, handleContinue, lastFeedback, stopAudioRecording, stopListening])

  const toggleFullscreen = async () => {
    if (!document.fullscreenElement) {
      try {
        await document.documentElement.requestFullscreen()
        setIsFullscreen(true)
      } catch (e) {
        console.warn('Fullscreen failed:', e)
      }
    } else {
      try {
        await document.exitFullscreen()
        setIsFullscreen(false)
      } catch (e) {
        console.warn('Exit fullscreen failed:', e)
      }
    }
  }

  const handleLeaveInterview = async () => {
    shouldListenRef.current = false
    stopAllAudioAndSpeech()
    stopAllMediaStreams()
    clearSilenceTimers()
    clearAutoAdvanceTimer()
    stopListening()
    await onEndInterview()
  }

  const fullLiveText = (transcript + (interimTranscript ? ' ' + interimTranscript : '')).trim()
  const qText = currentQuestion?.text || ''
  const qId = currentQuestion?.id || ''

  return (
    <div className="relative w-screen h-screen bg-slate-950 text-slate-100 flex flex-col overflow-hidden select-none">
      {/* 1. Strict Proctoring Shield */}
      <ProctoringShield
        onViolation={(count, reason) => {
          toast.error(`Proctoring Strike ${count}: ${reason}`, { duration: 4000 })
        }}
      />

      {/* 2. Top Examination Header Bar */}
      <header className="h-14 px-6 flex items-center justify-between border-b border-slate-800 bg-slate-900/80 backdrop-blur-md z-30">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-brand-600 to-indigo-500 flex items-center justify-center font-bold text-white text-sm shadow-md">
            Q
          </div>
          <div>
            <h2 className="text-sm font-bold text-slate-100 flex items-center gap-2">
              Proctored AI Examination
              <span className="text-[11px] font-medium px-2 py-0.5 rounded-full bg-brand-500/20 text-brand-300 border border-brand-500/30">
                {session.target_role || 'Software Engineering'}
              </span>
            </h2>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="hidden sm:flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-800 border border-slate-700 text-xs text-slate-300">
            <span className="w-2 h-2 rounded-full bg-brand-400"></span>
            <span className="capitalize">{currentQuestion?.phase || session.current_phase} Phase</span>
            <span className="text-slate-500">&bull; Question {session.turn_count || 1}</span>
          </div>

          <SessionTimer startedAt={session.started_at} isActive={true} />

          <Button
            variant="ghost"
            size="sm"
            onClick={toggleFullscreen}
            className="text-slate-400 hover:text-white"
            title={isFullscreen ? 'Exit Full Screen' : 'Enter Full Screen'}
          >
            {isFullscreen ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
          </Button>
        </div>
      </header>

      {/* 3. Main Examination Grid */}
      <main className="flex-1 p-4 sm:p-6 grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6 min-h-0 relative z-20">
        {/* Left Tile: AI Examiner Avatar (Speaks Question ONCE via edge-tts) */}
        <div className="w-full h-full min-h-[300px]">
          <MeetingAvatar
            questionId={qId}
            questionText={qText}
            avatarState={avatarState}
            onSpeechEnd={handleAISpeechEnd}
            showCaptions={showCaptions}
          />
        </div>

        {/* Right Tile: Candidate Compulsory Video & Hands-Free Verbal Transcript */}
        <div className="w-full h-full flex flex-col gap-4 min-h-[300px]">
          {/* Candidate Webcam (Compulsory: NO user mute / NO camera off) */}
          <div className="flex-1 min-h-[220px]">
            <CandidateVideoTile
              candidateName={candidateName}
              onStreamReady={(stream) => {
                mediaStreamRef.current = stream
              }}
            />
          </div>

          {/* Real-time Voice Answer Transcription Box (Read-Only: candidate speaks hands-free) */}
          <div className="h-52 rounded-2xl bg-slate-900/90 border border-slate-800 p-4 flex flex-col shadow-xl backdrop-blur-md">
            <div className="flex items-center justify-between pb-2 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <span className="relative flex h-2 w-2">
                  {isListening && (
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  )}
                  <span
                    className={`relative inline-flex rounded-full h-2 w-2 ${
                      isListening ? 'bg-emerald-500' : 'bg-slate-500'
                    }`}
                  />
                </span>
                <span className="text-xs font-bold uppercase tracking-wider text-slate-300">
                  {isListening ? 'Listening & Transcribing Voice Live…' : (avatarState === 'speaking' ? 'AI Examiner Speaking…' : 'AI Evaluating Answer…')}
                </span>
              </div>

              <div className="flex items-center gap-2 text-[11px] text-slate-400 font-mono">
                {isWhisperProcessing && (
                  <span className="text-brand-400 flex items-center gap-1 font-semibold">
                    <Cpu className="h-3 w-3 animate-spin" /> Whisper STT Refinement
                  </span>
                )}
                <span>{fullLiveText ? fullLiveText.split(/\s+/).filter(Boolean).length : 0} words</span>
                <span className="text-slate-600">&bull;</span>
                <span className="text-emerald-400 font-medium">Hands-Free</span>
              </div>
            </div>

            {/* Read-Only Transcript Display */}
            <div className="flex-1 overflow-y-auto py-2.5 text-xs sm:text-sm text-slate-200">
              {fullLiveText ? (
                <p className="leading-relaxed">
                  <span className="text-slate-100">{transcript}</span>
                  {interimTranscript && (
                    <span className="text-brand-300 italic opacity-85"> {interimTranscript}</span>
                  )}
                </p>
              ) : (
                <div className="h-full flex flex-col items-center justify-center text-slate-500 text-center gap-1.5">
                  <Mic className="h-5 w-5 text-slate-600 animate-pulse" />
                  <p className="text-xs">
                    {isListening
                      ? 'Speak your answer clearly. You can pause to think at any time without interruption.'
                      : 'The microphone will automatically start listening the moment the examiner finishes reading.'}
                  </p>
                </div>
              )}
            </div>

            {/* Hands-Free Live Status Bar (NO SUBMIT BUTTON REQUIRED) */}
            <div className="pt-2 border-t border-slate-800 flex items-center justify-between">
              {isSubmitting || isWhisperProcessing ? (
                <div className="flex items-center gap-2 text-xs text-brand-400">
                  <Spinner size="sm" />
                  <span>AI is evaluating your answer and generating the next question…</span>
                </div>
              ) : silenceCountdown !== null ? (
                <div className="flex items-center gap-2 text-xs text-amber-300 animate-pulse">
                  <Clock className="h-3.5 w-3.5" />
                  <span>
                    Answer complete pause detected &bull; Auto-submitting in <strong>{silenceCountdown}s</strong> (keep speaking to continue answering)...
                  </span>
                </div>
              ) : (
                <div className="flex items-center gap-2 text-[11px] text-slate-400">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                  <span>Fully hands-free: Speak your answer. The AI automatically senses when you finish.</span>
                </div>
              )}

              <span className="text-[10px] text-slate-500 uppercase tracking-widest font-mono">
                Hands-Free AI
              </span>
            </div>
          </div>
        </div>
      </main>

      {/* 4. Feedback & Hands-Free Auto-Advance Modal */}
      {lastFeedback && (
        <div className="fixed inset-0 z-40 flex items-center justify-center p-4 bg-black/85 backdrop-blur-md animate-fade-in">
          <div className="max-w-lg w-full bg-slate-900 border border-brand-500/40 rounded-2xl p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <div className="p-2 rounded-xl bg-brand-500/10 text-brand-400">
                  <Sparkles className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-slate-100">Answer Evaluated</h3>
                  <p className="text-xs text-slate-400">AI evaluation of your verbal response</p>
                </div>
              </div>
              <div className="px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 font-bold text-sm">
                Score: {Math.round((lastFeedback.response_saved?.score || 0) * 10)}/10
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 text-xs text-slate-300 leading-relaxed">
              <p className="font-semibold text-slate-200 mb-1">Feedback &amp; Observations:</p>
              <p>{lastFeedback.response_saved?.feedback || 'Good response. Proceeding to the next question.'}</p>
            </div>

            {/* Hands-Free Auto-Advance countdown indicator */}
            {autoAdvanceCountdown !== null && (
              <div className="rounded-xl bg-brand-500/10 border border-brand-500/20 p-2.5 flex items-center justify-between text-xs text-brand-300">
                <div className="flex items-center gap-2">
                  <Clock className="h-4 w-4 text-brand-400 animate-spin" />
                  <span>
                    {lastFeedback.interview_complete
                      ? `Completing examination automatically in ${autoAdvanceCountdown}s…`
                      : `Loading next question automatically in ${autoAdvanceCountdown}s…`}
                  </span>
                </div>
                <span className="font-mono font-bold text-brand-200">{autoAdvanceCountdown}s</span>
              </div>
            )}

            <div className="pt-2">
              <Button
                onClick={handleContinue}
                className="w-full bg-brand-600 hover:bg-brand-500 text-white font-semibold py-2.5"
                icon={<ChevronRight className="h-4 w-4" />}
              >
                {lastFeedback.interview_complete ? 'Complete Examination & View Summary' : 'Proceed Immediately'}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* 5. Bottom Examination Control Dock (No mute/off toggles) */}
      <footer className="h-16 px-6 bg-slate-900/95 border-t border-slate-800 flex items-center justify-between z-30">
        <div className="flex items-center gap-2 text-xs text-slate-400">
          <span className="font-bold text-slate-300">Exam In Progress</span> &bull;
          <span>Full Proctoring Active</span>
        </div>

        <div className="flex items-center gap-3">
          {/* Captions Toggle */}
          <button
            type="button"
            onClick={() => setShowCaptions((prev) => !prev)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 ${
              showCaptions
                ? 'bg-brand-600 text-white shadow-sm'
                : 'bg-slate-800 text-slate-400 border border-slate-700'
            }`}
            title="Toggle Question Text Subtitles"
          >
            <MessageSquare className="h-3.5 w-3.5" />
            <span>Subtitles</span>
          </button>

          {/* End Examination Button: immediately stops camera light & ends session */}
          <button
            type="button"
            onClick={handleLeaveInterview}
            disabled={isEnding}
            className="px-4 py-2 rounded-xl bg-red-600/90 hover:bg-red-500 text-white font-bold text-xs inline-flex items-center gap-1.5 shadow-lg shadow-red-500/20 transition-all ml-2"
            title="Leave & End Examination"
          >
            {isEnding ? <Spinner size="sm" /> : <PhoneOff className="h-3.5 w-3.5" />}
            <span>Leave Examination</span>
          </button>
        </div>

        <div className="hidden sm:flex items-center gap-2 text-xs text-slate-500">
          <span>Camera &amp; Audio: Locked Active</span>
        </div>
      </footer>
    </div>
  )
}

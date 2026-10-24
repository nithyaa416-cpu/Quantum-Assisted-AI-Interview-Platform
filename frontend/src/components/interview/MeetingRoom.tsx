/**
 * MeetingRoom — Authoritative Single Owner of the Interview Audio and Question Lifecycle.
 *
 * STATE MACHINE (per question):
 *   QUESTION_READY
 *   → AI_SPEAKING
 *   → STARTING_MICROPHONE
 *   → LISTENING_FOR_CANDIDATE
 *   → CANDIDATE_SPEAKING
 *   → FINALIZING_ANSWER
 *   → EVALUATING_ANSWER
 *   → (next question → QUESTION_READY)
 *
 * KEY GUARANTEES:
 * 1. Single Audio Owner: Only MeetingRoom initiates, pauses, or finalizes audio/speech.
 * 2. Autoplay Overlay: If browser blocks automatic TTS on cold load, a 1-click prompt
 *    instantly unlocks speech; subsequent questions play 100% automatically.
 * 3. AI Isolation: SpeechRecognition is strictly closed while AI is speaking; any transcript
 *    received during AI_SPEAKING is discarded.
 * 4. No Lost Words: Single persistent SpeechSynthesisUtterance prevents V8 garbage collection
 *    so utterance.onend 100% fires; interim transcripts are committed on rec.onend.
 * 5. Instant Mic Readiness: STARTING_MICROPHONE immediately permits speech capture so the
 *    very first word spoken by the candidate is captured and displayed.
 * 6. 10s Silence Detection: Arms only after candidate speaks >= 4 words; resets on new speech.
 */

import { useState, useEffect, useRef, useCallback } from 'react'
import {
  PhoneOff, Maximize2, Minimize2, MessageSquare,
  Sparkles, ChevronRight, Mic, Clock, Cpu, Volume2, Code2, Play,
} from 'lucide-react'
import toast from 'react-hot-toast'
import { ThemeToggle } from '@/components/ui/ThemeToggle'

import { MeetingAvatar, AvatarState } from './MeetingAvatar'
import { CandidateVideoTile } from './CandidateVideoTile'
import { ProctoringShield } from './ProctoringShield'
import { SessionTimer } from './InterviewTimer'
import { InterviewCodingPanel } from './InterviewCodingPanel'
import { Button } from '@/components/ui/Button'
import { Spinner } from '@/components/ui/Spinner'
import { stopAllMediaStreams, getActiveMediaStream } from '@/utils/mediaStreamManager'
import { interviewService } from '@/services/interviewService'
import type {
  InterviewSession,
  InterviewQuestion,
  SubmitResponseResult,
  InterviewCodingResult,
} from '@/types'

// ── Module-level Reference to prevent V8 Garbage Collection of Utterances ──────
let activeUtterance: SpeechSynthesisUtterance | null = null
let keepAliveTimer: ReturnType<typeof setInterval> | null = null

// ── Lifecycle State Machine ────────────────────────────────────────────────────
export type InterviewPhase =
  | 'QUESTION_READY'          // Question loaded; preparing TTS
  | 'AI_SPEAKING'             // TTS actively playing; microphone strictly OFF
  | 'STARTING_MICROPHONE'     // TTS confirmed ended; cold-start delay running
  | 'LISTENING_FOR_CANDIDATE' // Recognition running & listening; candidate has not yet spoken
  | 'CANDIDATE_SPEAKING'      // Candidate actively speaking; silence timer active
  | 'FINALIZING_ANSWER'       // Silence timeout reached; preparing submission
  | 'EVALUATING_ANSWER'       // Submitting answer to backend & waiting for evaluation

// ── Timing Constants ───────────────────────────────────────────────────────────
const ANSWER_SILENCE_TIMEOUT_MS = 10_000
const MIN_WORDS_TO_ARM_SILENCE = 4
const MIN_WORDS_TO_SUBMIT = 3
const RECOGNITION_COLD_START_MS = 300

const MAX_WEB_SPEECH_MS = (words: number) =>
  Math.min(50_000, Math.max(8_000, words * 600))

// ── Dev-Only Trace Logger ──────────────────────────────────────────────────────
function logInterviewEvent(event: string, details?: Record<string, any>) {
  if (typeof window !== 'undefined') {
    const time = new Date().toISOString().split('T')[1].slice(0, -1)
    console.log(
      `%c[QAIP-TRACE] ${time} %c${event}`,
      'color: #818cf8; font-weight: bold;',
      'color: #38bdf8; font-weight: bold;',
      details ?? ''
    )
  }
}

// ── Examiner Acoustic Echo Detector ──────────────────────────────────────────
function isQuestionEcho(spokenText: string, questionText?: string | null): boolean {
  if (!spokenText || !questionText) return false
  const spokenWords = spokenText
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, '')
    .split(/\s+/)
    .filter((w) => w.length > 2)
  if (spokenWords.length < 3) return false

  const questionWords = new Set(
    questionText
      .toLowerCase()
      .replace(/[^a-z0-9\s]/g, '')
      .split(/\s+/)
      .filter((w) => w.length > 2)
  )
  if (questionWords.size === 0) return false

  let matches = 0
  for (const word of spokenWords) {
    if (questionWords.has(word)) matches++
  }

  // If >60% of spoken words match the question, it is an echo of the examiner!
  return matches / spokenWords.length > 0.60
}

function splitIntoSentences(text: string): string[] {
  const clean = text.replace(/[*#`_~]/g, '').trim()
  if (!clean) return []
  const matched = clean.match(/[^.!?;\r\n]+[.!?;\r\n]*/g) || [clean]
  return matched.map((s) => s.trim()).filter((s) => s.length > 0)
}

// ── Component Props ────────────────────────────────────────────────────────────
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

// ── Main Component ─────────────────────────────────────────────────────────────
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
  // ── UI-only state ────────────────────────────────────────────────────────────
  const [showCaptions, setShowCaptions] = useState(true)
  const [isFullscreen, setIsFullscreen] = useState(Boolean(document.fullscreenElement))
  const [isMuted, setIsMuted] = useState(false)
  const [showAutoplayOverlay, setShowAutoplayOverlay] = useState(false)
  const isMutedRef = useRef(false)
  isMutedRef.current = isMuted

  // ── Coding phase state ───────────────────────────────────────────────────────
  const isCodingQuestion =
    (currentQuestion?.question_type === 'coding' && currentQuestion?.topic !== 'coding_introduction') ||
    (currentQuestion?.phase === 'coding' && (currentQuestion?.text === '[CODING_PROBLEM]' || currentQuestion?.topic !== 'coding_introduction'))

  const [codingSubmitted, setCodingSubmitted] = useState(false)
  const [codingFollowUpText, setCodingFollowUpText] = useState<string | null>(null)

  useEffect(() => {
    if (!isCodingQuestion) {
      setCodingSubmitted(false)
      setCodingFollowUpText(null)
    }
  }, [currentQuestion?.id]) // eslint-disable-line

  const handleCodingSubmitted = (result: InterviewCodingResult) => {
    setCodingSubmitted(true)
    setCodingFollowUpText(result.follow_up_question.text)
  }

  // ── Core State Machine ───────────────────────────────────────────────────────
  const [phase, setPhase] = useState<InterviewPhase>('QUESTION_READY')
  const phaseRef = useRef<InterviewPhase>('QUESTION_READY')

  const setPhaseSync = useCallback((p: InterviewPhase) => {
    phaseRef.current = p
    setPhase(p)
    logInterviewEvent(`PHASE_CHANGE → ${p}`, { questionId: currentQuestion?.id })
  }, [currentQuestion?.id])

  // ── Identity & Validation Refs ───────────────────────────────────────────────
  const currentQuestionIdRef = useRef<string | null>(currentQuestion?.id ?? null)
  currentQuestionIdRef.current = currentQuestion?.id ?? null

  const lastSpokenQuestionIdRef = useRef<string | null>(null)
  const ttsTokenRef = useRef(0)
  const recognitionGenerationRef = useRef(0)
  const speechEndFiredRef = useRef(false)
  const answerFinalizingRef = useRef(false)
  const isSubmittingRef = useRef(false)
  isSubmittingRef.current = isSubmitting || Boolean(lastFeedback)

  // ── Transcript state ─────────────────────────────────────────────────────────
  const [transcript, setTranscript] = useState('')
  const [interimTranscript, setInterimTranscript] = useState('')
  const [isListening, setIsListening] = useState(false)
  const [isWhisperProcessing, setIsWhisperProcessing] = useState(false)
  const [speechStartTime, setSpeechStartTime] = useState(Date.now())

  const fullTranscriptRef = useRef('')
  const interimTranscriptRef = useRef('')
  const shouldListenRef = useRef(false)

  // ── Timers ───────────────────────────────────────────────────────────────────
  const [silenceCountdown, setSilenceCountdown] = useState<number | null>(null)
  const [autoAdvanceCountdown, setAutoAdvanceCountdown] = useState<number | null>(null)
  const silenceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const silenceIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const autoAdvanceTimerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const coldStartTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const wsSafetyTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const autoplayCheckTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // ── TTS State & Refs ─────────────────────────────────────────────────────────
  const [avatarState, setAvatarState] = useState<AvatarState>('speaking')
  const webSpeechActiveRef = useRef(false)
  const webSpeechStartedRef = useRef(false)

  // ── Recognition & Recording Refs ─────────────────────────────────────────────
  const recognitionRef = useRef<any>(null)
  const mediaStreamRef = useRef<MediaStream | null>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])

  // ── Timer Clearers ───────────────────────────────────────────────────────────
  const clearSilenceTimers = useCallback(() => {
    if (silenceTimerRef.current) { clearTimeout(silenceTimerRef.current); silenceTimerRef.current = null }
    if (silenceIntervalRef.current) { clearInterval(silenceIntervalRef.current); silenceIntervalRef.current = null }
    setSilenceCountdown(null)
  }, [])

  const clearAutoAdvanceTimer = useCallback(() => {
    if (autoAdvanceTimerRef.current) { clearInterval(autoAdvanceTimerRef.current); autoAdvanceTimerRef.current = null }
    setAutoAdvanceCountdown(null)
  }, [])

  const clearAllTTSTimers = useCallback(() => {
    if (wsSafetyTimerRef.current) { clearTimeout(wsSafetyTimerRef.current); wsSafetyTimerRef.current = null }
    if (autoplayCheckTimerRef.current) { clearTimeout(autoplayCheckTimerRef.current); autoplayCheckTimerRef.current = null }
    if (keepAliveTimer) { clearInterval(keepAliveTimer); keepAliveTimer = null }
  }, [])

  /** Stop Web Speech immediately, incrementing ttsToken. */
  const stopTTS = useCallback(() => {
    ttsTokenRef.current += 1
    clearAllTTSTimers()
    webSpeechActiveRef.current = false
    webSpeechStartedRef.current = false
    activeUtterance = null

    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      try { window.speechSynthesis.cancel() } catch {}
    }
  }, [clearAllTTSTimers])

  // ── Unpause speech on any user interaction ──────────────────────────────────
  useEffect(() => {
    const handleGlobalInteraction = () => {
      if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
        if (window.speechSynthesis.speaking && window.speechSynthesis.paused) {
          window.speechSynthesis.resume()
        }
      }
    }
    window.addEventListener('click', handleGlobalInteraction)
    window.addEventListener('keydown', handleGlobalInteraction)
    return () => {
      window.removeEventListener('click', handleGlobalInteraction)
      window.removeEventListener('keydown', handleGlobalInteraction)
    }
  }, [])

  // ── Cleanup on unmount ────────────────────────────────────────────────────────
  useEffect(() => {
    logInterviewEvent('INTERVIEW_STARTED', { sessionId: session.id })
    return () => {
      shouldListenRef.current = false
      stopTTS()
      stopAllMediaStreams()
      clearSilenceTimers()
      clearAutoAdvanceTimer()
      if (coldStartTimerRef.current) clearTimeout(coldStartTimerRef.current)
      if (recognitionRef.current) {
        try {
          recognitionRef.current.onstart = null
          recognitionRef.current.onresult = null
          recognitionRef.current.onerror = null
          recognitionRef.current.onend = null
          recognitionRef.current.abort()
        } catch {}
      }
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
        try { mediaRecorderRef.current.stop() } catch {}
      }
    }
  }, [clearAutoAdvanceTimer, clearSilenceTimers, session.id, stopTTS])

  // ── Stop Recognition ──────────────────────────────────────────────────────────
  const stopListening = useCallback(() => {
    shouldListenRef.current = false
    setIsListening(false)
    if (recognitionRef.current) {
      try {
        recognitionRef.current.onstart = null
        recognitionRef.current.onresult = null
        recognitionRef.current.onerror = null
        recognitionRef.current.onend = null
        recognitionRef.current.abort()
      } catch {}
      recognitionRef.current = null
    }
  }, [])

  // ── Audio Recording (Whisper) ─────────────────────────────────────────────────
  const startAudioRecording = useCallback(() => {
    if (!mediaStreamRef.current) {
      const active = getActiveMediaStream()
      if (active) mediaStreamRef.current = active
    }
    if (!mediaStreamRef.current) return
    if (mediaRecorderRef.current?.state === 'recording') return

    try {
      audioChunksRef.current = []
      const mimeTypes = ['audio/webm;codecs=opus', 'audio/webm', 'audio/ogg;codecs=opus', 'audio/mp4']
      const supportedMime = mimeTypes.find((t) => MediaRecorder.isTypeSupported(t)) ?? ''
      const recorder = supportedMime
        ? new MediaRecorder(mediaStreamRef.current, { mimeType: supportedMime })
        : new MediaRecorder(mediaStreamRef.current)
      recorder.ondataavailable = (e) => {
        if (e.data?.size > 0) audioChunksRef.current.push(e.data)
      }
      recorder.start(250)
      mediaRecorderRef.current = recorder
    } catch (e) {
      console.warn('[Interview] MediaRecorder start failed:', e)
    }
  }, [])

  const stopAudioRecording = useCallback((): Promise<Blob | null> => {
    return new Promise((resolve) => {
      if (!mediaRecorderRef.current || mediaRecorderRef.current.state === 'inactive') {
        resolve(audioChunksRef.current.length > 0
          ? new Blob(audioChunksRef.current, { type: 'audio/webm' })
          : null)
        return
      }
      mediaRecorderRef.current.onstop = () =>
        resolve(new Blob(audioChunksRef.current, { type: 'audio/webm' }))
      try { mediaRecorderRef.current.stop() } catch { resolve(null) }
    })
  }, [])

  // ── Forward declaration refs ─────────────────────────────────────────────────
  const handleSubmitRef = useRef<() => Promise<void>>(async () => {})

  // ── Silence Detection ─────────────────────────────────────────────────────────
  const resetSilenceDetection = useCallback(
    (currentText: string) => {
      clearSilenceTimers()
      const words = currentText.trim().split(/\s+/).filter(Boolean)
      if (words.length < MIN_WORDS_TO_ARM_SILENCE) return

      let remaining = ANSWER_SILENCE_TIMEOUT_MS / 1000
      setSilenceCountdown(remaining)

      silenceIntervalRef.current = setInterval(() => {
        remaining -= 1
        if (remaining <= 0) {
          clearSilenceTimers()
        } else {
          setSilenceCountdown(remaining)
        }
      }, 1000)

      silenceTimerRef.current = setTimeout(() => {
        setSilenceCountdown(null)
        if (
          (phaseRef.current === 'LISTENING_FOR_CANDIDATE' || phaseRef.current === 'CANDIDATE_SPEAKING') &&
          !isSubmittingRef.current &&
          !answerFinalizingRef.current
        ) {
          logInterviewEvent('ANSWER_FINALIZED', { reason: 'silence_timeout' })
          handleSubmitRef.current()
        }
      }, ANSWER_SILENCE_TIMEOUT_MS)
    },
    [clearSilenceTimers]
  )

  // ── Start Recognition ─────────────────────────────────────────────────────────
  const startListening = useCallback(
    (questionId: string) => {
      recognitionGenerationRef.current += 1
      const myGen = recognitionGenerationRef.current

      shouldListenRef.current = true
      setIsListening(true)
      setAvatarState('listening')
      setPhaseSync('LISTENING_FOR_CANDIDATE')

      startAudioRecording()

      const SR: any =
        (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
      if (!SR) {
        console.warn('[Interview] SpeechRecognition not available in this browser')
        toast.error('Voice recognition requires Google Chrome or Microsoft Edge.', { duration: 6000 })
        return
      }

      try {
        if (recognitionRef.current) {
          try {
            recognitionRef.current.onstart = null
            recognitionRef.current.onresult = null
            recognitionRef.current.onerror = null
            recognitionRef.current.onend = null
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
          if (myGen !== recognitionGenerationRef.current) return
          if (questionId !== currentQuestionIdRef.current) return
          logInterviewEvent('RECOGNITION_STARTED', { questionId, generation: myGen })
          setIsListening(true)
        }

        rec.onaudiostart = () => {
          if (myGen !== recognitionGenerationRef.current) return
          logInterviewEvent('RECOGNITION_AUDIO_START', { questionId })
        }

        rec.onspeechstart = () => {
          if (myGen !== recognitionGenerationRef.current) return
          logInterviewEvent('CANDIDATE_SPEECH_DETECTED', { questionId })
          if (phaseRef.current !== 'CANDIDATE_SPEAKING') {
            setPhaseSync('CANDIDATE_SPEAKING')
            setSpeechStartTime(Date.now())
          }
        }

        rec.onresult = (event: any) => {
          const matchesQuestion = (questionId === currentQuestionIdRef.current)
          const matchesGen = (myGen === recognitionGenerationRef.current)
          const lifecycleAllows = (
            phaseRef.current === 'STARTING_MICROPHONE' ||
            phaseRef.current === 'LISTENING_FOR_CANDIDATE' ||
            phaseRef.current === 'CANDIDATE_SPEAKING'
          )
          const notFinalized = !answerFinalizingRef.current

          if (!matchesQuestion || !matchesGen || !lifecycleAllows || !notFinalized) {
            logInterviewEvent('TRANSCRIPT_REJECTED', {
              reason: !matchesQuestion ? 'question_mismatch' :
                      !matchesGen ? 'generation_mismatch' :
                      !lifecycleAllows ? `lifecycle_${phaseRef.current}` :
                      'answer_finalized',
              phase: phaseRef.current,
            })
            return
          }

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

          // Anti-Echo Guard: Discard speech that echoes the question
          if (currentQuestion?.text) {
            if (finalChunk && isQuestionEcho(finalChunk, currentQuestion.text)) {
              logInterviewEvent('TRANSCRIPT_REJECTED_ECHO', { chunk: finalChunk })
              return
            }
            if (interimChunk && isQuestionEcho(interimChunk, currentQuestion.text)) {
              logInterviewEvent('TRANSCRIPT_REJECTED_ECHO', { chunk: interimChunk })
              return
            }
          }

          if (finalChunk) {
            const prev = fullTranscriptRef.current ? fullTranscriptRef.current.trim() + ' ' : ''
            fullTranscriptRef.current = (prev + finalChunk.trim()).trim()
            setTranscript(fullTranscriptRef.current)
          }

          interimTranscriptRef.current = interimChunk
          setInterimTranscript(interimChunk)

          if (fullTranscriptRef.current || interimChunk) {
            if (phaseRef.current !== 'CANDIDATE_SPEAKING') {
              setPhaseSync('CANDIDATE_SPEAKING')
              setSpeechStartTime(Date.now())
            }
          }

          const totalText = (fullTranscriptRef.current + ' ' + interimChunk).trim()
          logInterviewEvent('TRANSCRIPT_ACCEPTED', {
            text: totalText.slice(-60),
            words: totalText.split(/\s+/).filter(Boolean).length,
          })
          resetSilenceDetection(totalText)
        }

        rec.onerror = (e: any) => {
          logInterviewEvent('RECOGNITION_ERROR', { error: e.error, generation: myGen })
          if (e.error === 'not-allowed') {
            shouldListenRef.current = false
            setIsListening(false)
            toast.error('Microphone access blocked. Please allow microphone permission in your browser.', { duration: 8000 })
            return
          }
          if (e.error !== 'no-speech') {
            console.warn('[Interview] SpeechRecognition error:', e.error)
          }
        }

        rec.onend = () => {
          logInterviewEvent('RECOGNITION_END', { generation: myGen, shouldListen: shouldListenRef.current, phase: phaseRef.current })

          // Preserve uncommitted interim speech before restart
          if (interimTranscriptRef.current) {
            const prev = fullTranscriptRef.current ? fullTranscriptRef.current.trim() + ' ' : ''
            fullTranscriptRef.current = (prev + interimTranscriptRef.current.trim()).trim()
            setTranscript(fullTranscriptRef.current)
            interimTranscriptRef.current = ''
            setInterimTranscript('')
          }

          // Controlled auto-restart policy
          if (
            shouldListenRef.current &&
            (phaseRef.current === 'LISTENING_FOR_CANDIDATE' || phaseRef.current === 'CANDIDATE_SPEAKING' || phaseRef.current === 'STARTING_MICROPHONE') &&
            !isSubmittingRef.current &&
            !answerFinalizingRef.current &&
            questionId === currentQuestionIdRef.current
          ) {
            setTimeout(() => {
              if (
                shouldListenRef.current &&
                (phaseRef.current === 'LISTENING_FOR_CANDIDATE' || phaseRef.current === 'CANDIDATE_SPEAKING' || phaseRef.current === 'STARTING_MICROPHONE') &&
                !isSubmittingRef.current &&
                !answerFinalizingRef.current &&
                questionId === currentQuestionIdRef.current
              ) {
                startListening(questionId)
              }
            }, 100)
          }
        }

        rec.start()
        recognitionRef.current = rec
      } catch (e: any) {
        console.warn('[Interview] Failed to start SpeechRecognition:', e)
        setIsListening(false)
      }
    },
    [resetSilenceDetection, setPhaseSync, startAudioRecording]
  )

  // ── onSpeechComplete ──────────────────────────────────────────────────────────
  const onSpeechComplete = useCallback(
    (token: number, questionId: string) => {
      if (token !== ttsTokenRef.current) return
      if (questionId !== currentQuestionIdRef.current) return
      if (speechEndFiredRef.current) return
      speechEndFiredRef.current = true

      clearAllTTSTimers()
      webSpeechActiveRef.current = false
      setShowAutoplayOverlay(false)

      logInterviewEvent('TTS_END', { questionId })

      // Clear temporary transcript for the new question
      fullTranscriptRef.current = ''
      interimTranscriptRef.current = ''
      setTranscript('')
      setInterimTranscript('')

      // Transition to STARTING_MICROPHONE
      setPhaseSync('STARTING_MICROPHONE')
      setAvatarState('listening')
      logInterviewEvent('RECOGNITION_START_REQUESTED', { questionId })

      // Cold start delay to ensure speaker acoustic decay
      if (coldStartTimerRef.current) clearTimeout(coldStartTimerRef.current)
      coldStartTimerRef.current = setTimeout(() => {
        if (
          (phaseRef.current === 'STARTING_MICROPHONE' || phaseRef.current === 'QUESTION_READY') &&
          questionId === currentQuestionIdRef.current
        ) {
          startListening(questionId)
        }
      }, RECOGNITION_COLD_START_MS)
    },
    [clearAllTTSTimers, setPhaseSync, startListening]
  )

  // ── Primary speakQuestion Entry Point (Web Speech with Keep-Alive) ───────────
  const speakQuestion = useCallback(
    (text: string, questionId: string, token: number) => {
      if (!text) {
        onSpeechComplete(token, questionId)
        return
      }
      if (isMutedRef.current) {
        logInterviewEvent('TTS_MUTED_SKIPPED', { questionId })
        onSpeechComplete(token, questionId)
        return
      }

      if (typeof window === 'undefined' || !('speechSynthesis' in window)) {
        console.warn('[Interview] speechSynthesis not available in window')
        onSpeechComplete(token, questionId)
        return
      }

      const cleanText = text
        .replace(/\[CODING_PROBLEM\]/g, 'Here is your coding challenge. Please review the problem and write your solution in the code editor.')
        .replace(/[*#`_~]/g, '')
        .trim()

      if (!cleanText) {
        onSpeechComplete(token, questionId)
        return
      }

      logInterviewEvent('TTS_START', { questionId, token, length: cleanText.length })
      setPhaseSync('AI_SPEAKING')
      setAvatarState('speaking')
      webSpeechActiveRef.current = true
      webSpeechStartedRef.current = false
      setShowAutoplayOverlay(false)

      try {
        window.speechSynthesis.cancel()

        const sentences = splitIntoSentences(cleanText)
        if (sentences.length === 0) {
          onSpeechComplete(token, questionId)
          return
        }

        const voices = window.speechSynthesis.getVoices()
        const preferredVoice = voices.find(
          (v) =>
            (v.name.includes('Google') ||
              v.name.includes('Natural') ||
              v.name.includes('Samantha') ||
              v.name.includes('Zira') ||
              v.lang.startsWith('en')) &&
            !v.name.includes('David')
        )

        let sentenceIdx = 0

        const playSentence = (idx: number) => {
          if (token !== ttsTokenRef.current) return
          if (questionId !== currentQuestionIdRef.current) return

          if (idx >= sentences.length) {
            webSpeechActiveRef.current = false
            clearAllTTSTimers()
            logInterviewEvent('TTS_COMPLETED_SUCCESSFULLY', { questionId })
            onSpeechComplete(token, questionId)
            return
          }

          const utterance = new SpeechSynthesisUtterance(sentences[idx])
          activeUtterance = utterance
          utterance.rate = 1.0
          utterance.pitch = 1.0
          if (preferredVoice) utterance.voice = preferredVoice

          utterance.onstart = () => {
            if (token !== ttsTokenRef.current) return
            webSpeechStartedRef.current = true
            setShowAutoplayOverlay(false)
            logInterviewEvent('TTS_SPEAKING_SENTENCE', { idx: idx + 1, total: sentences.length })
          }

          utterance.onend = () => {
            if (token !== ttsTokenRef.current) return
            playSentence(idx + 1)
          }

          utterance.onerror = (e) => {
            if (token !== ttsTokenRef.current) return
            logInterviewEvent('TTS_ERROR', { error: e.error, idx })
            if (e.error === 'canceled' || e.error === 'interrupted') return
            if (e.error === 'not-allowed') {
              logInterviewEvent('TTS_AUTOPLAY_NOT_ALLOWED', { questionId })
              setShowAutoplayOverlay(true)
              return
            }
            if (idx + 1 < sentences.length) {
              playSentence(idx + 1)
            } else {
              webSpeechActiveRef.current = false
              clearAllTTSTimers()
              onSpeechComplete(token, questionId)
            }
          }

          window.speechSynthesis.speak(utterance)
          window.speechSynthesis.resume()
        }

        playSentence(0)

        autoplayCheckTimerRef.current = setTimeout(() => {
          if (token !== ttsTokenRef.current) return
          if (phaseRef.current === 'AI_SPEAKING' && !webSpeechStartedRef.current) {
            logInterviewEvent('TTS_AUTOPLAY_PENDING_CLICK', { questionId })
            setShowAutoplayOverlay(true)
          }
        }, 1000)

        const safetyMs = MAX_WEB_SPEECH_MS(cleanText.split(/\s+/).length)
        wsSafetyTimerRef.current = setTimeout(() => {
          if (token !== ttsTokenRef.current) return
          if (webSpeechActiveRef.current) {
            console.warn('[Interview] Web Speech safety timer fired — completing speech')
            try { window.speechSynthesis.cancel() } catch {}
            webSpeechActiveRef.current = false
            onSpeechComplete(token, questionId)
          }
        }, safetyMs)
      } catch (err) {
        console.warn('[Interview] speakQuestion threw:', err)
        webSpeechActiveRef.current = false
        onSpeechComplete(token, questionId)
      }
    },
    [clearAllTTSTimers, onSpeechComplete, setPhaseSync]
  )

  // ── Question Change Effect ────────────────────────────────────────────────────
  useEffect(() => {
    if (!currentQuestion?.id || !currentQuestion?.text) return

    // Prevent duplicate fire on re-renders
    if (lastSpokenQuestionIdRef.current === currentQuestion.id) return
    lastSpokenQuestionIdRef.current = currentQuestion.id
    currentQuestionIdRef.current = currentQuestion.id

    logInterviewEvent('QUESTION_LOADED', {
      id: currentQuestion.id,
      phase: currentQuestion.phase,
      turn: currentQuestion.turn_number,
      text: currentQuestion.text.slice(0, 60),
    })

    // Stop everything from previous question
    shouldListenRef.current = false
    stopListening()
    if (coldStartTimerRef.current) {
      clearTimeout(coldStartTimerRef.current)
      coldStartTimerRef.current = null
    }
    clearSilenceTimers()
    clearAutoAdvanceTimer()
    stopTTS()

    // Reset per-question state
    answerFinalizingRef.current = false
    speechEndFiredRef.current = false
    fullTranscriptRef.current = ''
    interimTranscriptRef.current = ''
    setTranscript('')
    setInterimTranscript('')
    setIsListening(false)

    setPhaseSync('QUESTION_READY')

    const token = ttsTokenRef.current
    speakQuestion(currentQuestion.text, currentQuestion.id, token)
  }, [
    clearAutoAdvanceTimer,
    clearSilenceTimers,
    currentQuestion?.id,
    currentQuestion?.phase,
    currentQuestion?.text,
    currentQuestion?.turn_number,
    setPhaseSync,
    speakQuestion,
    stopListening,
    stopTTS,
  ])

  // ── Manual Replay ─────────────────────────────────────────────────────────────
  const handleReplayRequest = useCallback(() => {
    if (!currentQuestion?.text) return
    if (phaseRef.current === 'FINALIZING_ANSWER' || phaseRef.current === 'EVALUATING_ANSWER') return

    logInterviewEvent('REPLAY_REQUESTED', { questionId: currentQuestion.id })

    shouldListenRef.current = false
    stopListening()
    if (coldStartTimerRef.current) {
      clearTimeout(coldStartTimerRef.current)
      coldStartTimerRef.current = null
    }
    clearSilenceTimers()
    stopTTS()

    speechEndFiredRef.current = false
    fullTranscriptRef.current = ''
    interimTranscriptRef.current = ''
    setTranscript('')
    setInterimTranscript('')
    setIsListening(false)

    setPhaseSync('QUESTION_READY')

    const token = ttsTokenRef.current
    speakQuestion(currentQuestion.text, currentQuestion.id, token)
  }, [clearSilenceTimers, currentQuestion?.id, currentQuestion?.text, setPhaseSync, speakQuestion, stopListening, stopTTS])

  // ── One-click Autoplay Unmute Action ──────────────────────────────────────────
  const handleUserUnmuteAndStart = useCallback(() => {
    setShowAutoplayOverlay(false)
    shouldListenRef.current = false
    stopListening()
    if (coldStartTimerRef.current) {
      clearTimeout(coldStartTimerRef.current)
      coldStartTimerRef.current = null
    }
    clearSilenceTimers()
    stopTTS()

    speechEndFiredRef.current = false
    fullTranscriptRef.current = ''
    interimTranscriptRef.current = ''
    setTranscript('')
    setInterimTranscript('')
    setIsListening(false)

    setPhaseSync('QUESTION_READY')

    if (currentQuestion?.text && currentQuestion?.id) {
      const token = ttsTokenRef.current
      speakQuestion(currentQuestion.text, currentQuestion.id, token)
    }
  }, [clearSilenceTimers, currentQuestion?.id, currentQuestion?.text, setPhaseSync, speakQuestion, stopListening, stopTTS])

  // ── Mute Toggle ───────────────────────────────────────────────────────────────
  const handleToggleMute = useCallback(() => {
    setIsMuted((prev) => {
      const next = !prev
      isMutedRef.current = next
      if (next) {
        if (phaseRef.current === 'AI_SPEAKING' || phaseRef.current === 'QUESTION_READY') {
          stopTTS()
          const token = ttsTokenRef.current
          if (currentQuestion?.id) {
            onSpeechComplete(token, currentQuestion.id)
          }
        }
      }
      return next
    })
  }, [currentQuestion?.id, onSpeechComplete, stopTTS])

  // ── Answer Submission ─────────────────────────────────────────────────────────
  const handleSubmit = useCallback(async () => {
    if (answerFinalizingRef.current) return
    answerFinalizingRef.current = true

    clearSilenceTimers()
    shouldListenRef.current = false
    stopListening()

    setPhaseSync('FINALIZING_ANSWER')
    setAvatarState('thinking')

    const rawSpoken = (fullTranscriptRef.current + ' ' + (interimTranscriptRef.current || interimTranscript)).trim()
    let wordList = rawSpoken.split(/\s+/).filter(Boolean)
    let finalAnswerText = rawSpoken

    // Whisper recovery fallback if Web Speech missed words or microphone had silence
    setIsWhisperProcessing(true)
    try {
      const audioBlob = await stopAudioRecording()
      if (audioBlob && audioBlob.size > 2000) {
        const whisperText = await interviewService.transcribeAudio(audioBlob, session.id)
        if (whisperText && whisperText.trim()) {
          const whisperWords = whisperText.trim().split(/\s+/).filter(Boolean)
          if (whisperWords.length >= MIN_WORDS_TO_SUBMIT && (!currentQuestion?.text || !isQuestionEcho(whisperText, currentQuestion.text))) {
            finalAnswerText = whisperText.trim()
            wordList = whisperWords
            fullTranscriptRef.current = finalAnswerText
            setTranscript(finalAnswerText)
            setInterimTranscript('')
          }
        }
      }
    } catch (err) {
      console.warn('[Interview] Whisper recovery skipped:', err)
    } finally {
      setIsWhisperProcessing(false)
    }

    logInterviewEvent('ANSWER_FINALIZED', {
      rawWords: wordList.length,
      sample: finalAnswerText.slice(0, 60),
    })

    // Secondary Echo check on finalAnswerText before submitting
    if (currentQuestion?.text && isQuestionEcho(finalAnswerText, currentQuestion.text)) {
      logInterviewEvent('SUBMISSION_REJECTED_ECHO', { answer: finalAnswerText.slice(0, 60) })
      toast.error('Examiner echo detected. Please answer the question in your own words.', { duration: 4500 })
      answerFinalizingRef.current = false
      fullTranscriptRef.current = ''
      interimTranscriptRef.current = ''
      setTranscript('')
      setInterimTranscript('')
      setPhaseSync('LISTENING_FOR_CANDIDATE')
      setAvatarState('listening')
      setTimeout(() => {
        if (currentQuestion?.id) startListening(currentQuestion.id)
      }, 300)
      return
    }

    if (wordList.length < MIN_WORDS_TO_SUBMIT) {
      logInterviewEvent('ANSWER_TOO_SHORT_RESUMING', { wordCount: wordList.length })
      toast('Please speak your answer clearly into the microphone.', { icon: '🎙️', duration: 4000 })
      answerFinalizingRef.current = false
      setPhaseSync('LISTENING_FOR_CANDIDATE')
      setAvatarState('listening')
      setTimeout(() => {
        if (
          (phaseRef.current === 'LISTENING_FOR_CANDIDATE' || phaseRef.current === 'CANDIDATE_SPEAKING') &&
          !isSubmittingRef.current &&
          currentQuestion?.id
        ) {
          startListening(currentQuestion.id)
        }
      }, 300)
      return
    }

    setPhaseSync('EVALUATING_ANSWER')
    const durationSeconds = Math.max(5, Math.round((Date.now() - speechStartTime) / 1000))
    logInterviewEvent('SUBMITTING_ANSWER', { durationSeconds, answerLength: finalAnswerText.length })
    await onSubmitAnswer(finalAnswerText, durationSeconds)
    logInterviewEvent('EVALUATION_COMPLETED', { questionId: currentQuestion?.id })
  }, [
    clearSilenceTimers,
    currentQuestion?.id,
    interimTranscript,
    onSubmitAnswer,
    setPhaseSync,
    speechStartTime,
    startListening,
    stopAudioRecording,
    stopListening,
  ])
  handleSubmitRef.current = handleSubmit

  // ── Auto-advance After Evaluation Feedback ────────────────────────────────────
  useEffect(() => {
    if (lastFeedback) {
      shouldListenRef.current = false
      clearSilenceTimers()
      stopListening()

      setAutoAdvanceCountdown(3)
      let secondsLeft = 3
      autoAdvanceTimerRef.current = setInterval(() => {
        secondsLeft -= 1
        if (secondsLeft <= 0) {
          clearAutoAdvanceTimer()
          handleContinueRef.current()
        } else {
          setAutoAdvanceCountdown(secondsLeft)
        }
      }, 1000)
    } else {
      clearAutoAdvanceTimer()
    }
    return () => { clearAutoAdvanceTimer() }
  }, [clearAutoAdvanceTimer, clearSilenceTimers, lastFeedback, stopListening])

  const handleContinue = useCallback(async () => {
    clearAutoAdvanceTimer()
    await onContinueNext()
  }, [clearAutoAdvanceTimer, onContinueNext])

  const handleContinueRef = useRef(handleContinue)
  handleContinueRef.current = handleContinue

  // ── Fullscreen & Exit Handlers ────────────────────────────────────────────────
  const toggleFullscreen = async () => {
    if (!document.fullscreenElement) {
      try { await document.documentElement.requestFullscreen(); setIsFullscreen(true) } catch {}
    } else {
      try { await document.exitFullscreen(); setIsFullscreen(false) } catch {}
    }
  }

  const handleLeaveInterview = async () => {
    shouldListenRef.current = false
    stopTTS()
    stopAllMediaStreams()
    clearSilenceTimers()
    clearAutoAdvanceTimer()
    stopListening()
    await onEndInterview()
  }

  // ── Derived Display Values ────────────────────────────────────────────────────
  const fullLiveText = (transcript + (interimTranscript ? ' ' + interimTranscript : '')).trim()
  const qText = isCodingQuestion && codingSubmitted
    ? codingFollowUpText ?? 'Please explain your approach and the time/space complexity.'
    : currentQuestion?.text ?? ''

  const avatarDisplayState: AvatarState =
    phase === 'QUESTION_READY' || phase === 'AI_SPEAKING'
      ? 'speaking'
      : phase === 'STARTING_MICROPHONE' || phase === 'LISTENING_FOR_CANDIDATE' || phase === 'CANDIDATE_SPEAKING'
      ? 'listening'
      : phase === 'FINALIZING_ANSWER' || phase === 'EVALUATING_ANSWER'
      ? 'thinking'
      : 'idle'

  // ── Render ────────────────────────────────────────────────────────────────────
  return (
    <div className="relative w-screen h-screen bg-slate-950 text-slate-100 flex flex-col overflow-hidden select-none">
      <ProctoringShield
        onViolation={(count, reason) =>
          toast.error(`Proctoring Strike ${count}: ${reason}`, { duration: 4000 })
        }
      />

      {/* Header */}
      <header className="h-14 px-6 flex items-center justify-between border-b border-slate-800 bg-slate-900/80 backdrop-blur-md z-30">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-brand-600 to-indigo-500 flex items-center justify-center font-bold text-white text-sm shadow-md">
            Q
          </div>
          <h2 className="text-sm font-bold text-slate-100 flex items-center gap-2">
            Proctored AI Examination
            <span className="text-[11px] font-medium px-2 py-0.5 rounded-full bg-brand-500/20 text-brand-300 border border-brand-500/30">
              {session.target_role || 'Software Engineering'}
            </span>
          </h2>
        </div>

        <div className="flex items-center gap-4">
          <ThemeToggle />
          <div className="hidden sm:flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-800 border border-slate-700 text-xs text-slate-300">
            <span className="w-2 h-2 rounded-full bg-brand-400" />
            <span className="capitalize">{currentQuestion?.phase || session.current_phase} Phase</span>
            <span className="text-slate-500">&bull; Question {session.turn_count || 1}</span>
          </div>
          <SessionTimer startedAt={session.started_at} isActive={true} durationSeconds={session.duration_seconds} />
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

      {/* Main Examination Stage */}
      <main className="flex-1 p-4 sm:p-6 flex flex-col gap-4 min-h-0 relative z-20 overflow-hidden">

        {/* Coding phase: Editor */}
        {isCodingQuestion && !codingSubmitted && (
          <div className="flex-1 min-h-0 overflow-hidden">
            <InterviewCodingPanel
              sessionId={session.id}
              questionId={currentQuestion!.id}
              onSubmitted={handleCodingSubmitted}
              onSkip={onContinueNext}
            />
          </div>
        )}

        {/* Coding phase: Verbal follow-up explanation */}
        {isCodingQuestion && codingSubmitted && (
          <div className="flex flex-col lg:flex-row gap-4 flex-1 min-h-0">
            <div className="flex-1 min-h-[300px]">
              <div className="h-full flex flex-col rounded-2xl bg-slate-900/90 border border-orange-500/30 p-5 shadow-xl">
                <div className="flex items-center gap-2 mb-3">
                  <Code2 className="h-4 w-4 text-orange-400" />
                  <span className="text-xs font-bold uppercase tracking-wider text-orange-400">
                    Coding Explanation
                  </span>
                </div>
                <p className="text-sm text-slate-200 leading-relaxed flex-1">
                  {codingFollowUpText || 'Please explain your approach and the time/space complexity of your solution.'}
                </p>
                <p className="text-xs text-slate-500 mt-4">Answer verbally — the microphone is listening.</p>
              </div>
            </div>
            <div className="w-full lg:w-[360px] flex flex-col gap-4 flex-shrink-0">
              <div className="flex-1 min-h-[180px]">
                <CandidateVideoTile
                  candidateName={candidateName}
                  onStreamReady={(stream) => { mediaStreamRef.current = stream }}
                />
              </div>
              <div className="h-44 rounded-2xl bg-slate-900/90 border border-slate-800 p-3 flex flex-col">
                <div className="flex items-center gap-2 pb-2 border-b border-slate-800">
                  <span className={`w-2 h-2 rounded-full ${isListening ? 'bg-emerald-500 animate-pulse' : 'bg-slate-600'}`} />
                  <span className="text-xs text-slate-400">{isListening ? 'Listening…' : 'Speak your explanation'}</span>
                </div>
                <div className="flex-1 overflow-y-auto py-2 text-xs text-slate-200">
                  {fullLiveText ? (
                    <p className="leading-relaxed">
                      <span>{transcript}</span>
                      {interimTranscript && <span className="text-brand-300 italic"> {interimTranscript}</span>}
                    </p>
                  ) : (
                    <p className="text-slate-500 text-center mt-4">Explain your solution verbally…</p>
                  )}
                </div>
                {(isSubmitting || isWhisperProcessing) && (
                  <div className="pt-2 border-t border-slate-800 flex items-center gap-2 text-xs text-brand-400">
                    <Spinner size="sm" />
                    <span>Evaluating explanation…</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Standard Verbal Phase */}
        {!isCodingQuestion && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6 flex-1 min-h-0">
            {/* Left: AI Avatar */}
            <div className="w-full h-full min-h-[300px] relative">
              <MeetingAvatar
                avatarState={avatarDisplayState}
                questionText={qText}
                isMuted={isMuted}
                onToggleMute={handleToggleMute}
                onReplayRequest={handleReplayRequest}
                showCaptions={showCaptions}
              />

              {/* 1-Click Autoplay Unlock Prompt (Displays ONLY if browser temporarily holds audio) */}
              {showAutoplayOverlay && (
                <button
                  type="button"
                  onClick={handleUserUnmuteAndStart}
                  className="absolute inset-0 z-30 flex flex-col items-center justify-center bg-black/75 backdrop-blur-md rounded-2xl gap-3 cursor-pointer group hover:bg-black/85 transition-all p-6 text-center"
                >
                  <div className="w-16 h-16 rounded-full bg-brand-600 flex items-center justify-center text-white shadow-2xl group-hover:scale-110 transition-transform ring-4 ring-brand-400/30 animate-pulse">
                    <Play className="h-8 w-8 ml-1" />
                  </div>
                  <div>
                    <span className="inline-block text-sm font-bold text-white px-4 py-1.5 rounded-full bg-brand-600 border border-brand-400 shadow-md">
                      Click to Hear Examiner Question
                    </span>
                    <p className="text-xs text-slate-300 mt-2">
                      Tap anywhere to start examiner voice &amp; connect microphone
                    </p>
                  </div>
                </button>
              )}
            </div>

            {/* Right: Candidate Video + Live Transcript */}
            <div className="w-full h-full flex flex-col gap-4 min-h-[300px]">
              <div className="flex-1 min-h-[220px]">
                <CandidateVideoTile
                  candidateName={candidateName}
                  onStreamReady={(stream) => { mediaStreamRef.current = stream }}
                />
              </div>

              {/* Live Transcript Container */}
              <div className="h-52 rounded-2xl bg-slate-900/90 border border-slate-800 p-4 flex flex-col shadow-xl backdrop-blur-md">
                <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                  <div className="flex items-center gap-2">
                    <span className="relative flex h-2 w-2">
                      {isListening && (
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                      )}
                      <span className={`relative inline-flex rounded-full h-2 w-2 ${isListening ? 'bg-emerald-500' : 'bg-slate-500'}`} />
                    </span>
                    <span className="text-xs font-bold uppercase tracking-wider text-slate-300">
                      {phase === 'QUESTION_READY' || phase === 'AI_SPEAKING'
                        ? 'AI Examiner Speaking — Please Wait…'
                        : phase === 'STARTING_MICROPHONE'
                        ? 'Connecting Microphone…'
                        : isListening
                        ? (currentQuestion?.phase === 'closing' ? 'Listening to Your Question for Alex…' : 'Listening & Transcribing Voice Live…')
                        : phase === 'FINALIZING_ANSWER' || phase === 'EVALUATING_ANSWER'
                        ? 'AI Evaluating Answer…'
                        : 'Microphone Ready'}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-[11px] text-slate-400 font-mono">
                    {isWhisperProcessing && (
                      <span className="text-brand-400 flex items-center gap-1 font-semibold">
                        <Cpu className="h-3 w-3 animate-spin" /> Whisper STT
                      </span>
                    )}
                    <span>{fullLiveText ? fullLiveText.split(/\s+/).filter(Boolean).length : 0} words</span>
                    <span className="text-slate-600">&bull;</span>
                    <span className="text-emerald-400 font-medium">Hands-Free</span>
                  </div>
                </div>

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
                        {phase === 'QUESTION_READY' || phase === 'AI_SPEAKING'
                          ? 'Please wait while the examiner finishes speaking before you answer.'
                          : phase === 'STARTING_MICROPHONE'
                          ? 'Microphone is activating…'
                          : isListening
                          ? (currentQuestion?.phase === 'closing'
                              ? 'Ask any question about the role, team, or company. Alex will answer verbally.'
                              : 'Speak your answer clearly. A 10-second pause will auto-submit.')
                          : 'Microphone will activate once the examiner finishes reading the question.'}
                      </p>
                    </div>
                  )}
                </div>

                <div className="pt-2 border-t border-slate-800 flex items-center justify-between">
                  {isSubmitting || isWhisperProcessing ? (
                    <div className="flex items-center gap-2 text-xs text-brand-400">
                      <Spinner size="sm" />
                      <span>AI is evaluating your answer…</span>
                    </div>
                  ) : silenceCountdown !== null ? (
                    <div className="flex items-center gap-2 text-xs text-amber-300 animate-pulse">
                      <Clock className="h-3.5 w-3.5" />
                      <span>
                        Pause detected — auto-submitting in <strong>{silenceCountdown}s</strong>. Keep speaking to continue.
                      </span>
                    </div>
                  ) : phase === 'QUESTION_READY' || phase === 'AI_SPEAKING' ? (
                    <div className="flex items-center gap-2 text-[11px] text-slate-500">
                      <Volume2 className="h-3.5 w-3.5 text-brand-400 animate-pulse" />
                      <span>Examiner is speaking — microphone will activate automatically when done.</span>
                    </div>
                  ) : phase === 'STARTING_MICROPHONE' ? (
                    <div className="flex items-center gap-2 text-[11px] text-slate-500">
                      <Mic className="h-3.5 w-3.5 text-slate-400 animate-pulse" />
                      <span>Initializing audio channel…</span>
                    </div>
                  ) : (
                    <div className="flex items-center gap-2 text-[11px] text-slate-400">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                      <span>Fully hands-free: speak your answer — 10s pause auto-submits.</span>
                    </div>
                  )}
                  <span className="text-[10px] text-slate-500 uppercase tracking-widest font-mono">Hands-Free</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Answer Feedback Modal */}
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
                  <p className="text-xs text-slate-400">AI evaluation of your response</p>
                </div>
              </div>
              <div className="px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 font-bold text-sm">
                Score: {Math.round((lastFeedback.response_saved?.score || 0) * 10)}/10
              </div>
            </div>

            {/* Immediate Conversational Interviewer Feedback */}
            <div className="p-4 rounded-xl bg-gradient-to-br from-slate-950/80 to-slate-900/90 border border-brand-500/30 text-slate-200 shadow-inner space-y-2">
              <div className="flex items-center justify-between text-xs text-brand-400 font-semibold uppercase tracking-wider">
                <span className="flex items-center gap-1.5">
                  <MessageSquare className="h-3.5 w-3.5" /> Interviewer Reaction
                </span>
                <span className="text-[11px] text-slate-400 font-normal">Immediate Feedback</span>
              </div>
              <p className="text-sm font-medium text-slate-100 italic leading-relaxed pl-2 border-l-2 border-brand-500">
                &ldquo;{lastFeedback.response_saved?.feedback || 'Good response. Proceeding to the next question.'}&rdquo;
              </p>
            </div>

            {/* Next Question Preview (Generated directly from user's previous answer) */}
            {lastFeedback.next_question && (
              <div className="p-3.5 rounded-xl bg-slate-950/40 border border-slate-800/80 text-xs text-slate-300 space-y-1">
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                  Next Question (Adapted from your answer):
                </span>
                <p className="text-slate-200 leading-relaxed font-medium">
                  {lastFeedback.next_question.text}
                </p>
              </div>
            )}
            {autoAdvanceCountdown !== null && (
              <div className="rounded-xl bg-brand-500/10 border border-brand-500/20 p-2.5 flex items-center justify-between text-xs text-brand-300">
                <div className="flex items-center gap-2">
                  <Clock className="h-4 w-4 text-brand-400 animate-spin" />
                  <span>
                    {lastFeedback.interview_complete
                      ? `Completing examination in ${autoAdvanceCountdown}s…`
                      : `Loading next question in ${autoAdvanceCountdown}s…`}
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
                {lastFeedback.interview_complete
                  ? 'Complete Examination & View Summary'
                  : 'Proceed Immediately'}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="h-16 px-6 bg-slate-900/95 border-t border-slate-800 flex items-center justify-between z-30">
        <div className="flex items-center gap-2 text-xs text-slate-400">
          <span className="font-bold text-slate-300">Exam In Progress</span> &bull;
          <span>Full Proctoring Active</span>
        </div>
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => setShowCaptions((p) => !p)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 ${
              showCaptions
                ? 'bg-brand-600 text-white shadow-sm'
                : 'bg-slate-800 text-slate-400 border border-slate-700'
            }`}
          >
            <MessageSquare className="h-3.5 w-3.5" />
            <span>Subtitles</span>
          </button>
          <button
            type="button"
            onClick={handleLeaveInterview}
            disabled={isEnding}
            className="px-4 py-2 rounded-xl bg-red-600/90 hover:bg-red-500 text-white font-bold text-xs inline-flex items-center gap-1.5 shadow-lg shadow-red-500/20 transition-all ml-2"
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

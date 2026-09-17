import { useState } from 'react'
import { clsx } from 'clsx'
import { MessageSquare, GitBranch, TrendingUp, Mic, Volume2, VolumeX } from 'lucide-react'
import type { InterviewQuestion } from '@/types'

const PHASE_COLORS: Record<string, string> = {
  warmup:    'text-amber-400   bg-amber-400/10   border-amber-400/20',
  technical: 'text-blue-400    bg-blue-400/10    border-blue-400/20',
  project:   'text-violet-400  bg-violet-400/10  border-violet-400/20',
  hr:        'text-green-400   bg-green-400/10   border-green-400/20',
  closing:   'text-slate-400   bg-slate-400/10   border-slate-400/20',
  coding:    'text-pink-400    bg-pink-400/10    border-pink-400/20',
}

const DIFF_CONFIG = {
  easy:   { color: 'text-emerald-400', label: 'Easy'   },
  medium: { color: 'text-amber-400',   label: 'Medium' },
  hard:   { color: 'text-red-400',     label: 'Hard'   },
}

interface QuestionCardProps {
  question: InterviewQuestion
  turnNumber: number
  totalTurns?: number
}

export function QuestionCard({ question, turnNumber, totalTurns }: QuestionCardProps) {
  const phaseColor = PHASE_COLORS[question.phase] ?? PHASE_COLORS.technical
  const diffConf   = DIFF_CONFIG[question.difficulty] ?? DIFF_CONFIG.medium
  const [isSpeaking, setIsSpeaking] = useState(false)

  // Text-to-Speech: read the question aloud
  const handleReadAloud = () => {
    if (!('speechSynthesis' in window)) return
    if (isSpeaking) {
      window.speechSynthesis.cancel()
      setIsSpeaking(false)
      return
    }
    const utterance = new SpeechSynthesisUtterance(question.text)
    utterance.lang  = 'en-US'
    utterance.rate  = 0.92
    utterance.pitch = 1.0
    utterance.onend = () => setIsSpeaking(false)
    utterance.onerror = () => setIsSpeaking(false)
    setIsSpeaking(true)
    window.speechSynthesis.speak(utterance)
  }

  return (
    <div className="card p-6 space-y-4">
      {/* Header row */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2 flex-wrap">
          {/* Phase badge */}
          <span className={clsx(
            'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border',
            phaseColor,
          )}>
            <MessageSquare className="h-3 w-3" />
            {question.phase.charAt(0).toUpperCase() + question.phase.slice(1)}
          </span>

          {/* Topic */}
          {question.topic && (
            <span className="px-2.5 py-1 rounded-full text-xs font-medium bg-surface text-slate-400 border border-surface-border">
              {question.topic}
            </span>
          )}

          {/* Follow-up indicator */}
          {question.is_follow_up && (
            <span className={clsx(
              'inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium border',
              question.follow_up_reason === 'strong_answer'
                ? 'text-blue-400 bg-blue-400/10 border-blue-400/20'
                : 'text-amber-400 bg-amber-400/10 border-amber-400/20',
            )}>
              {question.follow_up_reason === 'strong_answer'
                ? <><TrendingUp className="h-3 w-3" /> Follow-up: Advanced</>
                : <><GitBranch className="h-3 w-3" /> Follow-up</>
              }
            </span>
          )}
        </div>

        {/* Right: difficulty + progress + TTS button */}
        <div className="flex items-center gap-3">
          <span className={clsx('text-xs font-medium', diffConf.color)}>
            {diffConf.label}
          </span>
          <span className="text-xs text-slate-500">
            Q{turnNumber}{totalTurns ? ` / ~${totalTurns}` : ''}
          </span>

          {/* Read aloud button */}
          {'speechSynthesis' in window && (
            <button
              onClick={handleReadAloud}
              title={isSpeaking ? 'Stop reading' : 'Read question aloud'}
              className={clsx(
                'p-1.5 rounded-lg transition-colors',
                isSpeaking
                  ? 'text-brand-400 bg-brand-400/10 animate-pulse'
                  : 'text-slate-500 hover:text-slate-300 hover:bg-surface-hover',
              )}
            >
              {isSpeaking
                ? <VolumeX className="h-4 w-4" />
                : <Volume2 className="h-4 w-4" />
              }
            </button>
          )}
        </div>
      </div>

      {/* Question text */}
      <div className="bg-surface rounded-xl p-4 border border-surface-border">
        <p className="text-slate-100 text-base leading-relaxed font-medium">
          {question.text}
        </p>
      </div>

      {/* Voice answer prompt */}
      <div className="flex items-center gap-2 text-xs text-slate-500">
        <Mic className="h-3.5 w-3.5 text-brand-400 flex-shrink-0" />
        <span>
          Tap the <span className="text-brand-400 font-medium">microphone button</span> below to speak your answer.
          {' '}The AI will transcribe and evaluate it automatically.
        </span>
      </div>
    </div>
  )
}

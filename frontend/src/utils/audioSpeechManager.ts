/**
 * Global audio and speech manager to ensure:
 * 1. Only ONE voice can EVER play at any given time (no overlapping dual voices).
 * 2. When advancing to the next question, any previous speech/audio is instantly killed
 *    and its error/ended handlers are detached so it never triggers fallbacks.
 * 3. When the user leaves or ends the interview, ALL audio and speech synthesis
 *    stops immediately.
 */

let activeAudio: HTMLAudioElement | null = null
let currentSpeechToken = 0

/**
 * Stop ALL playing audio and speech synthesis immediately.
 * Invalidates any in-flight speech attempts.
 */
export function stopAllAudioAndSpeech(): void {
  // Invalidate any async speech promises
  currentSpeechToken += 1

  // 1. Immediately detach handlers, pause, and discard any active Audio element
  if (activeAudio) {
    try {
      activeAudio.onended = null
      activeAudio.onerror = null
      activeAudio.onplay = null
      activeAudio.pause()
      activeAudio.currentTime = 0
      activeAudio.src = ''
    } catch (e) {
      console.warn('Error stopping active audio element:', e)
    }
    activeAudio = null
  }

  // 2. Immediately cancel any Web Speech Synthesis
  if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
    try {
      window.speechSynthesis.cancel()
    } catch (e) {
      console.warn('Error cancelling speechSynthesis:', e)
    }
  }
}

/**
 * Returns a new unique speech token. Any callback checking against this token
 * will know if it has been superseded by a newer question or a stop call.
 */
export function getNewSpeechToken(): number {
  stopAllAudioAndSpeech()
  return currentSpeechToken
}

/**
 * Checks if the given token is still the active, non-superseded speech token.
 */
export function isSpeechTokenValid(token: number): boolean {
  return token === currentSpeechToken
}

/**
 * Registers an Audio element as the currently active playing audio.
 */
export function registerActiveAudio(audio: HTMLAudioElement): void {
  activeAudio = audio
}

/**
 * Call during a direct user gesture (such as clicking "Start Interview" or "Continue")
 * to unlock Web Audio, HTML5 Audio, and Web Speech Synthesis across modern browsers
 * (Chrome, Edge, Safari, Firefox) so that subsequent automatic playback is permitted.
 */
export function unlockAudioForInterview(): void {
  if (typeof window === 'undefined') return

  // 1. Unlock Web Audio Context
  try {
    const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext
    if (AudioContextClass) {
      const ctx = new AudioContextClass()
      if (ctx.state === 'suspended') {
        ctx.resume().catch(() => {})
      }
      const buffer = ctx.createBuffer(1, 1, 22050)
      const source = ctx.createBufferSource()
      source.buffer = buffer
      source.connect(ctx.destination)
      source.start(0)
    }
  } catch (e) {
    console.debug('[Audio] WebAudio unlock attempt:', e)
  }

  // 2. Prime SpeechSynthesis without empty/whitespace utterance (prevents Chrome deadlock)
  if ('speechSynthesis' in window) {
    try {
      window.speechSynthesis.getVoices()
      if (window.speechSynthesis.paused) {
        window.speechSynthesis.resume()
      }
    } catch (e) {
      console.debug('[Audio] SpeechSynthesis prime attempt:', e)
    }
  }

  // 3. Prime HTMLAudioElement
  try {
    const silent = new Audio('data:audio/wav;base64,UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA')
    silent.volume = 0.01
    silent.play().catch(() => {})
  } catch (e) {
    console.debug('[Audio] HTMLAudio prime attempt:', e)
  }
}

// Global safety listeners: stop audio immediately on unload / pagehide
if (typeof window !== 'undefined') {
  window.addEventListener('beforeunload', stopAllAudioAndSpeech)
  window.addEventListener('pagehide', stopAllAudioAndSpeech)
}

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

// Global safety listeners: stop audio immediately on unload / pagehide
if (typeof window !== 'undefined') {
  window.addEventListener('beforeunload', stopAllAudioAndSpeech)
  window.addEventListener('pagehide', stopAllAudioAndSpeech)
}

/**
 * Global Audio and Speech Manager.
 *
 * Ensures:
 * 1. Only ONE voice can EVER play at any given time (prevents dual/overlapping audio).
 * 2. Unlocks both Web Audio AudioContext and SpeechSynthesis across Chrome/Edge/Firefox.
 * 3. Never kills in-flight audio due to stale promise rejections.
 * 4. Supports high-fidelity Web Audio API buffer playback to bypass HTML5 Audio autoplay restrictions.
 */

let activeAudio: HTMLAudioElement | null = null
let activeSourceNode: AudioBufferSourceNode | null = null
let sharedAudioElement: HTMLAudioElement | null = null
let globalAudioContext: AudioContext | null = null
let currentSpeechToken = 0
let isBrowserAudioUnlocked = false

/**
 * Returns a persistent singleton Audio element.
 */
export function getSharedAudio(): HTMLAudioElement {
  if (!sharedAudioElement && typeof window !== 'undefined') {
    sharedAudioElement = new Audio()
    sharedAudioElement.preload = 'auto'
  }
  return sharedAudioElement!
}

/**
 * Returns or initializes the global Web Audio AudioContext.
 */
export function getGlobalAudioContext(): AudioContext | null {
  if (typeof window === 'undefined') return null
  if (!globalAudioContext) {
    try {
      const AudioCtx = window.AudioContext || (window as any).webkitAudioContext
      if (AudioCtx) {
        globalAudioContext = new AudioCtx()
      }
    } catch (e) {
      console.warn('AudioContext initialization deferred:', e)
    }
  }
  return globalAudioContext
}

/**
 * Proactively unlocks the browser's audio engine during user click/touch gestures.
 * This unlocks both HTMLMediaElement audio playback and SpeechSynthesis across Chrome/Edge/Firefox.
 */
export function unlockBrowserAudio(): void {
  if (typeof window === 'undefined') return

  isBrowserAudioUnlocked = true

  // 1. Resume Web Audio AudioContext
  try {
    const ctx = getGlobalAudioContext()
    if (ctx) {
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
    console.debug('AudioContext resume warning:', e)
  }

  // 2. Prime HTML5 Audio engine with a standalone primer (does NOT touch sharedAudioElement)
  try {
    const primer = new Audio('data:audio/wav;base64,UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA')
    primer.volume = 0.01
    primer.play().catch(() => {})
  } catch (e) {
    console.debug('Silent audio prime warning:', e)
  }

  // 3. Unstick and prime Web Speech Synthesis engine
  if ('speechSynthesis' in window) {
    try {
      if (window.speechSynthesis.paused) {
        window.speechSynthesis.resume()
      }
      // Warm up voice list
      window.speechSynthesis.getVoices()
    } catch (e) {
      console.debug('SpeechSynthesis prime warning:', e)
    }
  }
}

/**
 * Stop ALL playing audio, Web Audio buffers, and speech synthesis immediately.
 */
export function stopAllAudioAndSpeech(): void {
  // Invalidate any async speech promises
  currentSpeechToken += 1

  // 1. Stop Web Audio buffer source if playing
  if (activeSourceNode) {
    try {
      activeSourceNode.onended = null
      activeSourceNode.stop()
      activeSourceNode.disconnect()
    } catch {}
    activeSourceNode = null
  }

  // 2. Immediately detach handlers and pause active Audio element
  if (activeAudio) {
    try {
      activeAudio.onended = null
      activeAudio.onerror = null
      activeAudio.onplay = null
      activeAudio.pause()
      activeAudio.currentTime = 0
    } catch (e) {
      console.warn('Error stopping active audio element:', e)
    }
    if (activeAudio !== sharedAudioElement) {
      try {
        activeAudio.src = ''
      } catch {}
      activeAudio = null
    }
  }

  // 3. Immediately cancel any Web Speech Synthesis
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
 * will know if it has been superseded by a newer question.
 */
export function getNewSpeechToken(): number {
  stopAllAudioAndSpeech()
  return currentSpeechToken
}

/**
 * Checks if the given token is still the active speech token.
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
 * Registers an AudioBufferSourceNode as the currently active playing audio.
 */
export function registerActiveSourceNode(node: AudioBufferSourceNode): void {
  activeSourceNode = node
}

/**
 * Call during a direct user gesture (such as clicking "Start Interview" or "Continue")
 * to unlock Web Audio, HTML5 Audio, and Web Speech Synthesis across modern browsers
 * so that subsequent automatic playback is permitted.
 */
export const unlockAudioForInterview = unlockBrowserAudio

// Global safety listeners: stop audio immediately on unload / pagehide
if (typeof window !== 'undefined') {
  window.addEventListener('beforeunload', stopAllAudioAndSpeech)
  window.addEventListener('pagehide', stopAllAudioAndSpeech)
}

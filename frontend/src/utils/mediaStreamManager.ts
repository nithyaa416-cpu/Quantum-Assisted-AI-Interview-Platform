/**
 * Global media stream manager to guarantee camera and microphone tracks
 * are cleanly killed and hardware lights (webcam LED) turn off immediately
 * when leaving or quitting the interview.
 */

const activeStreams = new Set<MediaStream>()

export function registerMediaStream(stream: MediaStream): void {
  activeStreams.add(stream)
}

export function unregisterMediaStream(stream: MediaStream): void {
  activeStreams.delete(stream)
}

export function stopAllMediaStreams(): void {
  activeStreams.forEach((stream) => {
    try {
      stream.getTracks().forEach((track) => {
        track.stop()
        track.enabled = false
      })
    } catch (e) {
      console.warn('Error stopping track:', e)
    }
  })
  activeStreams.clear()
}

export function getActiveMediaStream(): MediaStream | null {
  for (const stream of activeStreams) {
    if (stream.active) {
      const audioTracks = stream.getAudioTracks()
      if (audioTracks.some((t) => t.readyState === 'live')) {
        return stream
      }
    }
  }
  return null
}

// ── Automatic Global Interceptor: Track EVERY getUserMedia stream ────────────
if (typeof window !== 'undefined' && navigator?.mediaDevices?.getUserMedia) {
  const originalGetUserMedia = navigator.mediaDevices.getUserMedia.bind(navigator.mediaDevices)
  navigator.mediaDevices.getUserMedia = async function (constraints) {
    const stream = await originalGetUserMedia(constraints)
    activeStreams.add(stream)
    return stream
  }
}

// Global safety listener on window unload and route navigation
if (typeof window !== 'undefined') {
  window.addEventListener('beforeunload', () => {
    stopAllMediaStreams()
  })
  window.addEventListener('pagehide', () => {
    stopAllMediaStreams()
  })
}

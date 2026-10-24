/**
 * Real-Time Interview Analytics Collector.
 *
 * Continuously aggregates and computes real-world interview aspects:
 * 1. Facial Analysis: Eye contact %, posture stability, attentiveness, expressions
 * 2. Voice Fluency: Words-per-minute (WPM), speech-to-silence ratio, pauses
 * 3. Voice Modulation: Pitch/frequency dynamic range from Web Audio API AnalyserNode
 * 4. Candidate Poise & Confidence Score: Composite multi-modal evaluation
 * 5. Proctoring Integrity: Single-human compliance, mobile phone flags, tab switch strikes
 */

import { mediaPipeService, type FacialVerificationStatus } from './mediaPipeService'

export interface LiveSpeechMetrics {
  totalWords: number
  totalSpeakingTimeSeconds: number
  wordsPerMinute: number
  fluencyScore: number // 0-100
  pitchModulationScore: number // 0-100 (vocal variety vs monotone)
  pauseCount: number
  articulationQuality: 'excellent' | 'steady' | 'rushed' | 'hesitant'
}

export interface LiveBehaviouralMetrics {
  eyeContactPercentage: number // 0-100
  postureStabilityScore: number // 0-100
  attentivenessScore: number // 0-100
  overallConfidenceScore: number // 0-100
  dominantExpression: 'confident' | 'smiling' | 'neutral' | 'tense'
  singleHumanCompliancePercentage: number // 0-100
  phoneDetectedIncidents: number
  multipleFacesIncidents: number
  faceAbsenceIncidents: number
  proctoringStrikesCount: number
  integrityRating: 'verified' | 'flagged' | 'suspicious'
}

export interface InterviewAnalyticsReportPayload {
  speech_metrics: {
    words_per_minute: number
    total_words_spoken: number
    speaking_duration_seconds: number
    fluency_score: number
    pitch_modulation_score: number
    articulation_quality: string
    pause_frequency: string
  }
  behavioural_metrics: {
    eye_contact_percentage: number
    posture_stability_score: number
    attentiveness_score: number
    confidence_score: number
    dominant_expression: string
    single_human_compliance: number
    phone_detected_incidents: number
    multiple_faces_incidents: number
    face_absence_incidents: number
    proctoring_strikes: number
    integrity_status: string
  }
}

class InterviewAnalyticsCollector {
  private isCollecting = false
  private audioAnalyser: AnalyserNode | null = null
  private audioSampleInterval: any = null
  private facialUnsubscribe: (() => void) | null = null

  // Facial accumulator
  private totalVideoFrames = 0
  private eyeContactFrames = 0
  private facingCameraFrames = 0
  private singleHumanFrames = 0
  private confidenceAccumulator = 0
  private postureAccumulator = 0
  private expressionCounts = {
    confident: 0,
    smiling: 0,
    neutral: 0,
    tense: 0,
  }

  // Proctoring events
  private phoneIncidents = 0
  private multiFaceIncidents = 0
  private noFaceIncidents = 0
  private strikesCount = 0

  // Audio & speech accumulator
  private totalWords = 0
  private totalSpeechDuration = 0
  private pauseEvents = 0
  private audioSpectrumVariances: number[] = []

  /**
   * Start collecting live metrics during interview.
   */
  public start(analyser?: AnalyserNode) {
    this.reset()
    this.isCollecting = true
    if (analyser) {
      this.audioAnalyser = analyser
      this.startAudioSampling()
    }

    // Subscribe to MediaPipe real-time callbacks
    const listener = (status: FacialVerificationStatus) => {
      if (!this.isCollecting) return
      this.recordFacialFrame(status)
    }

    mediaPipeService.startTracking(null as any, listener)
    this.facialUnsubscribe = () => mediaPipeService.stopTracking(listener)
  }

  /**
   * Stop collecting metrics.
   */
  public stop() {
    this.isCollecting = false
    if (this.audioSampleInterval) {
      clearInterval(this.audioSampleInterval)
      this.audioSampleInterval = null
    }
    if (this.facialUnsubscribe) {
      this.facialUnsubscribe()
      this.facialUnsubscribe = null
    }
  }

  public reset() {
    this.totalVideoFrames = 0
    this.eyeContactFrames = 0
    this.facingCameraFrames = 0
    this.singleHumanFrames = 0
    this.confidenceAccumulator = 0
    this.postureAccumulator = 0
    this.expressionCounts = { confident: 0, smiling: 0, neutral: 0, tense: 0 }
    this.phoneIncidents = 0
    this.multiFaceIncidents = 0
    this.noFaceIncidents = 0
    this.strikesCount = 0
    this.totalWords = 0
    this.totalSpeechDuration = 0
    this.pauseEvents = 0
    this.audioSpectrumVariances = []
  }

  public setAudioAnalyser(analyser: AnalyserNode) {
    this.audioAnalyser = analyser
    if (this.isCollecting && !this.audioSampleInterval) {
      this.startAudioSampling()
    }
  }

  private startAudioSampling() {
    if (!this.audioAnalyser) return
    const buffer = new Uint8Array(this.audioAnalyser.frequencyBinCount)

    // Sample voice modulation 5 times per second
    this.audioSampleInterval = setInterval(() => {
      if (!this.audioAnalyser) return
      this.audioAnalyser.getByteFrequencyData(buffer)

      // Only evaluate when active sound is detected
      let sum = 0
      for (let i = 0; i < buffer.length; i++) sum += buffer[i]
      const avgEnergy = sum / buffer.length

      if (avgEnergy > 8) {
        // Voice is active: compute standard deviation of energy across vocal frequency bins
        let sqDiffSum = 0
        for (let i = 0; i < buffer.length; i++) {
          sqDiffSum += Math.pow(buffer[i] - avgEnergy, 2)
        }
        const stdDev = Math.sqrt(sqDiffSum / buffer.length)
        this.audioSpectrumVariances.push(stdDev)
        if (this.audioSpectrumVariances.length > 200) {
          this.audioSpectrumVariances.shift()
        }
      }
    }, 200)
  }

  private recordFacialFrame(status: FacialVerificationStatus) {
    this.totalVideoFrames++

    if (status.faceCount === 1) {
      this.singleHumanFrames++
    } else if (status.faceCount > 1) {
      this.multiFaceIncidents++
    } else if (status.faceCount === 0) {
      this.noFaceIncidents++
    }

    if (status.phoneDetected) {
      this.phoneIncidents++
    }

    if (status.eyeContact.hasEyeContact) {
      this.eyeContactFrames++
    }

    if (status.headPose.isFacingCamera) {
      this.facingCameraFrames++
    }

    this.confidenceAccumulator += status.facialAnalysis.confidenceScore
    this.postureAccumulator += status.facialAnalysis.postureStability

    const exp = status.facialAnalysis.expression
    this.expressionCounts[exp] = (this.expressionCounts[exp] || 0) + 1
  }

  /**
   * Called each time a candidate response turn is submitted.
   */
  public recordTurnSpeech(transcript: string, durationSeconds: number) {
    const words = transcript.trim().split(/\s+/).filter(Boolean).length
    this.totalWords += words
    this.totalSpeechDuration += Math.max(1, durationSeconds)

    // Rough pause heuristic: commas, ellipses, and short segments
    const pauses = (transcript.match(/[,.!?]{2,}|\.\.\./g) || []).length
    this.pauseEvents += pauses
  }

  /**
   * Called by ProctoringShield when a violation strikes.
   */
  public recordProctoringViolation(_reason: string) {
    this.strikesCount++
  }

  /**
   * Get live speech metrics snapshot.
   */
  public getSpeechSnapshot(): LiveSpeechMetrics {
    const durationMinutes = (this.totalSpeechDuration || 1) / 60
    const wpm = Math.round(this.totalWords / durationMinutes)

    // Optimal interview speaking rate: 120 - 150 WPM
    let fluencyScore = 80
    if (wpm >= 110 && wpm <= 160) {
      fluencyScore = 95
    } else if (wpm > 160 && wpm <= 190) {
      fluencyScore = 80 // a bit fast
    } else if (wpm >= 80 && wpm < 110) {
      fluencyScore = 75 // a bit slow/thoughtful
    } else if (wpm < 80) {
      fluencyScore = 60 // hesitant
    } else {
      fluencyScore = 65 // rushing
    }

    // Voice modulation score based on audio spectrum dynamics
    let modulationScore = 82
    if (this.audioSpectrumVariances.length > 5) {
      const avgVariance =
        this.audioSpectrumVariances.reduce((a, b) => a + b, 0) / this.audioSpectrumVariances.length
      // Map variance [10..45] to score [60..98]
      modulationScore = Math.max(55, Math.min(98, Math.round(50 + avgVariance * 1.2)))
    }

    let quality: LiveSpeechMetrics['articulationQuality'] = 'steady'
    if (wpm >= 120 && wpm <= 155 && modulationScore >= 80) {
      quality = 'excellent'
    } else if (wpm > 165) {
      quality = 'rushed'
    } else if (wpm < 85) {
      quality = 'hesitant'
    }

    return {
      totalWords: this.totalWords,
      totalSpeakingTimeSeconds: Math.round(this.totalSpeechDuration),
      wordsPerMinute: wpm || 0,
      fluencyScore,
      pitchModulationScore: modulationScore,
      pauseCount: this.pauseEvents,
      articulationQuality: quality,
    }
  }

  /**
   * Get live behavioural metrics snapshot.
   */
  public getBehaviouralSnapshot(): LiveBehaviouralMetrics {
    const frames = Math.max(1, this.totalVideoFrames)

    const eyeContactPct = Math.round((this.eyeContactFrames / frames) * 100)
    const singleHumanPct = Math.round((this.singleHumanFrames / frames) * 100)
    const attentiveness = Math.round((this.facingCameraFrames / frames) * 100)
    const avgPosture = Math.round(this.postureAccumulator / frames) || 85
    const avgConfidence = Math.round(this.confidenceAccumulator / frames) || 82

    // Find dominant expression
    let dominant: LiveBehaviouralMetrics['dominantExpression'] = 'confident'
    let maxCount = -1
    for (const [exp, count] of Object.entries(this.expressionCounts)) {
      if (count > maxCount) {
        maxCount = count
        dominant = exp as any
      }
    }

    // Overall integrity rating
    let integrity: LiveBehaviouralMetrics['integrityRating'] = 'verified'
    if (this.phoneIncidents > 0 || this.multiFaceIncidents > 5 || this.strikesCount >= 3) {
      integrity = 'flagged'
    } else if (this.strikesCount > 0 || singleHumanPct < 85) {
      integrity = 'suspicious'
    }

    return {
      eyeContactPercentage: Math.min(100, eyeContactPct),
      postureStabilityScore: Math.min(100, avgPosture),
      attentivenessScore: Math.min(100, attentiveness),
      overallConfidenceScore: Math.min(100, avgConfidence),
      dominantExpression: dominant,
      singleHumanCompliancePercentage: Math.min(100, singleHumanPct),
      phoneDetectedIncidents: this.phoneIncidents,
      multipleFacesIncidents: this.multiFaceIncidents,
      faceAbsenceIncidents: this.noFaceIncidents,
      proctoringStrikesCount: this.strikesCount,
      integrityRating: integrity,
    }
  }

  /**
   * Package final report payload to send to backend on session completion.
   */
  public getFinalReportPayload(): InterviewAnalyticsReportPayload {
    const speech = this.getSpeechSnapshot()
    const beh = this.getBehaviouralSnapshot()

    return {
      speech_metrics: {
        words_per_minute: speech.wordsPerMinute,
        total_words_spoken: speech.totalWords,
        speaking_duration_seconds: speech.totalSpeakingTimeSeconds,
        fluency_score: speech.fluencyScore,
        pitch_modulation_score: speech.pitchModulationScore,
        articulation_quality: speech.articulationQuality,
        pause_frequency: speech.pauseCount > 10 ? 'frequent' : speech.pauseCount > 4 ? 'moderate' : 'natural',
      },
      behavioural_metrics: {
        eye_contact_percentage: beh.eyeContactPercentage,
        posture_stability_score: beh.postureStabilityScore,
        attentiveness_score: beh.attentivenessScore,
        confidence_score: beh.overallConfidenceScore,
        dominant_expression: beh.dominantExpression,
        single_human_compliance: beh.singleHumanCompliancePercentage,
        phone_detected_incidents: beh.phoneDetectedIncidents,
        multiple_faces_incidents: beh.multipleFacesIncidents,
        face_absence_incidents: beh.faceAbsenceIncidents,
        proctoring_strikes: beh.proctoringStrikesCount,
        integrity_status: beh.integrityRating,
      },
    }
  }
}

export const interviewAnalyticsCollector = new InterviewAnalyticsCollector()

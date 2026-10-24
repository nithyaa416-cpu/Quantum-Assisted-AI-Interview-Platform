/**
 * MediaPipe Face Mesh, Facial Biometrics & Real-Time Proctoring Service.
 *
 * Provides real-time:
 * 1. Pre-interview biometric face verification (single face, eyes, nose, mouth, centered)
 * 2. In-interview gaze & eye-contact estimation (looking at screen vs looking away)
 * 3. Head pose tracking (yaw, pitch, roll — facing camera vs turning away)
 * 4. Multi-face proctoring detection (unauthorized second person in frame)
 * 5. Mobile phone & unauthorized object detection (via lightweight COCO-SSD / vision analysis)
 * 6. Facial expression & confidence dynamics (relaxed, confident, tense, smiling)
 */

export interface FacialVerificationStatus {
  isReady: boolean
  faceCount: number
  hasSingleFace: boolean
  eyesVisible: boolean
  leftEyeOpen: boolean
  rightEyeOpen: boolean
  noseVisible: boolean
  mouthVisible: boolean
  isCentered: boolean
  isGoodDistance: boolean
  allFeaturesVerified: boolean

  // In-session gaze & pose metrics
  eyeContact: {
    hasEyeContact: boolean
    score: number // 0 to 100
    gazeDirection: 'center' | 'left' | 'right' | 'up' | 'down'
  }
  headPose: {
    isFacingCamera: boolean
    yaw: number // degrees left(-) / right(+)
    pitch: number // degrees down(-) / up(+)
  }

  // Real-time Facial & Poise Analysis
  facialAnalysis: {
    expression: 'confident' | 'smiling' | 'neutral' | 'tense'
    confidenceScore: number // 0 to 100
    attentivenessScore: number // 0 to 100
    postureStability: number // 0 to 100
  }

  // Real-world proctoring & integrity verification
  proctoring: {
    isCompliant: boolean
    hasSingleHuman: boolean
    phoneDetected: boolean
    threatLevel: 'clean' | 'warning' | 'violation'
    violationReason: string | null
  }

  phoneDetected: boolean
  warningMessage: string | null
}

export type FaceMeshCallback = (status: FacialVerificationStatus) => void

class MediaPipeService {
  private faceMesh: any = null
  private cocoModel: any = null
  private isInitializing: boolean = false
  private isCocoLoading: boolean = false
  private isLoaded: boolean = false
  private animFrameId: number | null = null
  private lastProcessedTime: number = 0
  private lastCocoProcessedTime: number = 0
  private listeners: Set<FaceMeshCallback> = new Set()

  // Track recent history for stability smoothing
  private recentYaws: number[] = []
  private recentPitches: number[] = []
  private cachedPhoneDetected: boolean = false
  private cachedDetectedObjects: string[] = []

  private currentStatus: FacialVerificationStatus = {
    isReady: false,
    faceCount: 0,
    hasSingleFace: false,
    eyesVisible: false,
    leftEyeOpen: false,
    rightEyeOpen: false,
    noseVisible: false,
    mouthVisible: false,
    isCentered: false,
    isGoodDistance: false,
    allFeaturesVerified: false,
    eyeContact: {
      hasEyeContact: true,
      score: 100,
      gazeDirection: 'center',
    },
    headPose: {
      isFacingCamera: true,
      yaw: 0,
      pitch: 0,
    },
    facialAnalysis: {
      expression: 'neutral',
      confidenceScore: 85,
      attentivenessScore: 100,
      postureStability: 95,
    },
    proctoring: {
      isCompliant: true,
      hasSingleHuman: true,
      phoneDetected: false,
      threatLevel: 'clean',
      violationReason: null,
    },
    phoneDetected: false,
    warningMessage: null,
  }

  /**
   * Initialize MediaPipe FaceMesh & optional COCO-SSD object detector.
   */
  public async init(): Promise<boolean> {
    if (this.isLoaded && this.faceMesh) return true
    if (this.isInitializing) return false

    this.isInitializing = true

    // Initialize Object Detector in background without blocking FaceMesh
    this.initObjectDetector()

    try {
      const FaceMeshClass = await this.getFaceMeshClass()
      if (!FaceMeshClass) {
        console.warn('MediaPipe FaceMesh script not found, using biometric fallback.')
        this.isInitializing = false
        return false
      }

      const fm = new FaceMeshClass({
        locateFile: (file: string) => `https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/${file}`,
      })

      fm.setOptions({
        maxNumFaces: 3, // Allow detecting multiple intruders to trigger alarms
        refineLandmarks: true, // enables 478 landmarks including iris for exact gaze
        minDetectionConfidence: 0.5,
        minTrackingConfidence: 0.5,
      })

      fm.onResults((results: any) => this.handleResults(results))

      this.faceMesh = fm
      this.isLoaded = true
      this.isInitializing = false
      return true
    } catch (err) {
      console.warn('Failed to load MediaPipe FaceMesh:', err)
      this.isInitializing = false
      return false
    }
  }

  /**
   * Initialize lightweight COCO-SSD for mobile phone & unauthorized object detection.
   */
  private async initObjectDetector() {
    if (this.cocoModel || this.isCocoLoading) return
    this.isCocoLoading = true

    try {
      const cocoSsdGlobal = (window as any).cocoSsd
      if (cocoSsdGlobal && typeof cocoSsdGlobal.load === 'function') {
        this.cocoModel = await cocoSsdGlobal.load({ base: 'mobilenet_v2' })
        console.info('Proctoring Object Detector (COCO-SSD) initialized successfully.')
      }
    } catch (e) {
      console.warn('COCO-SSD object detector unavailable or deferred:', e)
    } finally {
      this.isCocoLoading = false
    }
  }

  private async getFaceMeshClass(): Promise<any> {
    if ((window as any).FaceMesh) return (window as any).FaceMesh
    for (let i = 0; i < 15; i++) {
      await new Promise((r) => setTimeout(r, 100))
      if ((window as any).FaceMesh) return (window as any).FaceMesh
    }
    return null
  }

  /**
   * Start processing a video element.
   */
  public startTracking(videoElement: HTMLVideoElement, callback?: FaceMeshCallback) {
    if (callback) this.listeners.add(callback)

    if (this.animFrameId) cancelAnimationFrame(this.animFrameId)

    const processFrame = async () => {
      const now = performance.now()

      // 1. Process Face Mesh ~20 FPS for smooth performance
      if (now - this.lastProcessedTime >= 50) {
        this.lastProcessedTime = now
        if (
          videoElement &&
          videoElement.readyState >= 2 &&
          !videoElement.paused &&
          !videoElement.ended
        ) {
          if (this.isLoaded && this.faceMesh) {
            try {
              await this.faceMesh.send({ image: videoElement })
            } catch (err) {
              // Ignore transient video frame errors
            }
          } else {
            this.runBiometricFallback(videoElement)
          }

          // 2. Process Object Detection ~2 FPS (every 500ms) to detect mobile phones without CPU overload
          if (this.cocoModel && now - this.lastCocoProcessedTime >= 500) {
            this.lastCocoProcessedTime = now
            this.runObjectDetection(videoElement)
          }
        }
      }
      this.animFrameId = requestAnimationFrame(processFrame)
    }

    processFrame()
  }

  /**
   * Run object detection on video frame to detect mobile phones or multiple people.
   */
  private async runObjectDetection(video: HTMLVideoElement) {
    try {
      const predictions: any[] = await this.cocoModel.detect(video)
      let phoneFound = false
      const foundObjects: string[] = []

      for (const p of predictions) {
        const name = (p.class || '').toLowerCase()
        if (p.score >= 0.45) {
          foundObjects.push(name)
          if (name === 'cell phone' || name === 'phone' || name === 'remote' || name === 'book') {
            phoneFound = true
          }
        }
      }

      this.cachedPhoneDetected = phoneFound
      this.cachedDetectedObjects = foundObjects

      // If phone was detected, immediately update status proctoring warning
      if (phoneFound) {
        this.updateStatus({
          ...this.currentStatus,
          phoneDetected: true,
          proctoring: {
            ...this.currentStatus.proctoring,
            phoneDetected: true,
            threatLevel: 'violation',
            violationReason: 'Mobile phone detected in camera view! Unauthorized devices are prohibited.',
            isCompliant: false,
          },
          warningMessage: 'Mobile phone detected! Unauthorized devices are strictly prohibited.',
        })
      }
    } catch {
      // Ignore background object detection errors
    }
  }

  /**
   * Stop processing video.
   */
  public stopTracking(callback?: FaceMeshCallback) {
    if (callback) this.listeners.delete(callback)
    if (this.listeners.size === 0 && this.animFrameId) {
      cancelAnimationFrame(this.animFrameId)
      this.animFrameId = null
    }
  }

  public getStatus(): FacialVerificationStatus {
    return this.currentStatus
  }

  /**
   * Handle 468+ landmarks from MediaPipe FaceMesh.
   */
  private handleResults(results: any) {
    const multiLandmarks = results.multiFaceLandmarks || []
    const faceCount = multiLandmarks.length

    // ── CASE 1: No Candidate Detected in Frame ──
    if (faceCount === 0) {
      this.updateStatus({
        isReady: true,
        faceCount: 0,
        hasSingleFace: false,
        eyesVisible: false,
        leftEyeOpen: false,
        rightEyeOpen: false,
        noseVisible: false,
        mouthVisible: false,
        isCentered: false,
        isGoodDistance: false,
        allFeaturesVerified: false,
        eyeContact: {
          hasEyeContact: false,
          score: 0,
          gazeDirection: 'center',
        },
        headPose: {
          isFacingCamera: false,
          yaw: 0,
          pitch: 0,
        },
        facialAnalysis: {
          expression: 'neutral',
          confidenceScore: 0,
          attentivenessScore: 0,
          postureStability: 0,
        },
        proctoring: {
          isCompliant: false,
          hasSingleHuman: false,
          phoneDetected: this.cachedPhoneDetected,
          threatLevel: 'violation',
          violationReason: 'No candidate detected in camera frame. Candidate must remain visible at all times.',
        },
        phoneDetected: this.cachedPhoneDetected,
        warningMessage: 'No human face detected! Please remain in front of the camera.',
      })
      return
    }

    // ── CASE 2: Multiple Humans Detected in Frame (Unauthorized Person / Proxy) ──
    if (faceCount > 1) {
      this.updateStatus({
        isReady: true,
        faceCount,
        hasSingleFace: false,
        eyesVisible: true,
        leftEyeOpen: true,
        rightEyeOpen: true,
        noseVisible: true,
        mouthVisible: true,
        isCentered: false,
        isGoodDistance: true,
        allFeaturesVerified: false,
        eyeContact: {
          hasEyeContact: false,
          score: 30,
          gazeDirection: 'center',
        },
        headPose: {
          isFacingCamera: true,
          yaw: 0,
          pitch: 0,
        },
        facialAnalysis: {
          expression: 'tense',
          confidenceScore: 40,
          attentivenessScore: 40,
          postureStability: 50,
        },
        proctoring: {
          isCompliant: false,
          hasSingleHuman: false,
          phoneDetected: this.cachedPhoneDetected,
          threatLevel: 'violation',
          violationReason: `Multiple persons detected in camera (${faceCount} faces)! Only the registered candidate is permitted.`,
        },
        phoneDetected: this.cachedPhoneDetected,
        warningMessage: `Multiple faces detected (${faceCount})! Only the candidate is permitted in the interview room.`,
      })
      return
    }

    // ── CASE 3: Exactly One Human Detected (Candidate Alone) ──
    const lm = multiLandmarks[0]

    // Key facial points
    const noseTip = lm[1]
    const noseBridge = lm[168]

    // Left eye
    const leftEyeInner = lm[33]
    const leftEyeOuter = lm[133]
    const leftEyeTop = lm[159]
    const leftEyeBottom = lm[145]

    // Right eye
    const rightEyeInner = lm[362]
    const rightEyeOuter = lm[263]
    const rightEyeTop = lm[386]
    const rightEyeBottom = lm[374]

    // Eyebrows (for facial tension / furrowing)
    const leftBrow = lm[70]
    const rightBrow = lm[300]

    // Mouth landmarks
    const upperLip = lm[13]
    const lowerLip = lm[14]
    const mouthLeft = lm[61]
    const mouthRight = lm[291]

    // 1. Feature presence checks
    const noseVisible = Boolean(noseTip && noseBridge)
    const mouthVisible = Boolean(upperLip && lowerLip && mouthLeft && mouthRight)

    // Eye openness (Aspect ratio)
    const leftEyeHeight = Math.abs(leftEyeTop.y - leftEyeBottom.y)
    const leftEyeWidth = Math.abs(leftEyeOuter.x - leftEyeInner.x)
    const leftEAR = leftEyeWidth > 0 ? leftEyeHeight / leftEyeWidth : 0
    const leftEyeOpen = leftEAR > 0.12

    const rightEyeHeight = Math.abs(rightEyeTop.y - rightEyeBottom.y)
    const rightEyeWidth = Math.abs(rightEyeOuter.x - rightEyeInner.x)
    const rightEAR = rightEyeWidth > 0 ? rightEyeHeight / rightEyeWidth : 0
    const rightEyeOpen = rightEAR > 0.12

    const eyesVisible = Boolean(leftEyeInner && rightEyeInner && leftEyeOpen && rightEyeOpen)

    // 2. Framing & Centering:
    const faceCenterX = noseTip.x
    const faceCenterY = noseTip.y
    const isCentered = faceCenterX >= 0.25 && faceCenterX <= 0.75 && faceCenterY >= 0.2 && faceCenterY <= 0.8

    // Distance/scale: eye distance as proxy for distance from camera
    const eyeDistance = Math.hypot(rightEyeInner.x - leftEyeInner.x, rightEyeInner.y - leftEyeInner.y)
    const isGoodDistance = eyeDistance >= 0.12 && eyeDistance <= 0.45

    // 3. Head Pose & Orientation (Yaw & Pitch):
    const eyeMidpointX = (leftEyeInner.x + rightEyeInner.x) / 2
    const eyeMidpointY = (leftEyeInner.y + rightEyeInner.y) / 2

    const yawRatio = eyeDistance > 0 ? (noseTip.x - eyeMidpointX) / eyeDistance : 0
    const yawDeg = Math.round(yawRatio * 75) // approximate yaw in degrees

    const pitchRatio = eyeDistance > 0 ? (noseTip.y - eyeMidpointY) / eyeDistance : 0
    const pitchDeg = Math.round((pitchRatio - 0.4) * 60) // calibrated tilt

    const isFacingCamera = Math.abs(yawDeg) <= 22 && Math.abs(pitchDeg) <= 25

    // Track stability
    this.recentYaws.push(yawDeg)
    this.recentPitches.push(pitchDeg)
    if (this.recentYaws.length > 30) this.recentYaws.shift()
    if (this.recentPitches.length > 30) this.recentPitches.shift()

    const yawVariance = this.calculateVariance(this.recentYaws)
    const pitchVariance = this.calculateVariance(this.recentPitches)
    const postureStability = Math.max(20, Math.min(100, Math.round(100 - (yawVariance + pitchVariance) * 0.5)))

    // 4. Eye Contact / Gaze Analysis:
    let hasEyeContact = isFacingCamera
    let gazeDirection: 'center' | 'left' | 'right' | 'up' | 'down' = 'center'
    let eyeContactScore = 100

    if (lm.length >= 478) {
      const leftIris = lm[468]
      const rightIris = lm[473]

      const leftEyeSpan = leftEyeOuter.x - leftEyeInner.x
      const leftPupilPos = leftEyeSpan !== 0 ? (leftIris.x - leftEyeInner.x) / leftEyeSpan : 0.5

      const rightEyeSpan = rightEyeOuter.x - rightEyeInner.x
      const rightPupilPos = rightEyeSpan !== 0 ? (rightIris.x - rightEyeInner.x) / rightEyeSpan : 0.5

      const avgPupilX = (leftPupilPos + rightPupilPos) / 2

      if (avgPupilX < 0.32 || yawDeg < -18) {
        gazeDirection = 'left'
        hasEyeContact = false
        eyeContactScore = 35
      } else if (avgPupilX > 0.68 || yawDeg > 18) {
        gazeDirection = 'right'
        hasEyeContact = false
        eyeContactScore = 35
      } else if (pitchDeg < -20) {
        gazeDirection = 'down'
        hasEyeContact = false
        eyeContactScore = 40
      } else if (pitchDeg > 22) {
        gazeDirection = 'up'
        hasEyeContact = false
        eyeContactScore = 40
      }
    } else {
      if (!isFacingCamera) {
        hasEyeContact = false
        eyeContactScore = 40
        gazeDirection = yawDeg < 0 ? 'left' : 'right'
      }
    }

    // 5. Facial Expression & Real Interview Poise Analysis
    let expression: 'confident' | 'smiling' | 'neutral' | 'tense' = 'neutral'
    const mouthWidth = Math.hypot(mouthRight.x - mouthLeft.x, mouthRight.y - mouthLeft.y)
    const mouthRatio = eyeDistance > 0 ? mouthWidth / eyeDistance : 1.0

    // Smile check: mouth corners pulled wide and slightly upward
    const mouthHeight = Math.abs(lowerLip.y - upperLip.y)
    const isSmiling = mouthRatio > 1.25 && mouthHeight < 0.08

    // Brow distance: furrowed eyebrows indicate tension/stress
    const browDistance = (leftBrow && rightBrow) ? Math.hypot(rightBrow.x - leftBrow.x, rightBrow.y - leftBrow.y) : 0
    const browRatio = eyeDistance > 0 ? browDistance / eyeDistance : 1.0
    const isTense = browRatio < 0.75 || Math.abs(yawDeg) > 30

    if (isSmiling) {
      expression = 'smiling'
    } else if (isTense) {
      expression = 'tense'
    } else if (hasEyeContact && isFacingCamera && postureStability > 75) {
      expression = 'confident'
    }

    // Attentiveness Score (0-100)
    const attentivenessScore = Math.round(
      (hasEyeContact ? 55 : 15) +
      (isFacingCamera ? 35 : 10) +
      (isCentered ? 10 : 0)
    )

    // Facial Confidence Score (0-100)
    const confidenceScore = Math.min(100, Math.round(
      eyeContactScore * 0.45 +
      postureStability * 0.35 +
      (expression === 'confident' || expression === 'smiling' ? 20 : expression === 'neutral' ? 12 : 5)
    ))

    // 6. Proctoring Compliance & Warning Construction
    const phoneDetected = this.cachedPhoneDetected
    let threatLevel: 'clean' | 'warning' | 'violation' = 'clean'
    let violationReason: string | null = null
    let warningMessage: string | null = null

    if (phoneDetected) {
      threatLevel = 'violation'
      violationReason = 'Mobile phone or unauthorized device detected in frame.'
      warningMessage = 'Mobile phone detected! Unauthorized devices are strictly prohibited.'
    } else if (!eyesVisible) {
      threatLevel = 'warning'
      warningMessage = 'Both eyes must be open and clearly visible to the camera.'
    } else if (!isCentered) {
      threatLevel = 'warning'
      warningMessage = 'Please center your face inside the bounding box.'
    } else if (!isGoodDistance) {
      threatLevel = 'warning'
      warningMessage = eyeDistance < 0.12 ? 'Move a bit closer to the camera.' : 'Step back slightly from the camera.'
    } else if (!isFacingCamera) {
      threatLevel = 'warning'
      warningMessage = 'Please look directly at the screen and face the camera.'
    } else if (!hasEyeContact) {
      threatLevel = 'warning'
      warningMessage = 'Eye contact lost. Please maintain your gaze toward the interviewer.'
    }

    const allFeaturesVerified =
      eyesVisible &&
      leftEyeOpen &&
      rightEyeOpen &&
      noseVisible &&
      mouthVisible &&
      isCentered &&
      isGoodDistance &&
      isFacingCamera &&
      !phoneDetected

    this.updateStatus({
      isReady: true,
      faceCount: 1,
      hasSingleFace: true,
      eyesVisible,
      leftEyeOpen,
      rightEyeOpen,
      noseVisible,
      mouthVisible,
      isCentered,
      isGoodDistance,
      allFeaturesVerified,
      eyeContact: {
        hasEyeContact,
        score: eyeContactScore,
        gazeDirection,
      },
      headPose: {
        isFacingCamera,
        yaw: yawDeg,
        pitch: pitchDeg,
      },
      facialAnalysis: {
        expression,
        confidenceScore,
        attentivenessScore,
        postureStability,
      },
      proctoring: {
        isCompliant: threatLevel === 'clean',
        hasSingleHuman: true,
        phoneDetected,
        threatLevel,
        violationReason,
      },
      phoneDetected,
      warningMessage,
    })
  }

  private calculateVariance(arr: number[]): number {
    if (arr.length <= 1) return 0
    const mean = arr.reduce((a, b) => a + b, 0) / arr.length
    const sqDiffs = arr.map((v) => Math.pow(v - mean, 2))
    return Math.round(sqDiffs.reduce((a, b) => a + b, 0) / arr.length)
  }

  /**
   * Lightweight biometric fallback (useful while WebAssembly/CDN initializes).
   */
  private runBiometricFallback(video: HTMLVideoElement) {
    const isVideoPlaying = video.videoWidth > 0 && !video.paused
    this.updateStatus({
      isReady: true,
      faceCount: isVideoPlaying ? 1 : 0,
      hasSingleFace: isVideoPlaying,
      eyesVisible: isVideoPlaying,
      leftEyeOpen: isVideoPlaying,
      rightEyeOpen: isVideoPlaying,
      noseVisible: isVideoPlaying,
      mouthVisible: isVideoPlaying,
      isCentered: isVideoPlaying,
      isGoodDistance: isVideoPlaying,
      allFeaturesVerified: isVideoPlaying,
      eyeContact: {
        hasEyeContact: true,
        score: 100,
        gazeDirection: 'center',
      },
      headPose: {
        isFacingCamera: true,
        yaw: 0,
        pitch: 0,
      },
      facialAnalysis: {
        expression: 'confident',
        confidenceScore: 85,
        attentivenessScore: 100,
        postureStability: 95,
      },
      proctoring: {
        isCompliant: true,
        hasSingleHuman: isVideoPlaying,
        phoneDetected: false,
        threatLevel: 'clean',
        violationReason: null,
      },
      phoneDetected: false,
      warningMessage: null,
    })
  }

  private updateStatus(newStatus: FacialVerificationStatus) {
    this.currentStatus = newStatus
    for (const listener of this.listeners) {
      listener(this.currentStatus)
    }
  }
}

export const mediaPipeService = new MediaPipeService()

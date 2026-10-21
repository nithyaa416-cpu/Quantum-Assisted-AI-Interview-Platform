# Pending Tasks — Quantum-Assisted AI Interview Platform

> Last updated: 2026-09-25

---

## 🎯 Active Milestone: Interview Flow & Resume Architecture Redesign

- [x] **Task 1**: Password reset — verify user exists + add OTP verification to forget password flow
- [x] **Task 2**: Multi-Resume Support — Remove auto-deactivation so users can store multiple resumes and pick which one to use
- [x] **Task 3**: Move Target Role to Interview Setup & Add Job Description (JD) Box:
  - Add Target Role input/selector directly into `/interview/new`
  - Add Job Description textarea in `/interview/new`
  - Add Resume dropdown selector in `/interview/new`
  - Remove standalone Target Roles link from sidebar navigation & dashboard quick actions
  - **Just-in-Time Resume Extraction**: Resume text/skills are NOT extracted on upload; instead, extraction runs dynamically on the selected resume right when starting the interview.
  - Dashboard stat cards updated to show Resumes and Questions Answered instead of premature global profile skills/roles.
- [x] **Task 4**: Backend Interview Session Enhancement — Added `job_description` (text) and `resume` (FK to Resume) to `InterviewSession` model and migration `0003_interviewsession_job_description_and_more.py`
- [x] **Task 5**: DOCX/DOC Resume Support — Added Word document (.docx, .doc) text extraction to parser pipeline + frontend dropzone support (PDF, DOCX, DOC)

---

## 🔴 AI Interview Core Logic

- [x] **Task 6**: Follow-up context reconstruction — Fixed `_build_context()` in `interview_views.py` using `find_question_in_bank()` to restore `follow_ups` & `harder_follow_up`, and wired adaptive triggers in `interview_engine.py` for weak & strong responses
- [x] **Task 7**: Remove hardcoded 13-turn cap in `SubmitResponseView` — dynamically calculate total from `PHASE_QUESTION_COUNTS` across session types (coding: 5, technical: 13, hr: 11, project: 12, mixed: 13) and properly signal `should_end_interview`
- [x] **Task 8**: Connect JD + Selected Resume to Question Generation — Tailor interview questions using candidate's chosen resume and pasted Job Description in `ai_services.py` and `interview_engine.py`
- [x] **Task 9**: Interactive 1-on-1 Meeting Interview Style — Transformed static interview UI into a live 1-on-1 meeting experience (`MeetingRoom.tsx`) with animated 3D AI avatar (`MeetingAvatar.tsx`), candidate camera preview (`CandidateVideoTile.tsx`), proctoring shield (`ProctoringShield.tsx`), hands-free speech recognition & edge-tts synthesis

---

## 🟡 Student Profile & Planning

- [ ] **Task 10**: Add `preparation_time` field to `StudentProfile` (diagram says "Set Preparation Time")
- [ ] **Task 11**: Extract company names from resume experience section
- [ ] **Task 12**: Celery task to periodically clean up expired/verified OTPs

---

## ⚛️ Quantum QAOA Integration & Preparation Planner

- [ ] **Task 13**: QAOA Preparation Scheduler Service (`apps/preparation/quantum_optimizer.py`):
  - Formulate student preparation roadmap as a Quadratic Unconstrained Binary Optimization (QUBO) problem
  - Objective: maximize topic priority weights and interview weakness coverage within candidate time budget (days/daily hours) subject to topic prerequisites
  - Implement parameterized quantum circuit via Qiskit + `AerSimulator` (with classical fallback)
  - Output ground-state energy (`qaoa_energy`), circuit depth, and optimal topic sequence to `PreparationPlan` and `PracticeModule` models
- [ ] **Task 14**: Connect Post-Interview Assessment Weaknesses to Quantum Scheduler:
  - Extract identified `SkillGap` records from completed interview sessions
  - Feed penalty weights into QAOA objective function so the quantum planner dynamically prioritizes topics where candidate struggled in real interviews
- [ ] **Task 15**: Frontend Quantum Roadmap & Metrics Dashboard (`PreparationPage.tsx`):
  - Interactive daily module timeline showing topic, hours, subtopics, and practice question types
  - Quantum metrics badge card displaying QAOA Energy loss, circuit depth, and convergence score

---

## 👁️ Real-Time MediaPipe Proctoring & Object Detection

- [ ] **Task 16**: Strict Single Human Proctoring:
  - MediaPipe Face Mesh & object detection: Enforce exactly 1 human in camera frame
  - Real-time alarms for 0 persons (candidate left camera) and >1 persons (unauthorized proxy/helper in room)
- [ ] **Task 17**: Mobile Phone & Unauthorized Device Detection:
  - Real-time vision-based object detector (COCO-SSD / device detector) tracking camera feed
  - Flag presence of mobile phones (`cell phone`), books, or handheld devices with immediate proctoring violation strike
- [ ] **Task 18**: Behavioral Analytics Tracking:
  - Real-time eye contact percentage, gaze direction (center/left/right/down/up)
  - Head pose alignment (yaw & pitch stability)
  - Facial expression & confidence index (calm, confident, smiling, tense)

---

## 📊 Comprehensive Assessment Report & Behavioral Analysis Modules

- [ ] **Task 19**: Behavioral & Speech Metrics Collector (`frontend/src/utils/interviewAnalyticsCollector.ts`):
  - Aggregate facial metrics: Eye contact %, posture stability, attentiveness score
  - Aggregate voice metrics: Speech fluency (WPM, pause/silence ratio), pitch modulation & dynamic range via Web Audio API frequency analysis
  - Composite candidate Confidence Score (weighted blend of voice stability, eye contact, and posture)
  - Proctoring integrity audit: Count of phone detections, multi-human incidents, tab switches
- [ ] **Task 20**: Backend Assessment & SkillGap Generator (`backend/apps/assessments/services/report_generator.py`):
  - Automated report generation triggered upon session completion (`POST /api/sessions/{id}/end/`)
  - Score dimensions: Technical, Communication, Behavioural, Problem Solving, Overall
  - Populate structured `speech_metrics` and `behavioural_metrics`
  - Generate personalized strengths, improvement recommendations, and targeted `SkillGap` records
- [ ] **Task 21**: Rich Post-Interview Assessment Report UI (`InterviewHistoryPage.tsx`):
  - Visual readiness score & badges
  - Dedicated Behavioral & Speech Analytics tab (Eye contact gauge, Voice fluency meter, Pitch modulation bar, Confidence index)
  - Proctoring compliance summary
  - Direct "Recalibrate Quantum Preparation Plan" action button connecting to QAOA planner


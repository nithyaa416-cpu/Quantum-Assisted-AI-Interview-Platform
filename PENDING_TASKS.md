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
- [ ] **Task 4 (On Hold)**: Backend Interview Session Enhancement — Add `job_description` (text) and `resume` (FK) to `InterviewSession` model and migration
- [x] **Task 5**: DOCX/DOC Resume Support — Added Word document (.docx, .doc) text extraction to parser pipeline + frontend dropzone support (PDF, DOCX, DOC)

---

## 🔴 AI Interview Core Logic

- [ ] **Task 6**: Follow-up context reconstruction — Fix `_build_context()` in `interview_views.py` which sets `follow_ups: []` so adaptive follow-ups can trigger
- [ ] **Task 7**: Remove hardcoded 13-turn cap in `SubmitResponseView` — dynamically calculate total from `PHASE_QUESTION_COUNTS`
- [ ] **Task 8**: Connect JD + Selected Resume to Question Generation — Tailor interview questions using candidate's chosen resume and pasted Job Description
- [ ] **Task 9**: Interactive 1-on-1 Meeting Interview Style — Transform the static interview UI into a live 1-on-1 meeting experience with an interactive AI avatar, conversational audio/speech animation, and video meeting feel instead of a static form

---

## 🟡 Student Profile & Planning

- [ ] **Task 10**: Add `preparation_time` field to `StudentProfile` (diagram says "Set Preparation Time")
- [ ] **Task 11**: Extract company names from resume experience section
- [ ] **Task 12**: Celery task to periodically clean up expired/verified OTPs

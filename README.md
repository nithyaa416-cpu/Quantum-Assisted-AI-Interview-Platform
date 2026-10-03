# Quantum-Assisted AI Interview Intelligence and Placement Readiness Platform

> **QAIP** — A personalised, adaptive AI interview preparation platform for college students preparing for placement drives. Each student is evaluated individually. No student ranking or comparison exists.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Technology Stack](#2-technology-stack)
3. [Project Structure](#3-project-structure)
4. [What Has Been Built](#4-what-has-been-built)
5. [Database Models](#5-database-models)
6. [API Reference](#6-api-reference)
7. [Frontend Pages & Components](#7-frontend-pages--components)
8. [How to Run](#8-how-to-run)
9. [Test Results](#9-test-results)
10. [What Is Pending](#10-what-is-pending)

---

## 1. Project Overview

QAIP helps individual students prepare for placement interviews by:

- Conducting personalised adaptive multi-turn AI interviews (HR, Technical, Project, Coding)
- Analysing uploaded resumes to extract skills, projects, education and experience
- Identifying skill gaps based on target roles
- Generating quantum-optimised (QAOA) preparation plans
- Providing detailed post-interview assessment reports

**Core principle:** Every feature is scoped to the individual student. No student is ranked, compared, or scored against others.

---

## 2. Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React 18 + TypeScript + Tailwind CSS + Vite |
| Backend (core) | Django 4.2 + Django REST Framework |
| Auth | JWT (djangorestframework-simplejwt) |
| Database | SQLite (dev) / PostgreSQL (production) |
| Cache / Queue | Redis + Celery (configured, not yet active) |
| Resume parsing | pdfminer.six + custom NLP pipeline |
| AI Interviewer | Rule-based adaptive engine (LLM-ready interface) |
| Quantum (Phase 6) | Qiskit + QAOA (planned) |
| Deployment | Docker + Nginx (planned) |

---

## 3. Project Structure

```
main_project/
├── backend/                        # Django backend
│   ├── config/
│   │   ├── settings/
│   │   │   ├── base.py
│   │   │   ├── development.py      # USE_SQLITE=True for local dev
│   │   │   └── production.py
│   │   ├── urls.py                 # Root URL config
│   │   ├── celery.py
│   │   └── wsgi.py
│   ├── apps/
│   │   ├── accounts/               # Auth, user, student profile
│   │   ├── resumes/                # Resume upload, parsing, target roles
│   │   │   └── parser/             # PDF extraction + NLP pipeline
│   │   ├── sessions/               # Interview sessions, questions, responses
│   │   │   ├── interview_engine.py # Adaptive question selection logic
│   │   │   ├── interview_views.py  # AI interviewer REST endpoints
│   │   │   └── question_bank.py    # Curated question bank (200+ questions)
│   │   ├── assessments/            # Scores, skill gaps, coding submissions
│   │   └── preparation/            # Preparation plans, practice modules
│   ├── core/                       # Shared permissions, pagination, exceptions
│   ├── requirements.txt
│   ├── manage.py
│   ├── pytest.ini
│   ├── .env                        # Local env (gitignored)
│   └── .env.example
│
├── frontend/                       # React + TypeScript frontend
│   ├── src/
│   │   ├── pages/                  # Route-level page components
│   │   ├── components/
│   │   │   ├── auth/               # Login/register shell
│   │   │   ├── layout/             # Sidebar, TopBar, AppLayout, ProtectedRoute
│   │   │   ├── interview/          # Interview UI components
│   │   │   ├── resume/             # Upload, status badge, skills editor
│   │   │   ├── target-role/        # Domain badge, catalogue picker, skill gap chart
│   │   │   └── ui/                 # Shared: Button, Card, Input, Badge, Spinner...
│   │   ├── hooks/                  # React Query hooks per domain
│   │   ├── services/               # Axios API service layer
│   │   ├── store/                  # Zustand auth store
│   │   ├── types/                  # TypeScript interfaces
│   │   └── utils/                  # Error extraction helpers
│   ├── package.json
│   ├── tailwind.config.js
│   └── vite.config.ts              # Proxies /api → localhost:8000
│
├── start.bat                       # Double-click to start both servers
└── README.md
```

---

## 4. What Has Been Built

### Phase 1 — Database & Authentication ✅

**Backend:**
- Custom `CustomUser` model using email (not username) as login
- `StudentProfile` auto-created on registration via `post_save` signal
- JWT auth: register, login, logout (token blacklist), refresh, `/me`
- Password reset endpoint (no email required — dev mode)
- All 12 database models with migrations applied

**Frontend:**
- Login page with inline error display and "Forgot password?" flow
- Registration page with live password strength checklist
- Password reset flow (3 steps: email → new password → confirm)
- JWT stored in Zustand + localStorage, auto-refresh on 401
- Protected routes redirect unauthenticated users to `/login`

---

### Phase 2 — Frontend UI Shell ✅

- Dark-themed professional design (slate/indigo palette)
- Collapsible sidebar navigation
- Sticky topbar with user avatar and initials
- Dashboard with stats row, quick actions, recent sessions, performance snapshot
- Profile page with tag-input for skills and target roles
- Consistent JSON response envelope `{ success, data }` / `{ success, error }`
- `react-hot-toast` notifications on all actions
- Lazy-loaded pages (code splitting via Vite)

---

### Phase 3 — Resume Intelligence ✅

**Backend parser pipeline (`apps/resumes/parser/`):**

| File | Purpose |
|---|---|
| `pdf_extractor.py` | pdfminer.six — extracts raw text from PDF |
| `section_detector.py` | Regex-based section header detection |
| `extractors.py` | Contact, skills, education, experience, projects, certifications |
| `skill_ontology.py` | 200+ skills across 9 categories with normalisation map |
| `pipeline.py` | Orchestrates all steps; runs in background thread on upload |

**API endpoints (`/api/resumes/`):**

| Method | URL | Purpose |
|---|---|---|
| POST | `/api/resumes/upload/` | Upload PDF, trigger async parse |
| GET | `/api/resumes/` | List all resumes |
| GET | `/api/resumes/{id}/` | Full detail with extracted data |
| PATCH | `/api/resumes/{id}/` | Manually correct extracted data |
| DELETE | `/api/resumes/{id}/` | Delete resume + file |
| GET | `/api/resumes/{id}/status/` | Poll parse progress |
| POST | `/api/resumes/{id}/parse/` | Re-trigger parsing |
| GET | `/api/resumes/{id}/skills/` | Skills grouped by category |
| GET | `/api/resumes/active/summary/` | Active resume summary |

**Frontend — Resumes page:**
- Drag-and-drop PDF upload with client-side validation
- Live parse status badge (pending → processing → completed/failed)
- 2-second auto-polling while parsing is in progress
- Tabbed detail view: Skills / Projects / Education / Experience
- Editable skill tags with category colour coding
- ParseStatusBadge, SkillsEditor, UploadDropzone components

---

### Phase 4 — Target Role Module ✅

**Backend (`apps/resumes/role_catalogue.py` + `target_role_views.py`):**

13 curated roles: Software Developer, Python Developer, Java Developer, Data Analyst, Machine Learning Engineer, AI Engineer, Frontend Developer, Backend Developer, Full Stack Developer, DevOps Engineer, Data Engineer, Mobile Developer, Cybersecurity Analyst.

Each role has:
- `required_skills` — used for skill-gap analysis
- `interview_topics` — will drive AI interview questions
- `coding_topics` — will drive coding assessments
- `aliases` — auto-normalised (typing "sde" stores "Software Developer")

**API endpoints (`/api/target-roles/`):**

| Method | URL | Purpose |
|---|---|---|
| GET | `/api/target-roles/catalogue/` | Full catalogue with `?q=` search and `?domain=` filter |
| GET/POST | `/api/target-roles/` | List / add student's roles |
| GET/PATCH/DELETE | `/api/target-roles/{id}/` | Detail with catalogue metadata |
| POST | `/api/target-roles/{id}/set-primary/` | Set as primary (only one allowed) |
| GET | `/api/target-roles/primary/` | Get current primary role |
| GET | `/api/target-roles/skill-gap/` | Required vs student skills comparison |

**Key behaviours:**
- First role auto-becomes primary
- Deleting primary auto-promotes next role
- All changes sync `StudentProfile.target_roles` JSON field
- Skill gap merges profile skills + resume parsed skills

**Frontend — Target Roles page:**
- Searchable role catalogue with domain filter pills
- Custom role entry (typing any name not in catalogue)
- Role cards with expandable interview topics, coding topics, required skills
- Primary role banner with crown indicator
- Skill gap analysis panel with coverage ring + present/missing skills

---

### Phase 5 — AI Interviewer ✅

**Backend (`apps/sessions/`):**

**`question_bank.py`** — 200+ curated questions across:
- Warmup (3 questions)
- Technical by domain × difficulty: software engineering, backend, frontend, data science, ML/AI, devops (40+ questions)
- HR/Behavioural (7 questions)
- Project discussion (4 questions)
- Closing (2 questions)

Each question has `follow_ups` (weak answer) and `harder_follow_up` (strong answer).

**`interview_engine.py`** — Adaptive decision logic:
- Weak answer (score < 0.35) → follow-up clarification
- Strong answer (score ≥ 0.65) → harder follow-up (50% chance)
- Adjusts question difficulty based on last 2 answers' average
- Tracks asked questions — no repeats within a session
- Auto-advances phase: warmup → technical → project → HR → closing

**`interview_views.py`** — REST endpoints at `/api/interview/`:

| Method | URL | Purpose |
|---|---|---|
| POST | `/api/interview/sessions/` | Create session + generate Q1 immediately |
| GET | `/api/interview/sessions/` | List sessions |
| GET | `/api/interview/sessions/{id}/` | Full state with all turns |
| POST | `/api/interview/sessions/{id}/respond/` | Submit answer → evaluate → return next Q |
| POST | `/api/interview/sessions/{id}/end/` | End session |
| GET | `/api/interview/sessions/{id}/history/` | Full Q&A transcript |

**Answer evaluation:** Keyword-coverage heuristic (0.0–1.0 score). LLM-ready — swap `evaluate_answer_quality()` to replace.

**Frontend — Interview module:**

| Component | Purpose |
|---|---|
| `SessionSetup` | Pre-interview config: type, difficulty, target role |
| `QuestionCard` | Displays question with TTS read-aloud (🔊 button) |
| `AnswerArea` | **Voice-first**: big mic button, live transcript, text fallback |
| `FeedbackPanel` | Score bar, AI feedback, adaptive continue button |
| `PhaseIndicator` | Visual phase progress (warmup → technical → project → HR → closing) |
| `InterviewTimer` | Session elapsed timer + per-question countdown |
| `InterviewPage` | Full session state machine |
| `InterviewHistoryPage` | Expandable Q&A transcript with per-turn scores |

**Voice input features:**
- Web Speech API for real-time transcription
- Live waveform animation while recording
- Fallback text input if mic unavailable
- Detailed mic fix guide for `audio-capture` error (Chrome/Edge/Windows steps)
- Text-to-Speech reads question aloud on click

---

## 5. Database Models

| Model | App | Table | Key Fields |
|---|---|---|---|
| `CustomUser` | accounts | `accounts_user` | email (login), full_name, UUID PK |
| `StudentProfile` | accounts | `accounts_student_profile` | user (1:1), college, skills (JSON), target_roles (JSON) |
| `Resume` | resumes | `resumes_resume` | file, parsed_data (JSON), parse_status, version |
| `TargetRole` | resumes | `resumes_target_role` | role_name, domain, is_primary |
| `InterviewSession` | sessions | `sessions_interview_session` | session_type, status, difficulty, started_at |
| `InterviewQuestion` | sessions | `sessions_interview_question` | turn_number, phase, question_text, expected_concepts (JSON) |
| `StudentResponse` | sessions | `sessions_student_response` | transcript, score (0.00–1.00), ai_feedback |
| `CodingSubmission` | assessments | `assessments_coding_submission` | language, code, test_results (JSON), overall_score |
| `Assessment` | assessments | `assessments_assessment` | overall_score, technical_score, communication_score... |
| `SkillGap` | assessments | `assessments_skill_gap` | skill_name, current_level, target_level, gap_score |
| `PreparationPlan` | preparation | `preparation_plan` | topic_weights (JSON), recommended_sequence (JSON), qaoa_energy |
| `PracticeModule` | preparation | `preparation_practice_module` | topic, scheduled_day, status, resources (JSON) |

---

## 6. API Reference

### Authentication (`/api/auth/`)

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/register` | Public | Register + get tokens |
| POST | `/login` | Public | Login + get tokens |
| POST | `/logout` | JWT | Blacklist refresh token |
| POST | `/refresh` | Public | Exchange refresh for access |
| GET | `/me` | JWT | Current user data |
| POST | `/reset-password/` | Public | Reset password by email |

### Profile (`/api/profile/`)

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET/PATCH/PUT | `/me` | JWT | Get / update student profile |

### Resumes (`/api/resumes/`)

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/` | JWT | List all resumes |
| POST | `/upload/` | JWT | Upload PDF → async parse |
| GET | `/active/summary/` | JWT | Active resume summary |
| GET | `/{id}/` | JWT | Full detail with parsed data |
| PATCH | `/{id}/` | JWT | Manually edit extracted data |
| DELETE | `/{id}/` | JWT | Delete resume |
| GET | `/{id}/status/` | JWT | Poll parse status |
| POST | `/{id}/parse/` | JWT | Re-trigger parsing |
| GET | `/{id}/skills/` | JWT | Skills grouped by category |
| GET/POST | `/target-roles/` | JWT | List / add target roles (legacy) |

### Target Roles (`/api/target-roles/`)

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/catalogue/` | JWT | All roles with `?q=` + `?domain=` |
| GET | `/primary/` | JWT | Current primary role |
| GET | `/skill-gap/` | JWT | Skill gap vs primary role |
| GET/POST | `/` | JWT | List / add student's roles |
| GET/PATCH/DELETE | `/{id}/` | JWT | Role detail / update / delete |
| POST | `/{id}/set-primary/` | JWT | Make this role primary |

### AI Interview (`/api/interview/`)

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET/POST | `/sessions/` | JWT | List / create+start session |
| GET | `/sessions/{id}/` | JWT | Full session state |
| POST | `/sessions/{id}/respond/` | JWT | Submit answer → get next Q |
| POST | `/sessions/{id}/end/` | JWT | End session |
| GET | `/sessions/{id}/history/` | JWT | Full Q&A transcript |

### Assessments (`/api/assessments/`)

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/` | JWT | List all assessments |
| GET | `/sessions/{session_id}/` | JWT | Assessment for a session |
| GET | `/skill-gaps/` | JWT | Student's skill gaps |
| GET | `/coding/` | JWT | Coding submissions |

### Preparation (`/api/preparation/`)

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/plans/` | JWT | List preparation plans |
| GET | `/plans/active/` | JWT | Current active plan |
| GET | `/modules/` | JWT | Practice modules |
| PATCH | `/modules/{id}/` | JWT | Update module status |

---

## 7. Frontend Pages & Components

### Pages

| Route | Page | Description |
|---|---|---|
| `/login` | `LoginPage` | Email/password login with inline errors + "Forgot password?" |
| `/register` | `RegisterPage` | Registration with live password strength checklist |
| `/dashboard` | `DashboardPage` | Stats, quick actions, recent sessions, performance snapshot |
| `/profile` | `ProfilePage` | Skills/roles tag editor, social links, college info |
| `/resumes` | `ResumesPage` | Upload + status polling + tabbed extracted data |
| `/target-roles` | `TargetRolePage` | Catalogue picker, role cards, skill gap analysis |
| `/interview/new` | `InterviewPage` | Session setup + live interview interface |
| `/interview/:id` | `InterviewPage` | Resume active interview |
| `/interview/history/:id` | `InterviewHistoryPage` | Full Q&A transcript with scores |
| `/preparation` | `PreparationPage` | Placeholder (Phase 6) |

### Shared UI Components (`src/components/ui/`)

`Button`, `Card`, `StatCard`, `Input`, `Badge`, `Spinner`, `PageLoader`, `EmptyState`, `ScoreRing`

### Interview Components (`src/components/interview/`)

`AnswerArea` (voice-first), `FeedbackPanel`, `InterviewTimer`, `PhaseIndicator`, `QuestionCard`, `SessionSetup`

### Resume Components (`src/components/resume/`)

`ParseStatusBadge`, `SkillsEditor`, `UploadDropzone`

### Target Role Components (`src/components/target-role/`)

`DomainBadge`, `RoleCataloguePicker`, `SkillGapChart`

---

## 8. How to Run

### Prerequisites
- Python 3.10+
- Node.js 18+

### Quick Start (SQLite — no PostgreSQL needed)

**Terminal 1 — Backend:**
```bash
cd "d:\7th sem\main_project\backend"
pip install -r requirements.txt
copy .env.example .env          # Windows
python manage.py migrate
python manage.py runserver
```
Backend runs at → **http://localhost:8000**

**Terminal 2 — Frontend:**
```bash
cd "d:\7th sem\main_project\frontend"
npm install
npm run dev
```
Frontend runs at → **http://localhost:3000**

### Or: double-click `start.bat` in the project root to launch both.

### Switch to PostgreSQL (production)
```env
# In backend/.env
USE_SQLITE=False
DATABASE_NAME=qaip_db
DATABASE_USER=postgres
DATABASE_PASSWORD=your-password
```

### Password Requirements
- Minimum 8 characters
- At least one number
- Not all numeric
- Not a commonly used password (e.g. avoid `Test1234`, `Password1`)
- Example valid password: `YourName@2024`

### If login fails
Open http://localhost:8000/admin/ — if it loads, the backend is running. If not, start it first.

Use **Forgot password?** on the login page to reset without email.

---

## 9. Test Results

All backend tests pass:

```
accounts/tests.py         — 27 tests  ✅  (registration, login, logout, profile)
resumes/tests.py          — 33 tests  ✅  (upload, parse, edit, delete, skills, parser unit tests)
resumes/tests_target_roles.py — 34 tests ✅  (catalogue, CRUD, set-primary, skill-gap)
─────────────────────────────────────────
Total                       94 tests  ✅  all passing
```

TypeScript: **0 errors** (`npx tsc --noEmit`)  
Production build: **✅** (`npx vite build` — ~4 seconds, 21 chunks)

---

## 10. What Is Pending

| Phase | Module | Status |
|---|---|---|
| Phase 6 | LLM integration (replace rule-based engine with real LLM calls) | ⏳ Pending |
| Phase 6 | Whisper speech-to-text (server-side transcription) | ⏳ Pending |
| Phase 6 | QAOA preparation plan generator (Qiskit) | ⏳ Pending |
| Phase 7 | Final scoring & assessment report generation | ⏳ Pending |
| Phase 7 | Coding round (Monaco Editor + sandboxed execution) | ⏳ Pending |
| Phase 8 | Behavioural analysis (OpenCV + MediaPipe + YOLO) | ⏳ Pending |
| Phase 9 | Docker + Nginx deployment configuration | ⏳ Pending |
| Phase 9 | PostgreSQL production setup | ⏳ Pending |
| — | Celery async tasks (resume parsing already uses threads) | ⏳ Pending |
| — | Email verification / OTP (model exists, flow not wired) | ⏳ Pending |

### Architecture decisions made for future LLM integration

The interview engine is designed as a **drop-in replacement** point:

- `evaluate_answer_quality(answer, expected_concepts)` → replace body with LLM call
- `build_ai_feedback(question, answer, concepts, score, phase)` → replace with LLM narrative
- `AdaptiveInterviewEngine.decide_next_turn()` → replace `_pick_question()` with LLM generation

No structural changes needed when adding real LLM support.

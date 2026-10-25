// ─── Auth ────────────────────────────────────────────────────────────────────

export interface User {
  id: string
  email: string
  full_name: string
  is_active: boolean
  date_joined: string
}

export interface Tokens {
  access: string
  refresh: string
}

export interface AuthResponse {
  user: User
  tokens: Tokens
}

// ─── Student Profile ──────────────────────────────────────────────────────────

export interface StudentProfile {
  id: string
  email: string
  full_name: string
  college: string
  graduation_year: number | null
  phone: string
  bio: string
  skills: string[]
  target_roles: string[]
  linkedin_url: string
  github_url: string
  avatar: string | null
  created_at: string
  updated_at: string
}

export interface ProfileUpdatePayload {
  college?: string
  graduation_year?: number | null
  phone?: string
  bio?: string
  skills?: string[]
  target_roles?: string[]
  linkedin_url?: string
  github_url?: string
}

// ─── API envelope ─────────────────────────────────────────────────────────────

export interface ApiSuccess<T> {
  success: true
  data: T
}

export interface ApiError {
  success: false
  error: {
    code: string
    message: string
    details: Record<string, string[]>
  }
}

export type ApiResponse<T> = ApiSuccess<T> | ApiError

// ─── Auth forms ───────────────────────────────────────────────────────────────

export interface RegisterFormData {
  full_name: string
  email: string
  password: string
  confirm_password: string
  otp?: string
}


export interface LoginFormData {
  email: string
  password: string
}

// ─── Target Roles ─────────────────────────────────────────────────────────────

export interface TargetRole {
  id: string
  role_name: string
  domain: string
  is_primary: boolean
  created_at: string
}

export interface TargetRoleDetail extends TargetRole {
  required_skills: string[]
  interview_topics: string[]
  coding_topics: string[]
  role_description: string
}

export interface CreateTargetRolePayload {
  role_name: string
  domain?: string
  is_primary?: boolean
}

export interface RoleCatalogueEntry {
  display_name: string
  domain: string
  description: string
  required_skills: string[]
  interview_topics: string[]
  coding_topics: string[]
  aliases: string[]
}

export interface SkillGapResult {
  role: TargetRoleDetail
  required_skills: string[]
  present_skills: string[]
  missing_skills: string[]
  gap_percentage: number
  coverage: number
  interview_topics: string[]
  coding_topics: string[]
}

// ─── Resume ───────────────────────────────────────────────────────────────────

export type ParseStatus = 'pending' | 'processing' | 'completed' | 'failed'

export interface ResumeSkill {
  name: string
  category: string
  confidence: 'high' | 'medium' | 'low'
}

export interface ResumeProject {
  title: string
  description: string
  technologies: string[]
  url: string
}

export interface ResumeEducation {
  degree: string
  institution: string
  start_year: string
  end_year: string
  gpa: string
}

export interface ResumeExperience {
  role: string
  company: string
  date_range: string
  description: string[]
  technologies: string[]
}

export interface ResumeCertification {
  name: string
  year: string
}

export interface ResumeContact {
  name: string
  email: string
  phone: string
  linkedin: string
  github: string
}

export interface ResumeListItem {
  id: string
  student_name: string
  original_filename: string
  file_url?: string
  parse_status: ParseStatus
  is_parsed: boolean
  parsed_at: string | null
  version: number
  is_active: boolean
  skills_count: number
  created_at: string
}

export interface ResumeDetail extends ResumeListItem {
  parse_error: string
  raw_text?: string
  contact: ResumeContact
  skills: ResumeSkill[]
  projects: ResumeProject[]
  education: ResumeEducation[]
  experience: ResumeExperience[]
  certifications: ResumeCertification[]
  summary: string
}

export interface ResumeParseStatus {
  id: string
  parse_status: ParseStatus
  parse_error: string
  is_parsed: boolean
  parsed_at: string | null
  skills_count: number
  projects_count: number
}

export interface ActiveResumeSummary {
  id: string
  original_filename: string
  parse_status: ParseStatus
  summary: string
  skills: ResumeSkill[]
  projects_count: number
  education_count: number
  experience_count: number
  word_count: number
}

export interface ParsedDataUpdate {
  skills?: ResumeSkill[]
  projects?: ResumeProject[]
  education?: ResumeEducation[]
  experience?: ResumeExperience[]
  certifications?: ResumeCertification[]
  summary?: string
}

// ─── Interview ────────────────────────────────────────────────────────────────

export interface InterviewQuestion {
  id: string
  text: string
  phase: 'warmup' | 'technical' | 'project' | 'hr' | 'closing' | 'coding'
  topic: string
  difficulty: 'easy' | 'medium' | 'hard'
  turn_number: number
  question_type?: 'situational' | 'technical' | 'conceptual' | 'coding' | 'behavioural'
  is_follow_up?: boolean
  follow_up_reason?: 'weak_answer' | 'strong_answer' | 'coding_result' | null
  answered?: boolean
  /** Sentinel value returned when interviewer is in the coding phase */
  is_coding_problem?: boolean
}

/** Result from submitting code during an interview session */
export interface InterviewCodingResult {
  submission_id: string
  status: string
  passed: number
  total: number
  score: number
  runtime_ms: number | null
  memory_kb: number | null
  results: Array<{
    test_case_id: string
    status: string
    stdout: string
    stderr: string
    passed: boolean
    time_ms: number | null
    memory_kb: number | null
    input: string | null
    expected_output: string | null
  }>
  follow_up_question?: {
    id: string
    text: string
    phase: string
    topic: string
    turn_number: number
  }
  next_question?: {
    id: string
    text: string
    phase: string
    topic: string
    turn_number: number
  }
  interview_complete?: boolean
}


export interface InterviewTurn {
  turn_number: number
  phase: string
  question: string
  topic: string
  difficulty: string
  question_type: string
  is_follow_up: boolean
  response: string | null
  score: number | null
  feedback: string | null
  answered: boolean
  response_time_seconds: number | null
}

export interface PhaseProgress {
  [phase: string]: { asked: number; total: number }
}

export interface InterviewSession {
  id: string
  session_type: string
  difficulty: string
  status: 'active' | 'completed' | 'created' | 'aborted'
  target_role: string | null
  started_at: string | null
  ended_at: string | null
  duration_seconds: number | null
  turn_count: number
  current_phase: string
  current_question: InterviewQuestion | null
  turns: InterviewTurn[]
  phase_progress: PhaseProgress
}

export interface InterviewListItem {
  id: string
  session_type: string
  difficulty: string
  status: string
  target_role: string | null
  turn_count: number
  answered_count: number
  avg_score?: number | null
  started_at: string | null
  ended_at: string | null
  duration_seconds: number | null
  created_at: string
  current_phase: string
}

export interface StartInterviewPayload {
  session_type: 'technical' | 'hr' | 'project' | 'coding' | 'mixed'
  difficulty: 'beginner' | 'intermediate' | 'advanced'
  duration_minutes?: number
  target_role_id?: string
  target_role_name?: string
  job_description?: string
  resume_id?: string
}

export interface SubmitResponseResult {
  response_saved: {
    question_id: string
    score: number
    feedback: string
  }
  next_question: InterviewQuestion | null
  interview_complete: boolean
  phase_progress: PhaseProgress
}

// ─── Sessions ─────────────────────────────────────────────────────────────────

export interface SessionSummary {
  id: string
  session_type: string
  status: string
  difficulty: string
  target_role_name: string | null
  question_count: number
  answered_count?: number
  started_at: string | null
  ended_at: string | null
  duration_seconds: number | null
  created_at: string
}

// ─── Assessments ──────────────────────────────────────────────────────────────

export interface Assessment {
  id: string
  session: string
  session_type?: string
  target_role?: string | null
  overall_score: number
  technical_score: number
  communication_score: number
  behavioural_score: number | null
  coding_score: number | null
  problem_solving_score: number
  strengths: string[]
  improvement_areas: Array<{ area: string; priority: string; recommendation: string }>
  detailed_feedback?: {
    technical?: string
    communication?: string
    behavioural?: string
    proctoring_summary?: {
      status?: string
      single_human_compliance?: string
      mobile_phone_detected?: boolean
      phone_incidents_count?: number
      multiple_faces_count?: number
      proctoring_strikes?: number
    }
    quantum_prep_recommendations?: string
  }
  speech_metrics?: {
    words_per_minute?: number
    total_words_spoken?: number
    speaking_duration_seconds?: number
    fluency_score?: number
    pitch_modulation_score?: number
    articulation_quality?: string
    pause_frequency?: string
  }
  behavioural_metrics?: {
    eye_contact_percentage?: number
    posture_stability_score?: number
    attentiveness_score?: number
    confidence_score?: number
    dominant_expression?: string
    single_human_compliance?: number
    phone_detected_incidents?: number
    multiple_faces_incidents?: number
    face_absence_incidents?: number
    proctoring_strikes?: number
    integrity_status?: string
  }
  generated_at: string
}

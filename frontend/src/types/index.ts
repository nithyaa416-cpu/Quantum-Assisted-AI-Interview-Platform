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
  follow_up_question: {
    id: string
    text: string
    phase: string
    topic: string
    turn_number: number
  }
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


// ─── Preparation & QAOA ────────────────────────────────────────────────────────

export interface ActivityPoolItem {
  id: string
  topic: string
  title: string
  category: 'coding' | 'technical' | 'system_design' | 'behavioral' | 'project'
  current_score: number
  target_score: number
  skill_gap_severity: number
  role_relevance: number
  selection_impact_estimate: number
  estimated_study_hours: number
  priority: 'high' | 'medium' | 'low'
  why_selected: string
  expected_outcome: string
  recommended_activities: string[]
  practice_exercises: string[]
  prerequisites: string[]
}

export interface InterviewTopicEvaluation {
  topic: string
  score_pct: number
  status: 'passed' | 'marginal' | 'unanswered' | 'low_score' | string
  priority?: 'high' | 'medium' | 'low' | string
  summary?: string
  reason?: string
  recommendation?: string
}

export interface InterviewMetrics {
  total_questions_asked: number
  questions_answered: number
  overall_score_pct: number
}

export interface FeedbackAnalysisData {
  has_mock_interview: boolean
  session_id: string | null
  target_role: {
    id: string | null
    role_name: string
    domain: string
  }
  interview_metrics?: InterviewMetrics
  strong_areas?: InterviewTopicEvaluation[]
  weak_areas?: InterviewTopicEvaluation[]
  strengths: string[]
  weaknesses: Array<{
    area: string
    priority: string
    score?: number
    recommendation: string
    question_context?: string
  }>
  activity_pool: ActivityPoolItem[]
  total_activities_available: number
  disclaimer: string
}

export interface PracticeModule {
  id: string
  plan: string
  activity_id: string
  topic: string
  sub_topics: string[]
  scheduled_day: number
  estimated_hours: number
  priority: 'high' | 'medium' | 'low'
  why_selected: string
  expected_outcome: string
  practice_exercises: string[]
  prerequisites: string[]
  order: number
  status: 'pending' | 'in_progress' | 'completed' | 'skipped'
  completed_at: string | null
  resources: Array<{ title: string; url: string; type: string }>
  is_completed: boolean
  created_at: string
}

export interface OptimizationMetadata {
  algorithm_used: string
  is_quantum: boolean
  num_qubits: number
  circuit_depth: number
  p_layers: number
  execution_time_ms: number
  qaoa_circuit_time_ms: number
  total_value: number
  total_hours: number
  budget_capacity: number
  repair_applied: boolean
  raw_solution?: {
    bitstring: string
    value: number
    hours: number
    is_feasible: boolean
  }
  top_measurement_states?: Array<{
    bitstring: string
    probability: number
    value: number
    hours: number
    is_feasible: boolean
  }>
  classical_comparison?: {
    classical_algorithm: string
    classical_optimal_value: number
    classical_hours: number
    classical_execution_time_ms: number
    qaoa_approximation_ratio: number
  }
  optimal_parameters?: {
    gamma: number[]
    beta: number[]
  }
}

export interface PreparationPlan {
  id: string
  target_role: string | null
  target_role_name: string | null
  session: string | null
  session_id: string | null
  preparation_days: number
  total_hours_budget: number
  daily_hours: number
  algorithm_used: string
  topic_weights: Record<string, number>
  recommended_sequence: Array<{
    day: number
    order: number
    topic: string
    title: string
    hours: number
    category: string
    priority: string
    why_selected: string
    expected_outcome: string
    practice_question_types: string[]
    sub_topics: string[]
  }>
  feedback_summary: {
    has_mock_interview: boolean
    session_id: string | null
    target_role: { id: string | null; role_name: string; domain: string }
    interview_metrics?: InterviewMetrics
    strong_areas?: InterviewTopicEvaluation[]
    weak_areas?: InterviewTopicEvaluation[]
    strengths: string[]
    weaknesses: any[]
    disclaimer: string
    total_activities_evaluated: number
    total_activities_selected: number
  }
  priority_areas: string[]
  optimization_metadata: OptimizationMetadata
  qaoa_energy: number | null
  circuit_depth: number | null
  is_active: boolean
  modules_count: number
  completed_modules: number
  practice_modules: PracticeModule[]
  generated_at: string
  updated_at: string
}

export interface GeneratePlanPayload {
  session_id?: string | null
  target_role_id?: string | null
  days_remaining: number
  daily_hours: number
  total_hours_budget?: number | null
  priority_areas?: string[]
  preferred_categories?: string[]
  force_algorithm?: 'qaoa' | 'classical'
}

export interface QuantumBenchmarkResult {
  problem_size_qubits: number
  total_budget_hours: number
  circuit_depth: number
  qaoa_execution_time_ms: number
  qaoa_circuit_time_ms: number
  qaoa_total_value: number
  qaoa_hours_scheduled: number
  qaoa_is_feasible: boolean
  repair_applied: boolean
  classical_comparison: {
    classical_algorithm: string
    classical_optimal_value: number
    classical_hours: number
    classical_execution_time_ms: number
    qaoa_approximation_ratio: number
  }
  top_measurement_states: Array<{
    bitstring: string
    probability: number
    value: number
    hours: number
    is_feasible: boolean
  }>
}

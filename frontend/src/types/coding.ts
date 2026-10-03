/**
 * TypeScript types for the Coding Interview module.
 * All types match the Django backend API response shape exactly.
 */

// ── Language ──────────────────────────────────────────────────────────────────

/** Frontend language descriptor. Backend maps id → Judge0 language_id. */
export interface CodingLanguage {
  /** Identifier sent to the backend: 'python' | 'java' | 'cpp' */
  id: 'python' | 'java' | 'cpp'
  /** Display name in the UI */
  name: string
  /** Monaco Editor language identifier */
  monacoLanguage: string
}

export const CODING_LANGUAGES: CodingLanguage[] = [
  { id: 'python', name: 'Python 3',  monacoLanguage: 'python' },
  { id: 'java',   name: 'Java',      monacoLanguage: 'java'   },
  { id: 'cpp',    name: 'C++ 17',    monacoLanguage: 'cpp'    },
]

// ── Problem ───────────────────────────────────────────────────────────────────

export interface CodingExample {
  input: string
  output: string
  explanation?: string
}

export interface CodingTestCase {
  id: string
  input_data: string
  expected_output: string
  order: number
}

/** Starter code per language key */
export type StarterCodeMap = {
  python: string
  java: string
  cpp: string
}

/** Lightweight problem — returned in the list endpoint */
export interface CodingProblemSummary {
  id: string
  title: string
  slug: string
  difficulty: 'easy' | 'medium' | 'hard'
  time_limit_seconds: number
  memory_limit_mb: number
}

/** Full problem — returned in the detail endpoint */
export interface CodingProblem extends CodingProblemSummary {
  description: string
  input_format: string
  output_format: string
  constraints: string[]
  examples: CodingExample[]
  starter_code: StarterCodeMap
  public_test_cases: CodingTestCase[]
}

// ── Execution result (single test case) ────────────────────────────────────────

export type ExecutionStatus =
  | 'accepted'
  | 'wrong_answer'
  | 'compilation_error'
  | 'runtime_error'
  | 'time_limit_exceeded'
  | 'memory_limit_exceeded'
  | 'internal_error'
  | 'pending'

export interface CodingExecutionResult {
  test_case_id: string
  status: ExecutionStatus
  stdout: string
  stderr: string
  time_ms: number | null
  memory_kb: number | null
  passed: boolean
  /** Only present for public test cases */
  input?: string | null
  /** Only present for public test cases */
  expected_output?: string | null
}

// ── Run Code ──────────────────────────────────────────────────────────────────

export interface CodingRunRequest {
  problem_id: string
  language: CodingLanguage['id']
  source_code: string
  /** Optional — links execution to an interview session */
  session_id?: string
}

export interface CodingRunResponse {
  overall_status: ExecutionStatus
  passed: number
  total: number
  runtime_ms: number | null
  memory_kb: number | null
  results: CodingExecutionResult[]
}

// ── Submit ────────────────────────────────────────────────────────────────────

export interface CodingSubmissionRequest {
  problem_id: string
  language: CodingLanguage['id']
  source_code: string
  session_id?: string
}

export interface CodingSubmissionResponse {
  submission_id: string
  status: ExecutionStatus
  passed: number
  total: number
  runtime_ms: number | null
  memory_kb: number | null
  score: number
  /** Safe results — hidden test case input/output are null */
  results: CodingExecutionResult[]
}

// ── Submission history entry ───────────────────────────────────────────────────

export interface CodingSubmissionHistoryItem {
  id: string
  problem_title: string
  language: string
  status: ExecutionStatus
  passed_count: number
  total_count: number
  runtime_ms: number | null
  memory_kb: number | null
  correctness_score: number | null
  overall_score: number | null
  pass_rate: number
  safe_results: CodingExecutionResult[]
  submitted_at: string
}

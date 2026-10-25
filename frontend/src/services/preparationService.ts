import api from './api'
import type {
  PreparationPlan,
  PracticeModule,
  FeedbackAnalysisData,
  GeneratePlanPayload,
  QuantumBenchmarkResult,
} from '@/types'

export const preparationService = {
  /**
   * Extract interview feedback analysis, strengths, weaknesses, and candidate activity pool
   */
  async getFeedbackAnalysis(sessionId?: string): Promise<FeedbackAnalysisData | null> {
    try {
      const url = sessionId
        ? `/api/preparation/feedback-analysis/?session_id=${encodeURIComponent(sessionId)}`
        : '/api/preparation/feedback-analysis/'
      const res = await api.get(url)
      return res.data?.data ?? null
    } catch (err) {
      console.error('Failed to fetch preparation feedback analysis:', err)
      return null
    }
  },

  /**
   * Generate a new QAOA-optimized preparation plan
   */
  async generatePlan(payload: GeneratePlanPayload): Promise<PreparationPlan> {
    const res = await api.post('/api/preparation/plans/generate/', payload)
    return res.data.data
  },

  /**
   * Fetch currently active preparation plan with modules
   */
  async getActivePlan(): Promise<PreparationPlan | null> {
    try {
      const res = await api.get('/api/preparation/plans/active/')
      return res.data?.data ?? null
    } catch {
      return null
    }
  },

  /**
   * List all preparation plans for candidate
   */
  async listPlans(): Promise<PreparationPlan[]> {
    try {
      const res = await api.get('/api/preparation/plans/')
      return res.data?.data ?? []
    } catch {
      return []
    }
  },

  /**
   * Fetch specific plan by UUID
   */
  async getPlanById(id: string): Promise<PreparationPlan | null> {
    try {
      const res = await api.get(`/api/preparation/plans/${id}/`)
      return res.data?.data ?? null
    } catch {
      return null
    }
  },

  /**
   * Regenerate an existing plan with updated options
   */
  async regeneratePlan(id: string, payload: Partial<GeneratePlanPayload>): Promise<PreparationPlan> {
    const res = await api.post(`/api/preparation/plans/${id}/regenerate/`, payload)
    return res.data.data
  },

  /**
   * Fetch practice modules for active plan (or specific plan)
   */
  async listModules(planId?: string): Promise<PracticeModule[]> {
    try {
      const url = planId ? `/api/preparation/modules/?plan_id=${planId}` : '/api/preparation/modules/'
      const res = await api.get(url)
      return res.data?.data ?? []
    } catch {
      return []
    }
  },

  /**
   * Update practice module completion status ('pending', 'in_progress', 'completed', 'skipped')
   */
  async updateModuleStatus(
    id: string,
    status: 'pending' | 'in_progress' | 'completed' | 'skipped'
  ): Promise<PracticeModule> {
    const res = await api.patch(`/api/preparation/modules/${id}/`, { status })
    return res.data.data
  },

  /**
   * Run live quantum vs classical benchmark
   */
  async runBenchmark(params?: {
    num_qubits?: number
    total_hours_budget?: number
    p_layers?: number
  }): Promise<QuantumBenchmarkResult | null> {
    try {
      const res = await api.post('/api/preparation/benchmark/', params ?? {})
      return res.data?.data ?? null
    } catch (err) {
      console.error('Benchmark execution error:', err)
      return null
    }
  },
}


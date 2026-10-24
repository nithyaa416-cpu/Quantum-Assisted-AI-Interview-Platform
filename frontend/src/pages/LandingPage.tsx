/**
 * LandingPage — High-Conversion, Interactive, and Ultra-Modern Landing Experience for QAIP.
 *
 * Features:
 * - Dynamic Tech Grid & Ambient Glowing Gradients
 * - Interactive Hero Simulator (Voice Examiner / Sandboxed Monaco IDE / AI Rubric)
 * - Interactive Target Role & Assessment Explorer
 * - Bento-Grid Features with Minimal, Curiosity-Inducing Copy
 * - Visual 4-Step Pipeline with Glow Connectors
 * - Quantum-Assisted QAOA Research Visualizer
 * - Interactive Quick Insights / FAQ
 * - Validated Contact Form & High-Impact CTA
 */

import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  MessageSquare, Code2, Brain, FileText, Target, TrendingUp,
  UserPlus, Mic, BarChart3, BookOpen, ChevronRight, ArrowRight,
  CheckCircle2, Send, AlertCircle, Atom, Sparkles, Zap, Shield,
  Terminal, Play, Check, ChevronDown, Layers, HelpCircle, Activity,
} from 'lucide-react'
import { clsx } from 'clsx'

import { PublicNavbar } from '@/components/landing/PublicNavbar'
import { PublicFooter } from '@/components/landing/PublicFooter'
import { Spinner } from '@/components/ui/Spinner'
import toast from 'react-hot-toast'

// ── Target Roles for Interactive Explorer ──────────────────────────────────────
const EXPLORER_ROLES = [
  {
    id: 'fullstack',
    title: 'Full Stack Engineer',
    category: 'Software Engineering',
    difficulty: 'Intermediate to Hard',
    rounds: ['System Architecture', 'React & Node.js', 'DSA: Graphs & DP', 'Project Defense', 'Behavioral'],
    skills: ['TypeScript', 'React', 'Node.js', 'PostgreSQL', 'Docker', 'REST/GraphQL'],
    sampleQuestion: 'How would you architect a distributed real-time notification service handling 100k events/sec?',
    color: 'from-blue-500 to-indigo-600',
  },
  {
    id: 'backend',
    title: 'Backend Systems Engineer',
    category: 'Distributed Systems',
    difficulty: 'Advanced',
    rounds: ['Concurrency & I/O', 'Database Indexing & Locks', 'DSA: Trees & Caching', 'Live Coding', 'HR'],
    skills: ['Python / Go', 'PostgreSQL', 'Redis', 'Kafka', 'Microservices', 'System Design'],
    sampleQuestion: 'Explain the difference between optimistic and pessimistic locking under high database contention.',
    color: 'from-purple-500 to-indigo-700',
  },
  {
    id: 'ai_ml',
    title: 'AI / ML Engineer',
    category: 'Machine Learning & Data',
    difficulty: 'Advanced',
    rounds: ['Math & Probability', 'Model Architecture', 'DSA: Arrays & Matrix Math', 'Model Serving', 'HR'],
    skills: ['PyTorch', 'TensorFlow', 'LLMs & RAG', 'Scikit-Learn', 'Vector DBs', 'Python'],
    sampleQuestion: 'How do you mitigate attention layer memory overhead in Transformers during long-context generation?',
    color: 'from-cyan-500 to-blue-600',
  },
  {
    id: 'devops',
    title: 'Cloud & DevOps Architect',
    category: 'Infrastructure',
    difficulty: 'Intermediate',
    rounds: ['Linux Internals', 'CI/CD Pipelines', 'DSA: Scripting & Shell', 'Kubernetes Cluster Recovery', 'HR'],
    skills: ['Kubernetes', 'Docker', 'Terraform', 'AWS/GCP', 'Prometheus', 'Linux'],
    sampleQuestion: 'Walk me through diagnosing a CrashLoopBackOff error caused by OOMKilled in a production pod.',
    color: 'from-emerald-500 to-teal-700',
  },
]

// ── Interactive FAQ Data ───────────────────────────────────────────────────────
const FAQS = [
  {
    q: 'How does the Voice AI Examiner conduct the interview?',
    a: 'QAIP utilizes neural speech synthesis paired with live speech recognition. The examiner speaks questions naturally and listens hands-free. It dynamically generates deep-dive follow-up questions tailored to your spoken answers.',
  },
  {
    q: 'Are coding problems executed live in a real sandbox?',
    a: 'Yes. QAIP embeds the full Monaco Editor (the engine powering VS Code) and executes code across Python, Java, and C++ inside an isolated, secure Judge0 sandbox with comprehensive test case verification.',
  },
  {
    q: 'What makes QAIP different from standard mock interview websites?',
    a: 'Unlike static question banks or random peer mock interviews, QAIP parses your actual resume to ask tailored questions, conducts voice interviews with automatic proctoring, and scores your answers with zero human bias.',
  },
  {
    q: 'What is the Quantum-Assisted component?',
    a: 'QAIP incorporates research exploring the Quantum Approximate Optimization Algorithm (QAOA) via Qiskit to mathematically model and optimize preparation paths, identifying the fastest route to bridge your specific skill gaps.',
  },
]

// ── Interactive Hero Live Demo ─────────────────────────────────────────────────
function InteractiveHeroDemo() {
  const [activeTab, setActiveTab] = useState<'voice' | 'coding' | 'rubric'>('voice')
  const [simulatedScore] = useState(9.4)

  return (
    <div className="relative group w-full max-w-xl mx-auto lg:max-w-none">
      {/* Dynamic ambient glow orb behind the mock */}
      <div className="absolute -inset-1 bg-gradient-to-r from-brand-500/30 via-purple-500/20 to-cyan-500/30 rounded-3xl blur-2xl opacity-75 group-hover:opacity-100 transition duration-1000 group-hover:duration-200 animate-pulse-slow" />

      {/* Main Container Card */}
      <div className="relative rounded-2xl bg-slate-900/90 border border-slate-700/60 shadow-2xl overflow-hidden backdrop-blur-xl">
        {/* Top Window Bar */}
        <div className="px-4 py-3 bg-slate-950/80 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-red-500/80 inline-block" />
            <span className="w-3 h-3 rounded-full bg-amber-500/80 inline-block" />
            <span className="w-3 h-3 rounded-full bg-emerald-500/80 inline-block" />
            <span className="text-[11px] font-mono text-slate-400 ml-2">qaip-interview-session-live.app</span>
          </div>

          <div className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-[10px] font-bold text-emerald-400">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
            LIVE SIMULATION
          </div>
        </div>

        {/* Interactive Mode Tabs */}
        <div className="grid grid-cols-3 bg-slate-950/40 p-1 border-b border-slate-800 text-xs font-semibold">
          <button
            type="button"
            onClick={() => setActiveTab('voice')}
            className={clsx(
              'py-2 px-3 rounded-lg flex items-center justify-center gap-2 transition-all',
              activeTab === 'voice'
                ? 'bg-brand-600 text-white shadow-md'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            )}
          >
            <Mic className="h-3.5 w-3.5" />
            <span>Voice AI</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('coding')}
            className={clsx(
              'py-2 px-3 rounded-lg flex items-center justify-center gap-2 transition-all',
              activeTab === 'coding'
                ? 'bg-brand-600 text-white shadow-md'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            )}
          >
            <Code2 className="h-3.5 w-3.5" />
            <span>Monaco IDE</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('rubric')}
            className={clsx(
              'py-2 px-3 rounded-lg flex items-center justify-center gap-2 transition-all',
              activeTab === 'rubric'
                ? 'bg-brand-600 text-white shadow-md'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            )}
          >
            <Sparkles className="h-3.5 w-3.5" />
            <span>Rubric AI</span>
          </button>
        </div>

        {/* Tab 1: Voice Examiner View */}
        {activeTab === 'voice' && (
          <div className="p-5 space-y-4 animate-fade-in">
            {/* Examiner Header */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-600 to-indigo-500 flex items-center justify-center text-white shadow-lg ring-2 ring-brand-400/40">
                  <Brain className="h-5 w-5 animate-pulse" />
                </div>
                <div>
                  <h4 className="text-sm font-bold text-slate-100 flex items-center gap-1.5">
                    AI Senior Examiner
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-brand-500/20 text-brand-300 font-normal">
                      Llama 3
                    </span>
                  </h4>
                  <p className="text-xs text-slate-400">Technical Round &bull; Distributed Systems</p>
                </div>
              </div>

              {/* Sound wave bars */}
              <div className="flex items-center gap-1 h-6 px-3 py-1 rounded-full bg-slate-950/70 border border-slate-800">
                {[0.4, 0.9, 0.6, 1.0, 0.5, 0.8, 0.3].map((h, i) => (
                  <span
                    key={i}
                    className="w-1 bg-brand-400 rounded-full"
                    style={{
                      height: `${h * 16}px`,
                      animation: `pulseRing 1.2s ease-in-out ${i * 0.15}s infinite alternate`,
                    }}
                  />
                ))}
              </div>
            </div>

            {/* Prompt Box */}
            <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 text-xs sm:text-sm text-slate-200 leading-relaxed">
              <div className="text-[10px] uppercase font-bold text-brand-400 tracking-wider mb-1 flex items-center gap-1">
                <MessageSquare className="h-3 w-3" /> Question Prompt
              </div>
              "How would you handle cache invalidation and race conditions in a distributed cluster using Redis and PostgreSQL?"
            </div>

            {/* Candidate Response Transcript */}
            <div className="p-3 rounded-xl bg-slate-900/80 border border-emerald-500/30 space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="flex items-center gap-1.5 text-emerald-400 font-semibold">
                  <Mic className="h-3.5 w-3.5 animate-pulse" /> Listening Live
                </span>
                <span className="text-[11px] text-slate-500 font-mono">10s Silence Auto-Submit</span>
              </div>
              <p className="text-xs text-slate-300 italic leading-relaxed">
                "I would implement the Cache-Aside pattern combined with transactional outbox events to guarantee consistency..."
              </p>
            </div>
          </div>
        )}

        {/* Tab 2: Monaco IDE View */}
        {activeTab === 'coding' && (
          <div className="p-4 space-y-3 animate-fade-in font-mono text-xs">
            <div className="flex items-center justify-between pb-2 border-b border-slate-800">
              <span className="text-slate-400 flex items-center gap-1.5">
                <Terminal className="h-3.5 w-3.5 text-brand-400" /> solution.py &bull; Python 3.10
              </span>
              <span className="text-emerald-400 font-semibold flex items-center gap-1">
                <Check className="h-3.5 w-3.5" /> Judge0 Ready
              </span>
            </div>

            <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 text-slate-300 leading-relaxed overflow-x-auto">
              <p className="text-purple-400">def <span className="text-blue-400">findMedianSortedArrays</span>(nums1, nums2):</p>
              <p className="text-slate-500 pl-4"># Binary search partition O(log(min(m, n)))</p>
              <p className="text-slate-300 pl-4">low, high = 0, len(nums1)</p>
              <p className="text-slate-300 pl-4"><span className="text-purple-400">while</span> low &lt;= high:</p>
              <p className="text-slate-300 pl-8">partitionX = (low + high) // 2</p>
              <p className="text-emerald-400 pl-8">return (maxLeft + minRight) / 2.0</p>
            </div>

            <div className="grid grid-cols-2 gap-2 text-[11px]">
              <div className="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/25 text-emerald-300 flex items-center justify-between">
                <span>Public Tests: 3/3 Passed</span>
                <span className="font-bold">✓ 100%</span>
              </div>
              <div className="p-2 rounded-lg bg-slate-800 border border-slate-700 text-slate-300 flex items-center justify-between">
                <span>Execution Time</span>
                <span className="font-bold text-brand-300">38ms</span>
              </div>
            </div>
          </div>
        )}

        {/* Tab 3: Rubric AI View */}
        {activeTab === 'rubric' && (
          <div className="p-5 space-y-4 animate-fade-in">
            <div className="flex items-center justify-between pb-2 border-b border-slate-800">
              <div>
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Evaluation Score</span>
                <div className="text-2xl font-black text-emerald-400 flex items-baseline gap-1">
                  {simulatedScore} <span className="text-xs text-slate-500 font-normal">/ 10</span>
                </div>
              </div>
              <span className="px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 text-xs font-bold">
                STRONG HIRE
              </span>
            </div>

            <div className="space-y-2.5">
              <div>
                <div className="flex justify-between text-xs text-slate-300 mb-1">
                  <span>Algorithmic Complexity &amp; Architecture</span>
                  <span className="font-bold text-brand-400">9.5/10</span>
                </div>
                <div className="h-1.5 rounded-full bg-slate-800 overflow-hidden">
                  <div className="h-full bg-brand-500 rounded-full w-[95%]" />
                </div>
              </div>
              <div>
                <div className="flex justify-between text-xs text-slate-300 mb-1">
                  <span>Edge-Case Handling &amp; Concurrency</span>
                  <span className="font-bold text-indigo-400">9.0/10</span>
                </div>
                <div className="h-1.5 rounded-full bg-slate-800 overflow-hidden">
                  <div className="h-full bg-indigo-500 rounded-full w-[90%]" />
                </div>
              </div>
            </div>

            <div className="p-3 rounded-xl bg-brand-500/10 border border-brand-500/20 text-xs text-brand-200 leading-relaxed">
              <strong>AI Feedback:</strong> Clear mastery of distributed cache invalidation and distributed locking mechanisms.
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

// ── Interactive Role Explorer ──────────────────────────────────────────────────
function RoleExplorer({ onSelectRole }: { onSelectRole: (role: string) => void }) {
  const [selectedIdx, setSelectedIdx] = useState(0)
  const current = EXPLORER_ROLES[selectedIdx]

  return (
    <div className="card p-6 sm:p-8 border-brand-500/20 relative overflow-hidden">
      <div className="flex flex-col md:flex-row gap-6 lg:gap-8 items-start">
        {/* Left: Role Buttons */}
        <div className="w-full md:w-1/3 space-y-2">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-400 block mb-2">
            Select Your Target Role
          </span>
          {EXPLORER_ROLES.map((role, idx) => (
            <button
              key={role.id}
              type="button"
              onClick={() => setSelectedIdx(idx)}
              className={clsx(
                'w-full text-left px-4 py-3 rounded-xl border transition-all flex items-center justify-between',
                selectedIdx === idx
                  ? 'bg-brand-600/20 border-brand-500/50 text-white font-bold ring-1 ring-brand-500/30'
                  : 'bg-surface border-surface-border text-slate-400 hover:text-slate-200 hover:bg-surface-hover'
              )}
            >
              <span className="text-sm">{role.title}</span>
              <ChevronRight className={clsx('h-4 w-4 transition-transform', selectedIdx === idx ? 'text-brand-400 translate-x-1' : 'text-slate-600')} />
            </button>
          ))}
        </div>

        {/* Right: Dynamic Role Preview */}
        <div className="w-full md:w-2/3 bg-slate-950/60 rounded-2xl p-5 border border-slate-800 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-slate-800">
            <div>
              <h3 className="text-lg font-bold text-slate-100">{current.title}</h3>
              <p className="text-xs text-brand-400 font-medium">{current.category} &bull; {current.difficulty}</p>
            </div>
            <button
              type="button"
              onClick={() => onSelectRole(current.title)}
              className="btn-primary text-xs px-4 py-2"
            >
              Start Role Mock <ArrowRight className="h-3.5 w-3.5" />
            </button>
          </div>

          {/* Rounds Breakdown */}
          <div>
            <span className="text-[11px] uppercase font-bold text-slate-400 tracking-wider block mb-2">
              Adaptive Interview Flow
            </span>
            <div className="flex flex-wrap gap-2">
              {current.rounds.map((round, i) => (
                <span
                  key={i}
                  className="px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-300 flex items-center gap-1.5"
                >
                  <span className="w-1.5 h-1.5 rounded-full bg-brand-400" />
                  {round}
                </span>
              ))}
            </div>
          </div>

          {/* Sample Question */}
          <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800">
            <span className="text-[10px] font-bold uppercase text-brand-400 tracking-wider block mb-1">
              Sample AI Question
            </span>
            <p className="text-xs sm:text-sm text-slate-200 italic">
              "{current.sampleQuestion}"
            </p>
          </div>

          {/* Skills Required */}
          <div>
            <span className="text-[11px] uppercase font-bold text-slate-400 tracking-wider block mb-2">
              Evaluated Competencies
            </span>
            <div className="flex flex-wrap gap-1.5">
              {current.skills.map((s, i) => (
                <span key={i} className="px-2 py-0.5 rounded-md bg-brand-500/10 text-brand-300 border border-brand-500/20 text-[11px]">
                  {s}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

// ── Main Landing Page ─────────────────────────────────────────────────────────
export default function LandingPage() {
  const navigate = useNavigate()
  const [openFaq, setOpenFaq] = useState<number | null>(0)

  const scrollTo = (id: string) => {
    document.querySelector(`#${id}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  return (
    <div className="min-h-screen bg-surface text-slate-100 selection:bg-brand-500 selection:text-white relative">
      <PublicNavbar />

      {/* ── 1. HERO SECTION ──────────────────────────────────────────────────── */}
      <section id="home" className="relative pt-28 pb-20 sm:pt-36 sm:pb-28 overflow-hidden tech-grid">
        {/* Ambient Gradient Backgrounds */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[450px] bg-gradient-to-tr from-brand-600/25 via-purple-600/15 to-cyan-500/20 rounded-full blur-[120px] pointer-events-none" />
        <div className="absolute top-1/3 -right-32 w-[350px] h-[350px] bg-indigo-500/10 rounded-full blur-[90px] pointer-events-none" />

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid lg:grid-cols-2 gap-12 lg:gap-14 items-center">
            {/* Left Column: Headline & Value Proposition */}
            <div className="text-center lg:text-left space-y-6">
              {/* Badge */}
              <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-brand-500/10 border border-brand-500/25 text-brand-300 text-xs font-semibold backdrop-blur-md">
                <Sparkles className="h-3.5 w-3.5 text-brand-400 animate-spin-slow" />
                <span>Quantum-Assisted Placement Intelligence &bull; QAIP v2.4</span>
              </div>

              {/* Main Punchy Headline */}
              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black text-slate-100 tracking-tight leading-[1.1]">
                Practice Smarter.
                <br />
                <span className="bg-gradient-to-r from-brand-400 via-indigo-300 to-cyan-400 bg-clip-text text-transparent">
                  Interview Fearlessly.
                </span>
              </h1>

              {/* Concise Subtitle */}
              <p className="text-base sm:text-lg text-slate-400 leading-relaxed max-w-xl mx-auto lg:mx-0">
                A hands-free conversational AI examiner with real-time Monaco code execution,
                objective rubric evaluation, and quantum-assisted preparation path ranking.
              </p>

              {/* Action Buttons */}
              <div className="flex flex-col sm:flex-row gap-3.5 justify-center lg:justify-start pt-2">
                <button
                  type="button"
                  onClick={() => navigate('/register')}
                  className="btn-primary text-base px-8 py-4 shadow-xl shadow-brand-600/30 group"
                >
                  <span>Start Live Mock Interview</span>
                  <ArrowRight className="h-4 w-4 group-hover:translate-x-1 transition-transform" />
                </button>
                <button
                  type="button"
                  onClick={() => scrollTo('features')}
                  className="btn-secondary text-base px-7 py-4"
                >
                  Explore Capabilities
                </button>
              </div>

              {/* Micro Metrics Bar */}
              <div className="pt-4 flex flex-wrap items-center justify-center lg:justify-start gap-6 text-xs text-slate-400 border-t border-surface-border/60">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                  <span>100% Hands-Free Voice</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-brand-400" />
                  <span>Monaco Editor + Judge0</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-cyan-400" />
                  <span>Objective 0–10 Rubrics</span>
                </div>
              </div>
            </div>

            {/* Right Column: Live Interactive Demo Mockup */}
            <div className="relative">
              <InteractiveHeroDemo />
            </div>
          </div>
        </div>
      </section>

      {/* ── 2. INTERACTIVE TARGET ROLE EXPLORER ───────────────────────────────── */}
      <section id="role-explorer" className="py-20 relative">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto mb-12">
            <span className="text-xs font-bold text-brand-400 uppercase tracking-widest block mb-2">
              Personalized Assessment Architecture
            </span>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-100">
              Tailored to Your Dream Job Role
            </h2>
            <p className="text-sm text-slate-400 mt-3">
              Explore how QAIP generates questions, live coding tasks, and evaluation rubrics specifically matching corporate hiring bars.
            </p>
          </div>

          <RoleExplorer onSelectRole={() => navigate('/register')} />
        </div>
      </section>

      {/* ── 3. FEATURES BENTO GRID (MINIMAL & ATTRACTIVE) ──────────────────────── */}
      <section id="features" className="py-20 bg-surface-card/25 tech-dots relative">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto mb-14">
            <span className="text-xs font-bold text-brand-400 uppercase tracking-widest block mb-2">
              Next-Gen Capabilities
            </span>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-100">
              Built for Serious Technical Excellence
            </h2>
            <p className="text-sm text-slate-400 mt-3">
              Everything required to eliminate interview anxiety, diagnose blind spots, and practice with real engineering rigor.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* Card 1 */}
            <div className="card p-6 glass-card-hover group relative overflow-hidden">
              <div className="w-12 h-12 rounded-xl bg-brand-500/10 border border-brand-500/25 flex items-center justify-center text-brand-400 mb-4 group-hover:scale-110 transition-transform">
                <Mic className="h-6 w-6" />
              </div>
              <h3 className="text-base font-bold text-slate-100 mb-2">Conversational Voice AI</h3>
              <p className="text-xs sm:text-sm text-slate-400 leading-relaxed">
                Hands-free spoken interviews. The AI examiner talks with natural cadence and listens to your spoken explanations with smart silence detection.
              </p>
            </div>

            {/* Card 2 */}
            <div className="card p-6 glass-card-hover group relative overflow-hidden">
              <div className="w-12 h-12 rounded-xl bg-indigo-500/10 border border-indigo-500/25 flex items-center justify-center text-indigo-400 mb-4 group-hover:scale-110 transition-transform">
                <Code2 className="h-6 w-6" />
              </div>
              <h3 className="text-base font-bold text-slate-100 mb-2">Monaco Coding Sandbox</h3>
              <p className="text-xs sm:text-sm text-slate-400 leading-relaxed">
                Execute code live in Python, Java, and C++ via Judge0. Run against hidden test cases with immediate feedback and complexity analysis.
              </p>
            </div>

            {/* Card 3 */}
            <div className="card p-6 glass-card-hover group relative overflow-hidden">
              <div className="w-12 h-12 rounded-xl bg-cyan-500/10 border border-cyan-500/25 flex items-center justify-center text-cyan-400 mb-4 group-hover:scale-110 transition-transform">
                <Brain className="h-6 w-6" />
              </div>
              <h3 className="text-base font-bold text-slate-100 mb-2">Adaptive Llama 3 Inquiry</h3>
              <p className="text-xs sm:text-sm text-slate-400 leading-relaxed">
                If your answer is shallow, the AI asks follow-ups just like a senior interviewer. It dynamically adapts question difficulty in real time.
              </p>
            </div>

            {/* Card 4 */}
            <div className="card p-6 glass-card-hover group relative overflow-hidden">
              <div className="w-12 h-12 rounded-xl bg-purple-500/10 border border-purple-500/25 flex items-center justify-center text-purple-400 mb-4 group-hover:scale-110 transition-transform">
                <FileText className="h-6 w-6" />
              </div>
              <h3 className="text-base font-bold text-slate-100 mb-2">Resume-Aware Personalization</h3>
              <p className="text-xs sm:text-sm text-slate-400 leading-relaxed">
                Upload your resume to extract skills and project milestones automatically. The examiner asks in-depth questions about what you built.
              </p>
            </div>

            {/* Card 5 */}
            <div className="card p-6 glass-card-hover group relative overflow-hidden">
              <div className="w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/25 flex items-center justify-center text-emerald-400 mb-4 group-hover:scale-110 transition-transform">
                <Shield className="h-6 w-6" />
              </div>
              <h3 className="text-base font-bold text-slate-100 mb-2">Proctoring &amp; Realism</h3>
              <p className="text-xs sm:text-sm text-slate-400 leading-relaxed">
                Enforces proctored examination rules: fullscreen locks, tab switch detection, and active camera verification for genuine readiness.
              </p>
            </div>

            {/* Card 6 */}
            <div className="card p-6 glass-card-hover group relative overflow-hidden">
              <div className="w-12 h-12 rounded-xl bg-amber-500/10 border border-amber-500/25 flex items-center justify-center text-amber-400 mb-4 group-hover:scale-110 transition-transform">
                <Atom className="h-6 w-6" />
              </div>
              <h3 className="text-base font-bold text-slate-100 mb-2">Quantum Path Optimization</h3>
              <p className="text-xs sm:text-sm text-slate-400 leading-relaxed">
                Research integration exploring Qiskit QAOA to calculate the optimal preparation path through your identified skill gaps.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ── 4. HOW IT WORKS TIMELINE ─────────────────────────────────────────── */}
      <section id="how-it-works" className="py-20 relative">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <span className="text-xs font-bold text-brand-400 uppercase tracking-widest block mb-2">
              Zero Guesswork
            </span>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-100">
              The Placement Mastery Pipeline
            </h2>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              {
                step: '01',
                title: 'Profile Setup',
                desc: 'Upload resume & target role. Skills and project context are parsed in seconds.',
                icon: <UserPlus className="h-5 w-5" />,
              },
              {
                step: '02',
                title: 'Live Voice Exam',
                desc: 'Speak answers hands-free. Examiner probes deeper adaptively based on your responses.',
                icon: <Mic className="h-5 w-5" />,
              },
              {
                step: '03',
                title: 'Sandboxed Code',
                desc: 'Tackle algorithmic problems in Monaco with real test case execution.',
                icon: <Code2 className="h-5 w-5" />,
              },
              {
                step: '04',
                title: 'Skill Gap Plan',
                desc: 'Receive 0–10 rubric scores, weakness breakdown, and targeted practice recommendations.',
                icon: <TrendingUp className="h-5 w-5" />,
              },
            ].map((s, idx) => (
              <div key={idx} className="card p-5 relative overflow-hidden group hover:border-brand-500/40 transition-all">
                <span className="text-3xl font-black text-slate-700/60 absolute top-3 right-3 font-mono group-hover:text-brand-500/20 transition-colors">
                  {s.step}
                </span>
                <div className="w-10 h-10 rounded-xl bg-brand-500/10 text-brand-400 flex items-center justify-center mb-3">
                  {s.icon}
                </div>
                <h4 className="text-sm font-bold text-slate-100 mb-1.5">{s.title}</h4>
                <p className="text-xs text-slate-400 leading-relaxed">{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── 5. QUANTUM OPTIMIZATION SHOWCASE ─────────────────────────────────── */}
      <section id="quantum" className="py-20 bg-surface-card/20 relative overflow-hidden">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="card p-8 sm:p-10 border-brand-500/30 relative overflow-hidden bg-gradient-to-br from-slate-900/90 via-slate-950 to-slate-900">
            {/* Ambient atom ring glow */}
            <div className="absolute top-1/2 -right-16 -translate-y-1/2 w-80 h-80 bg-brand-500/10 rounded-full blur-3xl pointer-events-none" />

            <div className="grid lg:grid-cols-2 gap-8 items-center">
              <div className="space-y-4">
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 text-xs font-semibold">
                  <Atom className="h-3.5 w-3.5 animate-spin-slow" />
                  <span>Research Track &bull; Qiskit Optimization</span>
                </div>
                <h3 className="text-2xl sm:text-3xl font-black text-slate-100">
                  Quantum Approximate Optimization (QAOA)
                </h3>
                <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
                  How should a student allocate 20 hours to recover 8 distinct skill gaps? Standard systems use static greedy sorting. QAIP explores QAOA combinatorial path mapping to select the highest-yield interview questions and study topics.
                </p>

                <div className="grid grid-cols-2 gap-3 pt-2 text-xs">
                  <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800">
                    <span className="text-[10px] text-slate-500 font-bold block uppercase">Algorithm</span>
                    <span className="text-slate-200 font-semibold">QAOA Hamiltonian</span>
                  </div>
                  <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800">
                    <span className="text-[10px] text-slate-500 font-bold block uppercase">Objective</span>
                    <span className="text-emerald-400 font-semibold">Max Skill Recovery / Hour</span>
                  </div>
                </div>
              </div>

              {/* Quantum Circuit Graphic Simulator */}
              <div className="relative p-6 rounded-2xl bg-slate-950 border border-slate-800 font-mono text-xs text-slate-400 flex flex-col items-center justify-center min-h-[220px]">
                <div className="w-24 h-24 rounded-full border border-brand-500/40 flex items-center justify-center animate-pulse-ring relative">
                  <div className="w-16 h-16 rounded-full border border-cyan-400/50 flex items-center justify-center animate-spin-slow">
                    <Atom className="h-8 w-8 text-brand-400" />
                  </div>
                </div>
                <div className="text-center mt-4">
                  <span className="text-[11px] font-bold text-slate-200 block">Qiskit State Space Optimization</span>
                  <span className="text-[10px] text-brand-400">Minimizing preparation entropy across target roles</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── 6. CURIOUS FAQ ACCORDION ─────────────────────────────────────────── */}
      <section id="faq" className="py-20 relative">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <span className="text-xs font-bold text-brand-400 uppercase tracking-widest block mb-2">
              Clarifications &amp; Facts
            </span>
            <h2 className="text-3xl font-extrabold text-slate-100">Frequently Asked Questions</h2>
          </div>

          <div className="space-y-3">
            {FAQS.map((faq, i) => (
              <div
                key={i}
                className="card border-surface-border overflow-hidden transition-all"
              >
                <button
                  type="button"
                  onClick={() => setOpenFaq(openFaq === i ? null : i)}
                  className="w-full p-4 sm:p-5 text-left flex items-center justify-between text-sm sm:text-base font-semibold text-slate-100 hover:text-brand-300 transition-colors"
                >
                  <span>{faq.q}</span>
                  <ChevronDown className={clsx('h-4 w-4 transition-transform flex-shrink-0 ml-3', openFaq === i && 'rotate-180 text-brand-400')} />
                </button>
                {openFaq === i && (
                  <div className="px-5 pb-5 pt-1 text-xs sm:text-sm text-slate-400 leading-relaxed border-t border-slate-800/60 animate-fade-in">
                    {faq.a}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── 7. CONTACT FORM ─────────────────────────────────────────────────── */}
      <section id="contact" className="py-20 bg-surface-card/20 relative">
        <div className="max-w-xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-10">
            <h2 className="text-3xl font-bold text-slate-100 mb-2">Have Feedback or Questions?</h2>
            <p className="text-xs sm:text-sm text-slate-400">
              Reach out to our placement readiness team. We read every inquiry.
            </p>
          </div>

          <div className="card p-6 sm:p-8 border-brand-500/20">
            <form onSubmit={(e) => { e.preventDefault(); toast.success('Message sent! We will follow up shortly.') }} className="space-y-4">
              <div>
                <label className="label">Name</label>
                <input type="text" className="input-base" placeholder="Your full name" required />
              </div>
              <div>
                <label className="label">Email</label>
                <input type="email" className="input-base" placeholder="you@university.edu" required />
              </div>
              <div>
                <label className="label">Message</label>
                <textarea rows={3} className="input-base resize-none" placeholder="How can we help your interview prep?" required />
              </div>
              <button type="submit" className="btn-primary w-full py-3 text-sm">
                <Send className="h-4 w-4" /> Send Message
              </button>
            </form>
          </div>
        </div>
      </section>

      {/* ── 8. HIGH-IMPACT FINAL CTA ─────────────────────────────────────────── */}
      <section className="py-16 relative overflow-hidden bg-gradient-to-r from-brand-900/40 via-indigo-950/60 to-slate-950 border-t border-surface-border">
        <div className="max-w-4xl mx-auto px-4 text-center space-y-5">
          <h2 className="text-3xl sm:text-4xl font-extrabold text-white">
            Ready to Crack Your Next Placement?
          </h2>
          <p className="text-sm text-slate-300 max-w-lg mx-auto">
            Take a mock interview now. Experience hands-free voice questioning and sandboxed code execution in under 2 minutes.
          </p>
          <div className="pt-2">
            <button
              type="button"
              onClick={() => navigate('/register')}
              className="btn-primary text-base px-9 py-4 shadow-2xl shadow-brand-500/40 hover:scale-105 transition-transform"
            >
              Get Started for Free <ArrowRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      </section>

      {/* ── 9. FOOTER ───────────────────────────────────────────────────────── */}
      <PublicFooter />
    </div>
  )
}

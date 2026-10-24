"""
Adaptive Interview Engine.

Drives the interview turn-by-turn. Decides:
  - Which phase to be in
  - Which question to ask next (based on history + performance)
  - Whether to follow up, increase difficulty, or move on
  - When to transition to the next phase

All decisions are made per-student, based on their individual session state.
"""
import re
import random
import logging
from dataclasses import dataclass, field
from typing import Optional

from .question_bank import (
    QuestionEntry,
    WARMUP_QUESTIONS,
    HR_QUESTIONS,
    PROJECT_QUESTIONS,
    CLOSING_QUESTIONS,
    get_technical_questions,
)
from .ai_services import generate_llm_interview_question

logger = logging.getLogger(__name__)

# ── Phase configuration ────────────────────────────────────────────────────────

# Full interview phase order — coding inserted between technical and project
PHASE_SEQUENCE = ['warmup', 'technical', 'coding', 'project', 'hr', 'closing']

# Coding-only sessions
CODING_ONLY_SEQUENCE = ['coding', 'closing']

PHASE_QUESTION_COUNTS = {
    'mixed':     {'warmup': 2, 'technical': 4, 'coding': 2, 'project': 2, 'hr': 2, 'closing': 1},
    'technical': {'warmup': 1, 'technical': 8, 'coding': 0, 'project': 2, 'hr': 1, 'closing': 1},
    'hr':        {'warmup': 1, 'technical': 2, 'coding': 0, 'project': 1, 'hr': 6, 'closing': 1},
    'project':   {'warmup': 1, 'technical': 3, 'coding': 0, 'project': 5, 'hr': 2, 'closing': 1},
    'coding':    {'warmup': 0, 'technical': 0, 'coding': 4, 'project': 0, 'hr': 0, 'closing': 1},
}

# ── Scoring constants ──────────────────────────────────────────────────────────

# Score thresholds on the 0.0–1.0 scale
SCORE_EXCELLENT    = 0.90   # 9-10/10
SCORE_GOOD         = 0.75   # 7-8/10
SCORE_ADEQUATE     = 0.55   # 5-6/10
SCORE_PARTIAL      = 0.35   # 3-4/10
SCORE_POOR         = 0.15   # 1-2/10
SCORE_EMPTY        = 0.0    # 0/10 — no answer / noise only

# Backward-compat alias used by views
GOOD_ANSWER_THRESHOLD = SCORE_GOOD
WEAK_ANSWER_THRESHOLD = SCORE_PARTIAL

# Noise tokens that do not constitute a real answer even if non-empty
_NOISE_TOKENS = frozenset({
    'uh', 'um', 'er', 'hmm', 'hm', 'ah', 'oh', 'okay', 'ok',
    'yeah', 'yes', 'no', 'yep', 'nope', 'right', 'sure', 'fine',
})


# ── Dataclasses ────────────────────────────────────────────────────────────────

@dataclass
class TurnDecision:
    """The engine's decision for the next question."""
    question_text: str
    phase: str
    topic: str
    difficulty_level: str
    question_type: str
    expected_concepts: list
    is_follow_up: bool
    follow_up_reason: Optional[str]   # 'weak_answer' | 'strong_answer' | None
    should_end_interview: bool


@dataclass
class SessionContext:
    """Current state of an interview session used to make decisions."""
    session_type: str
    domain: str
    difficulty: str
    current_phase: str
    turn_number: int
    questions_in_phase: int
    last_answer_score: Optional[float]
    last_question_text: str
    last_question_entry: Optional[QuestionEntry]
    asked_question_texts: set
    phase_scores: dict
    candidate_name: str = ""
    target_role_name: str = ""
    resume_skills: list = field(default_factory=list)
    resume_projects: list = field(default_factory=list)
    last_answer_text: str = ""


# ── Engine ─────────────────────────────────────────────────────────────────────

class AdaptiveInterviewEngine:
    """
    Determines the next interview action based on full session state.
    Uses dynamic LLM question generation with conversational progression.
    """

    def decide_next_turn(self, ctx: SessionContext) -> TurnDecision:
        """Main decision function. Returns what question to ask next."""

        # ── 1. Coding-only sessions start directly with coding ─────────────────
        if ctx.session_type == 'coding' and ctx.turn_number == 0:
            return TurnDecision(
                question_text=(
                    "Let's begin the coding round. I'll present you with a programming problem. "
                    "Think through your approach carefully before you start coding. "
                    "When you're ready, you'll have access to an editor to write and run your solution."
                ),
                phase='coding',
                topic='coding_introduction',
                difficulty_level=self._map_difficulty(ctx.difficulty),
                question_type='coding',
                expected_concepts=['algorithm', 'problem_solving', 'code'],
                is_follow_up=False,
                follow_up_reason=None,
                should_end_interview=False,
            )

        # ── 2. Turn 0 for non-coding sessions: welcoming intro ─────────────────
        if ctx.turn_number == 0:
            intro_q = generate_llm_interview_question(
                candidate_name=ctx.candidate_name,
                target_role=ctx.target_role_name or ctx.domain,
                resume_skills=ctx.resume_skills,
                resume_projects=ctx.resume_projects,
                current_phase='warmup',
                turn_number=1,
                difficulty='easy',
                session_type=ctx.session_type,
            )
            return TurnDecision(
                question_text=intro_q['question_text'],
                phase='warmup',
                topic=intro_q.get('topic', 'introduction'),
                difficulty_level='easy',
                question_type='situational',
                expected_concepts=intro_q.get('expected_concepts', ['name', 'background', 'education', 'goals', 'skills']),
                is_follow_up=False,
                follow_up_reason=None,
                should_end_interview=False,
            )

        # ── 3. Check completion ────────────────────────────────────────────────
        if self._should_end(ctx):
            closing = self._get_closing(ctx)
            return TurnDecision(
                question_text=closing['text'],
                phase='closing',
                topic='closing',
                difficulty_level='easy',
                question_type='situational',
                expected_concepts=closing['expected_concepts'],
                is_follow_up=False,
                follow_up_reason=None,
                should_end_interview=False,
            )

        # ── 4. Determine active phase and difficulty ──────────────────────────
        next_phase = self._maybe_advance_phase(ctx)
        active_phase = next_phase or ctx.current_phase
        diff = self._adaptive_difficulty(ctx)

        # ── 5. Coding phase: sentinel for coding problem ──────────────────────
        if active_phase == 'coding':
            follow_up_reason = None
            if ctx.last_answer_score is not None:
                if ctx.last_answer_score >= GOOD_ANSWER_THRESHOLD:
                    follow_up_reason = 'strong_answer'
                elif ctx.last_answer_score < WEAK_ANSWER_THRESHOLD:
                    follow_up_reason = 'weak_answer'
            return TurnDecision(
                question_text='[CODING_PROBLEM]',
                phase='coding',
                topic='coding',
                difficulty_level=diff,
                question_type='coding',
                expected_concepts=['algorithm', 'data_structure', 'complexity', 'correctness'],
                is_follow_up=ctx.turn_number >= 1,
                follow_up_reason=follow_up_reason,
                should_end_interview=False,
            )

        # ── 6. Generate next question via LLM ─────────────────────────────────
        llm_q = generate_llm_interview_question(
            candidate_name=ctx.candidate_name,
            target_role=ctx.target_role_name or ctx.domain,
            resume_skills=ctx.resume_skills,
            resume_projects=ctx.resume_projects,
            current_phase=active_phase,
            turn_number=ctx.turn_number + 1,
            difficulty=diff,
            last_question_text=ctx.last_question_text,
            last_answer_text=ctx.last_answer_text,
            last_score=ctx.last_answer_score,
            session_type=ctx.session_type,
        )

        follow_up_reason = None
        if ctx.last_answer_score is not None:
            if ctx.last_answer_score >= GOOD_ANSWER_THRESHOLD:
                follow_up_reason = 'strong_answer'
            elif ctx.last_answer_score < WEAK_ANSWER_THRESHOLD:
                follow_up_reason = 'weak_answer'

        return TurnDecision(
            question_text=llm_q['question_text'],
            phase=active_phase,
            topic=llm_q.get('topic', active_phase),
            difficulty_level=diff,
            question_type=llm_q.get('question_type', self._infer_type(active_phase)),
            expected_concepts=llm_q.get('expected_concepts', []),
            is_follow_up=ctx.turn_number >= 1,
            follow_up_reason=follow_up_reason,
            should_end_interview=False,
        )

    # ── Private helpers ────────────────────────────────────────────────────────

    def _should_end(self, ctx: SessionContext) -> bool:
        """
        Return True only when ALL configured phases have been completed.
        Uses phase_question_counts rather than a hardcoded turn limit.
        """
        if ctx.current_phase == 'closing' and ctx.questions_in_phase >= 1:
            return True

        counts = PHASE_QUESTION_COUNTS.get(ctx.session_type, PHASE_QUESTION_COUNTS['mixed'])
        total_limit = sum(counts.values())

        # Only end if we've hit or exceeded the total configured questions
        return ctx.turn_number >= total_limit

    def _phase_limit(self, ctx: SessionContext) -> int:
        counts = PHASE_QUESTION_COUNTS.get(ctx.session_type, PHASE_QUESTION_COUNTS['mixed'])
        return counts.get(ctx.current_phase, 3)

    def _maybe_advance_phase(self, ctx: SessionContext) -> Optional[str]:
        """Return next phase name if current phase quota is exhausted."""
        limit = self._phase_limit(ctx)
        if ctx.questions_in_phase >= limit:
            seq = CODING_ONLY_SEQUENCE if ctx.session_type == 'coding' else PHASE_SEQUENCE
            try:
                current_idx = seq.index(ctx.current_phase)
            except ValueError:
                current_idx = 0

            counts = PHASE_QUESTION_COUNTS.get(ctx.session_type, PHASE_QUESTION_COUNTS['mixed'])
            # Walk forward, skipping zero-count phases
            next_idx = current_idx + 1
            while next_idx < len(seq):
                candidate = seq[next_idx]
                if counts.get(candidate, 0) > 0:
                    return candidate
                next_idx += 1
        return None

    def _map_difficulty(self, session_difficulty: str) -> str:
        return {'beginner': 'easy', 'intermediate': 'medium', 'advanced': 'hard'}.get(
            session_difficulty, 'medium'
        )

    def _adaptive_difficulty(self, ctx: SessionContext) -> str:
        if ctx.session_type in ('technical', 'mixed', 'coding'):
            scores = ctx.phase_scores.get(ctx.current_phase, [])
            if len(scores) >= 2:
                recent_avg = sum(scores[-2:]) / 2
                if recent_avg >= GOOD_ANSWER_THRESHOLD:
                    return self._next_difficulty(ctx.difficulty)
                elif recent_avg < WEAK_ANSWER_THRESHOLD:
                    return self._prev_difficulty(ctx.difficulty)
        return self._map_difficulty(ctx.difficulty)

    def _next_difficulty(self, current: str) -> str:
        return {'beginner': 'medium', 'easy': 'medium', 'intermediate': 'hard',
                'medium': 'hard', 'advanced': 'hard', 'hard': 'hard'}.get(current, 'medium')

    def _prev_difficulty(self, current: str) -> str:
        return {'advanced': 'medium', 'hard': 'medium', 'intermediate': 'easy',
                'medium': 'easy', 'beginner': 'easy', 'easy': 'easy'}.get(current, 'easy')

    def _pick_question(self, phase: str, ctx: SessionContext) -> Optional[QuestionEntry]:
        if phase == 'warmup':
            pool = WARMUP_QUESTIONS
        elif phase == 'technical':
            diff = self._adaptive_difficulty(ctx)
            pool = get_technical_questions(ctx.domain, diff) or get_technical_questions(ctx.domain, 'medium')
        elif phase == 'hr':
            pool = HR_QUESTIONS
        elif phase == 'project':
            pool = PROJECT_QUESTIONS
        elif phase == 'closing':
            pool = CLOSING_QUESTIONS
        else:
            pool = WARMUP_QUESTIONS

        available = [q for q in pool if q['text'] not in ctx.asked_question_texts]
        if not available:
            available = pool
        return random.choice(available) if available else None

    def _get_closing(self, ctx: SessionContext) -> QuestionEntry:
        available = [q for q in CLOSING_QUESTIONS if q['text'] not in ctx.asked_question_texts]
        return available[0] if available else CLOSING_QUESTIONS[0]

    def _infer_type(self, phase: str) -> str:
        return {
            'warmup': 'situational',
            'technical': 'conceptual',
            'hr': 'behavioral',
            'project': 'project',
            'coding': 'coding',
            'closing': 'situational',
        }.get(phase, 'conceptual')


# ── Answer pre-validation ──────────────────────────────────────────────────────

def _is_meaningful_answer(text: str) -> tuple[bool, str]:
    """
    Deterministically classify the answer BEFORE touching the LLM.

    Returns (is_meaningful: bool, classification: str).

    Classification values:
      'no_answer'        — empty, whitespace, or pure noise tokens
      'meaningful'       — contains enough substance to evaluate
    """
    if not text:
        return False, 'no_answer'

    # Strip punctuation for token analysis
    clean = re.sub(r"[^\w\s']", ' ', text.lower()).strip()
    if not clean:
        return False, 'no_answer'

    tokens = [t for t in clean.split() if t]
    if not tokens:
        return False, 'no_answer'

    # Remove pure noise tokens to see what's left
    meaningful_tokens = [t for t in tokens if t not in _NOISE_TOKENS and len(t) > 1]

    # Require at least 3 meaningful tokens
    if len(meaningful_tokens) < 3:
        return False, 'no_answer'

    return True, 'meaningful'


# ── Scoring ────────────────────────────────────────────────────────────────────

def evaluate_answer_quality(answer_text: str, expected_concepts: list) -> float:
    """
    Score a text answer on a 0.0–1.0 scale.

    Critically:
      - Empty / noise-only answers always return 0.0
      - There is NO artificial score floor for real answers
      - Short but accurate answers can still score high via concept coverage
      - Long but irrelevant answers score low

    The 0.0–1.0 result maps to 0–10 in the UI.
    """
    # ── Pre-validation: empty / noise → hard 0 ────────────────────────────────
    is_meaningful, classification = _is_meaningful_answer(answer_text)
    if not is_meaningful:
        logger.info('Answer classified as NO_ANSWER — returning score 0.0')
        return SCORE_EMPTY

    answer_lower = answer_text.lower()
    word_count = len(answer_text.split())

    # ── Length score ───────────────────────────────────────────────────────────
    # 60+ words = full length marks; short but correct answers compensate via concept score
    length_score = min(word_count / 60.0, 1.0)

    # ── Concept coverage score ─────────────────────────────────────────────────
    if expected_concepts:
        hits = sum(
            1 for concept in expected_concepts
            if any(
                kw.lower() in answer_lower
                for kw in concept.replace('/', ' ').split()
                if len(kw) > 3
            )
        )
        concept_score = hits / len(expected_concepts)
    else:
        # No rubric concepts — rely more on length
        concept_score = 0.5

    # ── Combined score: 35% length + 65% concept coverage ────────────────────
    raw_score = 0.35 * length_score + 0.65 * concept_score

    # NO artificial floor — a real answer that covers zero concepts scores near 0
    return round(min(raw_score, 1.0), 2)


def build_ai_feedback(
    question_text: str,
    answer_text: str,
    expected_concepts: list,
    score: float,
    phase: str,
) -> str:
    """
    Generate structured AI feedback grounded in the actual answer.

    Rubric (maps score bands to qualitative labels):
      0.0        → NO_ANSWER / pure noise
      0.01–0.20  → Incorrect / major misunderstanding
      0.21–0.40  → Partially relevant, major gaps
      0.41–0.60  → Partially correct, some key points
      0.61–0.75  → Mostly correct, minor gaps
      0.76–0.90  → Good answer, well explained
      0.91–1.0   → Excellent — accurate, complete, clear
    """
    # ── Empty / no-answer ─────────────────────────────────────────────────────
    is_meaningful, classification = _is_meaningful_answer(answer_text)
    if not is_meaningful:
        return (
            "No answer was provided. Please attempt the question and explain your reasoning, "
            "even if you are unsure. Partial knowledge is always better than silence."
        )

    # ── Find missed concepts ───────────────────────────────────────────────────
    answer_lower = answer_text.lower()
    missed = [
        c for c in expected_concepts
        if not any(kw.lower() in answer_lower for kw in c.split() if len(kw) > 3)
    ]
    covered = [c for c in expected_concepts if c not in missed]

    # ── Phase-aware feedback prefix ───────────────────────────────────────────
    phase_context = {
        'technical': 'From a technical perspective: ',
        'project':   'Regarding your project discussion: ',
        'hr':        'In terms of communication and clarity: ',
        'warmup':    '',
        'closing':   '',
    }.get(phase, '')

    # ── Score-band feedback ────────────────────────────────────────────────────
    if score >= 0.91:
        quality = "Excellent answer."
        prefix = f"{phase_context}Excellent — your answer was accurate, complete, and clearly explained."
        if covered:
            prefix += f" You demonstrated strong understanding of: {', '.join(covered[:4])}."

    elif score >= 0.76:
        quality = "Good answer."
        prefix = f"{phase_context}Good response — you covered the key concepts well."
        if missed:
            prefix += f" You could strengthen your answer by also addressing: {', '.join(missed[:2])}."

    elif score >= 0.61:
        quality = "Mostly correct."
        prefix = f"{phase_context}Mostly correct — the core idea is right."
        if missed:
            prefix += f" Important points that were missing or incomplete: {', '.join(missed[:3])}."

    elif score >= 0.41:
        quality = "Partially correct."
        prefix = f"{phase_context}Partially correct — you showed some relevant understanding."
        if missed:
            prefix += f" Key concepts not addressed: {', '.join(missed[:3])}."
        prefix += " Try to be more structured and thorough in your explanation."

    elif score >= 0.21:
        quality = "Mostly incorrect."
        prefix = f"{phase_context}Your answer showed limited understanding of the question."
        if missed:
            prefix += f" Key concepts missing: {', '.join(missed[:4])}."
        prefix += " Review the topic and try to be more specific."

    else:
        quality = "Incorrect."
        prefix = (
            f"{phase_context}The answer did not demonstrate understanding of the concept asked. "
            "Please review the topic carefully."
        )
        if expected_concepts:
            prefix += f" Key areas to study: {', '.join(expected_concepts[:4])}."

    return prefix


# ── LLM-based scoring (called from views when LLM is available) ───────────────

def build_llm_scoring_prompt(
    question_text: str,
    answer_text: str,
    expected_concepts: list,
    phase: str,
    question_type: str,
) -> tuple[str, str]:
    """
    Build the system prompt + user prompt for LLM-based answer evaluation.

    The LLM must return structured JSON:
    {
      "score": 0-10,
      "classification": "no_answer|incorrect|partially_correct|mostly_correct|correct|excellent",
      "strengths": ["..."],
      "missing_concepts": ["..."],
      "feedback": "...",
      "should_follow_up": true/false
    }

    The LLM is explicitly instructed:
    - Do NOT award marks for concepts not present in the answer
    - Empty answers must score 0
    - Grounding: judge based only on what was actually said
    """
    rubric = """
SCORING RUBRIC (map your judgment to this scale):
0/10   — No answer, empty, pure noise, completely unrelated, no evidence of understanding
1-2/10 — Mostly incorrect, major misunderstanding, very little relevant information
3-4/10 — Some relevant understanding, major missing concepts, significant inaccuracies
5-6/10 — Partially correct, core idea understood, some important details missing
7-8/10 — Mostly correct, good understanding, covers important concepts, minor omissions
9-10/10— Correct, complete, technically accurate, clear explanation, strong understanding
"""

    phase_guidance = {
        'technical': (
            "Evaluate: factual correctness, technical terminology, quality of reasoning, "
            "use of examples, depth of explanation."
        ),
        'project': (
            "Evaluate: understanding of their own project, architecture decisions, "
            "technologies used, implementation details, challenges faced."
        ),
        'hr': (
            "Evaluate: relevance to the question, clarity of communication, "
            "professionalism, authenticity, consistency."
        ),
        'warmup': (
            "Evaluate: relevance, clarity, coherence, and ability to articulate background."
        ),
    }.get(phase, "Evaluate: relevance, correctness, and clarity.")

    expected_str = ', '.join(expected_concepts[:8]) if expected_concepts else 'not specified'

    system_prompt = f"""You are an expert interview evaluator. Your job is to score a candidate's answer strictly and fairly.

CRITICAL RULES — YOU MUST FOLLOW THESE:
1. If the answer is empty, null, or contains only filler words (uh, um, yes, no, okay), score = 0.
2. Do NOT award marks for concepts that are NOT present in the candidate's answer.
3. Do NOT assume the candidate knew something they did not say.
4. Do NOT be lenient simply because the answer is short — short but correct answers can score 7-10.
5. Judge based ONLY on what is actually in the answer text.
6. Return ONLY valid JSON matching the specified schema.

{rubric}

Phase focus: {phase_guidance}
"""

    user_prompt = f"""INTERVIEW QUESTION:
{question_text}

EXPECTED CONCEPTS/RUBRIC:
{expected_str}

CANDIDATE'S ACTUAL ANSWER:
{answer_text if answer_text and answer_text.strip() else '[NO ANSWER PROVIDED]'}

Evaluate the candidate's answer and return ONLY this JSON (no markdown, no prose):
{{
  "score": <integer 0-10>,
  "classification": "<no_answer|incorrect|partially_correct|mostly_correct|correct|excellent>",
  "strengths": [<list of strings, empty if none>],
  "missing_concepts": [<list of concepts the answer missed>],
  "feedback": "<1-3 sentence constructive feedback>",
  "should_follow_up": <true if score < 6 and question is worth probing further, else false>
}}"""

    return system_prompt, user_prompt


def parse_llm_evaluation(llm_response: str, fallback_score: float) -> dict:
    """
    Parse and validate the LLM evaluation JSON response.

    Rules:
    - score must be numeric 0-10
    - classification must be one of the allowed values
    - no_answer classification forces score = 0
    - invalid/unparseable response uses fallback_score
    """
    import json as _json

    ALLOWED_CLASSIFICATIONS = {
        'no_answer', 'incorrect', 'partially_correct',
        'mostly_correct', 'correct', 'excellent'
    }

    try:
        # Strip markdown code fences if present
        clean = llm_response.strip()
        if clean.startswith('```'):
            clean = re.sub(r'^```[a-z]*\n?', '', clean)
            clean = re.sub(r'\n?```$', '', clean)

        # Extract JSON object if embedded in prose
        json_match = re.search(r'\{.*\}', clean, re.DOTALL)
        if json_match:
            clean = json_match.group(0)

        data = _json.loads(clean)

        # Validate and normalise score
        raw_score = data.get('score')
        if not isinstance(raw_score, (int, float)):
            logger.warning('LLM returned non-numeric score: %r', raw_score)
            raw_score = round(fallback_score * 10)
        score = max(0, min(10, int(raw_score)))

        # Validate classification
        classification = str(data.get('classification', '')).lower().strip()
        if classification not in ALLOWED_CLASSIFICATIONS:
            logger.warning('LLM returned unknown classification: %r', classification)
            classification = _score_to_classification(score / 10.0)

        # Enforce: no_answer must have score 0
        if classification == 'no_answer':
            score = 0

        return {
            'score_10':        score,
            'score_01':        round(score / 10.0, 2),
            'classification':  classification,
            'strengths':       data.get('strengths', []),
            'missing_concepts': data.get('missing_concepts', []),
            'feedback':        data.get('feedback', ''),
            'should_follow_up': bool(data.get('should_follow_up', score < 6)),
        }

    except Exception as exc:
        logger.error('Failed to parse LLM evaluation response: %s | raw: %.200s', exc, llm_response)
        # Safe fallback — use deterministic score, do NOT invent data
        return {
            'score_10':        round(fallback_score * 10),
            'score_01':        fallback_score,
            'classification':  _score_to_classification(fallback_score),
            'strengths':       [],
            'missing_concepts': [],
            'feedback':        'Evaluation could not be parsed. Score based on keyword analysis.',
            'should_follow_up': fallback_score < 0.5,
        }


def _score_to_classification(score_01: float) -> str:
    if score_01 == 0:
        return 'no_answer'
    elif score_01 < 0.25:
        return 'incorrect'
    elif score_01 < 0.45:
        return 'partially_correct'
    elif score_01 < 0.65:
        return 'mostly_correct'
    elif score_01 < 0.85:
        return 'correct'
    else:
        return 'excellent'

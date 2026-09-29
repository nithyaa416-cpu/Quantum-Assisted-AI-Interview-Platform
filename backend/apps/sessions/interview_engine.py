"""
Adaptive Interview Engine.

Drives the interview turn-by-turn. Decides:
  - Which phase to be in
  - Which question to ask next (based on history + performance)
  - Whether to follow up, increase difficulty, or move on
  - When to transition to the next phase

All decisions are made per-student, based on their individual session state.
"""
import random
import logging
from dataclasses import dataclass
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

PHASE_SEQUENCE = ['warmup', 'technical', 'project', 'hr', 'closing']

PHASE_QUESTION_COUNTS = {
    'mixed':     {'warmup': 2, 'technical': 5, 'project': 2, 'hr': 3, 'closing': 1},
    'technical': {'warmup': 1, 'technical': 8, 'project': 2, 'hr': 1, 'closing': 1},
    'hr':        {'warmup': 1, 'technical': 2, 'project': 1, 'hr': 6, 'closing': 1},
    'project':   {'warmup': 1, 'technical': 3, 'project': 5, 'hr': 2, 'closing': 1},
    'coding':    {'warmup': 1, 'technical': 6, 'project': 2, 'hr': 1, 'closing': 1},
}

# Answer quality thresholds
GOOD_ANSWER_THRESHOLD = 0.65    # above this → may increase difficulty or follow up harder
WEAK_ANSWER_THRESHOLD = 0.35    # below this → follow up with clarification


@dataclass
class TurnDecision:
    """The engine's decision for the next question."""
    question_text: str
    phase: str
    topic: str
    difficulty_level: str
    question_type: str
    expected_concepts: list[str]
    is_follow_up: bool
    follow_up_reason: Optional[str]   # 'weak_answer' | 'strong_answer' | None
    should_end_interview: bool


@dataclass
class SessionContext:
    """Current state of an interview session used to make decisions."""
    session_type: str
    domain: str               # target role domain
    difficulty: str           # session difficulty
    current_phase: str
    turn_number: int
    questions_in_phase: int   # questions asked so far in current phase
    last_answer_score: Optional[float]
    last_question_text: str
    last_question_entry: Optional[QuestionEntry]
    asked_question_texts: set[str]
    phase_scores: dict[str, list[float]]   # phase → list of scores
    candidate_name: str = ""
    target_role_name: str = ""
    resume_skills: list[str] = field(default_factory=list)
    resume_projects: list[str] = field(default_factory=list)
    last_answer_text: str = ""


class AdaptiveInterviewEngine:
    """
    Determines the next interview action based on full session state.
    Uses dynamic LLM question generation with conversational progression.
    """

    def decide_next_turn(self, ctx: SessionContext) -> TurnDecision:
        """
        Main decision function. Returns what question to ask next.
        Called after each student response (or at session start).
        """
        # ── 1. Turn 1 is ALWAYS the welcoming personal introduction ───────────
        if ctx.turn_number == 0:
            intro_q = generate_llm_interview_question(
                candidate_name=ctx.candidate_name,
                target_role=ctx.target_role_name or ctx.domain,
                resume_skills=ctx.resume_skills,
                resume_projects=ctx.resume_projects,
                current_phase="warmup",
                turn_number=1,
                difficulty="easy",
            )
            return TurnDecision(
                question_text=intro_q["question_text"],
                phase="warmup",
                topic=intro_q.get("topic", "introduction"),
                difficulty_level="easy",
                question_type="situational",
                expected_concepts=intro_q.get("expected_concepts", ["name", "background", "education", "goals", "skills"]),
                is_follow_up=False,
                follow_up_reason=None,
                should_end_interview=False,
            )

        # ── 2. Check if interview should end ───────────────────────────────────
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

        # ── 3. Determine active phase and adaptive difficulty ──────────────────
        next_phase = self._maybe_advance_phase(ctx)
        active_phase = next_phase or ctx.current_phase
        diff = self._adaptive_difficulty(ctx)

        # ── 4. Generate next question dynamically via LLM ──────────────────────
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
        )

        return TurnDecision(
            question_text=llm_q["question_text"],
            phase=active_phase,
            topic=llm_q.get("topic", active_phase),
            difficulty_level=diff,
            question_type=llm_q.get("question_type", self._infer_type(active_phase)),
            expected_concepts=llm_q.get("expected_concepts", []),
            is_follow_up=True if ctx.turn_number >= 1 else False,
            follow_up_reason="strong_answer" if (ctx.last_answer_score or 0) >= GOOD_ANSWER_THRESHOLD else ("weak_answer" if (ctx.last_answer_score or 0) < WEAK_ANSWER_THRESHOLD else None),
            should_end_interview=False,
        )

    # ── Private helpers ────────────────────────────────────────────────────────

    def _should_end(self, ctx: SessionContext) -> bool:
        """Return True when we've reached the closing phase limit."""
        if ctx.current_phase == 'closing' and ctx.questions_in_phase >= 1:
            return True
        total_limit = sum(
            PHASE_QUESTION_COUNTS.get(ctx.session_type, PHASE_QUESTION_COUNTS['mixed']).values()
        )
        return ctx.turn_number >= total_limit

    def _phase_limit(self, ctx: SessionContext) -> int:
        counts = PHASE_QUESTION_COUNTS.get(ctx.session_type, PHASE_QUESTION_COUNTS['mixed'])
        return counts.get(ctx.current_phase, 3)

    def _maybe_advance_phase(self, ctx: SessionContext) -> Optional[str]:
        """Return the next phase name if we should advance, else None."""
        limit = self._phase_limit(ctx)
        if ctx.questions_in_phase >= limit:
            current_idx = PHASE_SEQUENCE.index(ctx.current_phase) if ctx.current_phase in PHASE_SEQUENCE else 0
            if current_idx < len(PHASE_SEQUENCE) - 1:
                return PHASE_SEQUENCE[current_idx + 1]
        return None

    def _adaptive_difficulty(self, ctx: SessionContext) -> str:
        """Adjust difficulty based on recent performance."""
        if ctx.session_type == 'technical' or ctx.session_type == 'mixed':
            scores = ctx.phase_scores.get(ctx.current_phase, [])
            if len(scores) >= 2:
                recent_avg = sum(scores[-2:]) / 2
                if recent_avg >= GOOD_ANSWER_THRESHOLD:
                    return self._next_difficulty(ctx.difficulty)
                elif recent_avg < WEAK_ANSWER_THRESHOLD:
                    return self._prev_difficulty(ctx.difficulty)
        # Map session difficulty to question difficulty
        return {'beginner': 'easy', 'intermediate': 'medium', 'advanced': 'hard'}.get(
            ctx.difficulty, 'medium'
        )

    def _next_difficulty(self, current: str) -> str:
        return {'beginner': 'medium', 'easy': 'medium', 'intermediate': 'hard',
                'medium': 'hard', 'advanced': 'hard', 'hard': 'hard'}.get(current, 'medium')

    def _prev_difficulty(self, current: str) -> str:
        return {'advanced': 'medium', 'hard': 'medium', 'intermediate': 'easy',
                'medium': 'easy', 'beginner': 'easy', 'easy': 'easy'}.get(current, 'easy')

    def _pick_question(self, phase: str, ctx: SessionContext) -> Optional[QuestionEntry]:
        """Pick an unasked question from the given phase."""
        if phase == 'warmup':
            pool = WARMUP_QUESTIONS
        elif phase == 'technical':
            diff = self._adaptive_difficulty(ctx)
            pool = get_technical_questions(ctx.domain, diff)
            if not pool:
                pool = get_technical_questions(ctx.domain, 'medium')
        elif phase == 'hr':
            pool = HR_QUESTIONS
        elif phase == 'project':
            pool = PROJECT_QUESTIONS
        elif phase == 'closing':
            pool = CLOSING_QUESTIONS
        else:
            pool = WARMUP_QUESTIONS

        # Filter out already-asked questions
        available = [q for q in pool if q['text'] not in ctx.asked_question_texts]
        if not available:
            # All questions asked — reset and reuse (rephrasing is optional)
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


def evaluate_answer_quality(answer_text: str, expected_concepts: list[str]) -> float:
    """
    Heuristically score a text answer against expected concepts.
    Returns a float 0.0–1.0.

    This is a keyword-coverage heuristic. In Phase 6, this is replaced
    by an LLM evaluation call — the interface stays identical.
    """
    if not answer_text or not answer_text.strip():
        return 0.0

    answer_lower = answer_text.lower()
    word_count = len(answer_text.split())

    # Length score (longer answers tend to be more complete)
    length_score = min(word_count / 80, 1.0)   # 80+ words = full marks for length

    # Concept coverage score
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
        concept_score = 0.5   # no concepts to check — neutral

    # Combine: 40% length, 60% concept coverage
    raw_score = 0.4 * length_score + 0.6 * concept_score

    # Minimum score for any answer (student attempted to respond)
    return max(round(raw_score, 2), 0.05)


def build_ai_feedback(
    question_text: str,
    answer_text: str,
    expected_concepts: list[str],
    score: float,
    phase: str,
) -> str:
    """
    Generate brief AI feedback for a student response.
    Rule-based for now; LLM-based in Phase 6.
    """
    if score >= GOOD_ANSWER_THRESHOLD:
        quality = "Strong answer"
        prefix = "Good response! "
    elif score >= WEAK_ANSWER_THRESHOLD:
        quality = "Adequate answer"
        prefix = "Decent answer. "
    else:
        quality = "Needs improvement"
        prefix = "Your answer could be stronger. "

    # Find which concepts were missed
    answer_lower = answer_text.lower()
    missed = [
        c for c in expected_concepts
        if not any(kw.lower() in answer_lower for kw in c.split() if len(kw) > 3)
    ]

    if missed and score < GOOD_ANSWER_THRESHOLD:
        missed_str = ', '.join(missed[:3])
        return f"{prefix}Consider addressing these concepts in your answer: {missed_str}."
    elif score >= GOOD_ANSWER_THRESHOLD:
        return f"{prefix}You covered the key concepts well."
    else:
        return f"{prefix}Try to be more specific and structured in your response."

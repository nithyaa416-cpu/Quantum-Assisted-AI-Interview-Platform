"""
Assessment & Report Generation Service.

Aggregates:
1. Technical, conceptual, and problem-solving responses from InterviewSession turns
2. Coding phase submissions & test execution metrics (if applicable)
3. Speech & Voice analysis: Fluency (WPM), articulation quality, pitch modulation dynamics
4. Behavioral & Facial analysis: Eye contact %, posture stability, facial confidence, expression
5. Proctoring & Integrity audit: Single-human compliance, mobile phone flags, tab switches

Produces:
- Genuine, uninflated Assessment record with multi-dimensional scores (0.00–1.00)
- Accurate evaluation: unanswered questions and silence score 0.00 (NOT 60% or 70%)
- Structured strengths (only verified >= 70%) and diagnostic improvement areas
- Targeted SkillGap records for feeding the QAOA quantum preparation optimizer
"""
import logging
import re
from decimal import Decimal
from typing import Optional, Dict, Any, List
from django.utils import timezone

from apps.sessions.models import InterviewSession, StudentResponse, InterviewQuestion
from apps.assessments.models import Assessment, SkillGap, CodingSubmission

logger = logging.getLogger(__name__)

# Noise tokens that do not constitute a real answer
_NOISE_TOKENS = frozenset({
    'uh', 'um', 'er', 'hmm', 'hm', 'ah', 'oh', 'okay', 'ok',
    'yeah', 'yes', 'no', 'yep', 'nope', 'right', 'sure', 'fine',
})


def _is_meaningful(text: str) -> bool:
    """Deterministically check if text has substantive candidate answer content."""
    if not text:
        return False
    clean = re.sub(r"[^\w\s']", ' ', text.lower()).strip()
    if not clean:
        return False
    tokens = [t for t in clean.split() if t]
    meaningful = [t for t in tokens if t not in _NOISE_TOKENS and len(t) > 1]
    return len(meaningful) >= 3


def generate_assessment_report(
    session: InterviewSession,
    speech_metrics: Optional[Dict[str, Any]] = None,
    behavioural_metrics: Optional[Dict[str, Any]] = None,
) -> Assessment:
    """
    Generate or update the Assessment report for a completed InterviewSession.
    
    Guarantees genuine, uninflated scoring:
    - If a question was asked and left unanswered (or answered with silence/noise), it scores 0.00.
    - If the candidate answered zero questions, technical, communication, and overall scores are 0.00 (0%).
    - Speech fluency and behavioral composure are scaled by actual participation; ghost/unanswered
      sessions do not receive inflated default marks.
    """
    speech_metrics = speech_metrics or {}
    behavioural_metrics = behavioural_metrics or {}

    questions = list(session.questions.all())
    responses = list(session.responses.select_related('question').all())
    coding_submissions = list(session.coding_submissions.all())

    resp_by_qid: Dict[Any, StudentResponse] = {r.question_id: r for r in responses}

    # ── 1. Evaluate Every Question Asked in Session ───────────────────────────
    tech_scores: List[float] = []
    prob_scores: List[float] = []
    comm_scores: List[float] = []
    topic_scores: Dict[str, List[float]] = {}

    meaningful_answers_count = 0
    total_words_spoken = 0

    if questions:
        for q in questions:
            topic = q.topic or 'General'
            phase = q.phase or 'technical'

            r = resp_by_qid.get(q.id)
            if r is not None:
                resp_text = (getattr(r, 'transcript', '') or getattr(r, 'response_text', '') or '').strip()
                words = len(resp_text.split())
                total_words_spoken += words

                # If answer was meaningful and had positive score
                if _is_meaningful(resp_text) and r.score is not None and float(r.score) > 0:
                    meaningful_answers_count += 1
                    q_score = float(r.score)
                else:
                    # Explicit silence, noise, or zero score
                    q_score = 0.0
            else:
                # Question was presented to candidate, but never answered (abandoned/skipped)
                q_score = 0.0
                words = 0

            topic_scores.setdefault(topic, []).append(q_score)

            # Route by phase
            if phase in ('technical', 'warmup'):
                tech_scores.append(q_score)
            elif phase in ('project', 'coding'):
                prob_scores.append(q_score)
                tech_scores.append(q_score)
            elif phase == 'hr':
                comm_scores.append(q_score)
            else:
                tech_scores.append(q_score)

            # Verbal answer contribution to communication
            if words >= 40 and q_score > 0:
                comm_scores.append(min(1.0, q_score * 0.7 + 0.3))
            elif words >= 15 and q_score > 0:
                comm_scores.append(min(1.0, q_score * 0.6 + 0.2))
            elif words >= 5 and q_score > 0:
                comm_scores.append(q_score * 0.5)
            else:
                comm_scores.append(0.0)
    else:
        # Fallback if questions list is empty: read responses directly
        for r in responses:
            q_score = float(r.score) if r.score is not None else 0.0
            resp_text = (getattr(r, 'transcript', '') or getattr(r, 'response_text', '') or '').strip()
            words = len(resp_text.split())
            total_words_spoken += words
            if _is_meaningful(resp_text) and q_score > 0:
                meaningful_answers_count += 1

            topic = r.question.topic if r.question and r.question.topic else 'General'
            topic_scores.setdefault(topic, []).append(q_score)
            tech_scores.append(q_score)

    total_q_count = len(questions) or len(responses)
    participation_ratio = (meaningful_answers_count / total_q_count) if total_q_count > 0 else 0.0

    # ── 2. Genuine Technical & Problem-Solving Averages ──────────────────────
    if tech_scores:
        avg_tech = sum(tech_scores) / len(tech_scores)
    else:
        avg_tech = 0.0

    if prob_scores:
        avg_prob = sum(prob_scores) / len(prob_scores)
    else:
        avg_prob = avg_tech

    # ── 3. Coding Assessment Scoring (if coding occurred) ────────────────────
    coding_score_val: Optional[Decimal] = None
    if coding_submissions:
        c_scores = [float(cs.overall_score) for cs in coding_submissions if cs.overall_score is not None]
        if c_scores:
            coding_score_val = Decimal(f"{sum(c_scores) / len(c_scores):.2f}")
        else:
            coding_score_val = Decimal("0.00")

    # ── 4. Voice & Speech Analysis Scoring ───────────────────────────────────
    # If candidate never spoke (total_words == 0 or meaningful_answers == 0), speech is 0
    wpm = int(speech_metrics.get('words_per_minute', 0))
    fluency_raw = float(speech_metrics.get('fluency_score', 0))
    modulation_raw = float(speech_metrics.get('pitch_modulation_score', 0))

    if total_words_spoken == 0 or meaningful_answers_count == 0:
        communication_score = Decimal("0.00")
        fluency_factor = 0.0
        modulation_factor = 0.0
    else:
        fluency_factor = max(0.0, min(1.0, fluency_raw / 100.0))
        modulation_factor = max(0.0, min(1.0, modulation_raw / 100.0))

        if comm_scores:
            verbal_answer_avg = sum(comm_scores) / len(comm_scores)
            comm_score_calc = (verbal_answer_avg * 0.60) + (fluency_factor * 0.25) + (modulation_factor * 0.15)
        else:
            comm_score_calc = (fluency_factor * 0.65) + (modulation_factor * 0.35)

        # Scale by participation so saying 3 words doesn't give full fluency marks
        comm_score_calc = comm_score_calc * min(1.0, total_words_spoken / 40.0)
        communication_score = Decimal(f"{max(0.0, min(1.0, comm_score_calc)):.2f}")

    # ── 5. Behavioral & Facial Analysis Scoring ──────────────────────────────
    eye_contact_pct = float(behavioural_metrics.get('eye_contact_percentage', 0))
    confidence_raw = float(behavioural_metrics.get('confidence_score', 0))
    posture_raw = float(behavioural_metrics.get('posture_stability_score', 0))

    if total_q_count == 0 or meaningful_answers_count == 0:
        # Ghost / abandoned session: zero behavioral score
        behavioural_score = Decimal("0.00")
        eye_factor = 0.0
        confidence_factor = 0.0
        posture_factor = 0.0
    else:
        eye_factor = max(0.0, min(1.0, eye_contact_pct / 100.0))
        confidence_factor = max(0.0, min(1.0, confidence_raw / 100.0))
        posture_factor = max(0.0, min(1.0, posture_raw / 100.0))

        raw_beh = (eye_factor * 0.40) + (confidence_factor * 0.35) + (posture_factor * 0.25)

        phone_incidents = int(behavioural_metrics.get('phone_detected_incidents', 0))
        multi_faces = int(behavioural_metrics.get('multiple_faces_incidents', 0))
        strikes = int(behavioural_metrics.get('proctoring_strikes', 0))

        penalty = (phone_incidents * 0.25) + (min(multi_faces, 3) * 0.15) + (min(strikes, 4) * 0.10)
        beh_calc = max(0.0, (raw_beh - penalty) * participation_ratio)
        behavioural_score = Decimal(f"{beh_calc:.2f}")

    # ── 6. Overall Multi-Modal Score Calculation ─────────────────────────────
    technical_score = Decimal(f"{max(0.0, min(1.0, avg_tech)):.2f}")
    problem_solving_score = Decimal(f"{max(0.0, min(1.0, avg_prob)):.2f}")

    if meaningful_answers_count == 0 and not coding_submissions:
        # Absolute zero: candidate answered nothing
        overall_score = Decimal("0.00")
    else:
        if coding_score_val is not None:
            overall_calc = (
                float(technical_score) * 0.35 +
                float(coding_score_val) * 0.25 +
                float(problem_solving_score) * 0.15 +
                float(communication_score) * 0.15 +
                float(behavioural_score) * 0.10
            )
        else:
            overall_calc = (
                float(technical_score) * 0.40 +
                float(problem_solving_score) * 0.25 +
                float(communication_score) * 0.20 +
                float(behavioural_score) * 0.15
            )
        overall_score = Decimal(f"{max(0.0, min(1.0, overall_calc)):.2f}")

    # ── 7. Synthesize Personalized Strengths ─────────────────────────────────
    strengths: List[str] = []

    # High-scoring topics (verified >= 70%)
    for topic, sc_list in topic_scores.items():
        if sc_list and (sum(sc_list) / len(sc_list)) >= 0.70:
            avg_sc = int((sum(sc_list) / len(sc_list)) * 100)
            strengths.append(f"Demonstrated solid conceptual mastery and depth in {topic} ({avg_sc}% score).")

    # Speech fluency & modulation highlights — ONLY if speech actually occurred
    if meaningful_answers_count >= 1 and total_words_spoken >= 40:
        if 110 <= wpm <= 165:
            strengths.append(f"Fluent verbal communication with an ideal pace of {wpm} WPM.")
        if modulation_factor >= 0.75:
            strengths.append("Engaging vocal variety and dynamic pitch modulation, avoiding monotone delivery.")
        elif modulation_factor >= 0.60:
            strengths.append("Clear and audible speech delivery across technical questions.")

    # Behavioral & facial poise — ONLY if candidate participated
    if meaningful_answers_count >= 1:
        if eye_factor >= 0.75:
            strengths.append(f"Consistent eye contact maintained ({int(eye_contact_pct)}%), displaying composure.")
        if confidence_factor >= 0.75:
            strengths.append("High poise and upright posture maintained under live interview conditions.")
        if behavioural_metrics.get('phone_detected_incidents', 0) == 0 and behavioural_metrics.get('proctoring_strikes', 0) == 0:
            strengths.append("Strict proctoring compliance verified with zero room or device infractions.")

    if not strengths:
        if meaningful_answers_count == 0:
            pass  # Leave empty: no strengths demonstrated when zero questions were answered
        else:
            strengths.append("Active interview attempt recorded. Continue practicing to build demonstrable strengths.")

    # ── 8. Synthesize Improvement Areas & Skill Gaps ─────────────────────────
    improvement_areas: List[Dict[str, str]] = []
    gaps_to_create: List[Dict[str, Any]] = []

    # Check every topic asked
    for topic, sc_list in topic_scores.items():
        avg = sum(sc_list) / len(sc_list) if sc_list else 0.0
        if avg < 0.65:
            priority = 'high' if avg < 0.40 else 'medium'
            if avg == 0.0:
                improvement_areas.append({
                    'area': f"Unanswered Topic: {topic}",
                    'priority': 'high',
                    'recommendation': f"You did not provide an answer for {topic}. Silence or leaving questions blank yields 0 marks. Practice speaking through your approach even when partially unsure."
                })
            else:
                improvement_areas.append({
                    'area': f"Technical Depth in {topic}",
                    'priority': priority,
                    'recommendation': f"Scored {int(avg * 100)}% in {topic}. Review core fundamentals, edge cases, and architectural trade-offs."
                })

            gaps_to_create.append({
                'skill_name': topic,
                'category': 'concept',
                'current_level': Decimal(f"{avg:.2f}"),
                'target_level': Decimal("0.85"),
                'priority': priority,
            })

    # Participation & Communication gaps
    if meaningful_answers_count == 0:
        improvement_areas.append({
            'area': "Active Verbal Participation",
            'priority': 'high',
            'recommendation': "No meaningful answers were recorded. Check your microphone setup, ensure permissions are granted, and speak clearly to receive scoring credit."
        })
    elif total_words_spoken < 30:
        improvement_areas.append({
            'area': "Answer Depth & Elaboration",
            'priority': 'high',
            'recommendation': f"Your answers were very brief ({total_words_spoken} total words). Elaborate using structured reasoning (e.g. state your approach, trade-offs, and complexity)."
        })

    if wpm > 0 and wpm < 100 and meaningful_answers_count >= 1:
        improvement_areas.append({
            'area': "Speaking Tempo & Fluidity",
            'priority': 'medium',
            'recommendation': f"Your speech pace was slightly hesitant ({wpm} WPM). Practice thinking out loud using structured frameworks (STAR or Rule of 3)."
        })
    elif wpm > 175:
        improvement_areas.append({
            'area': "Speech Pacing & Clarity",
            'priority': 'medium',
            'recommendation': f"You spoke quite rapidly ({wpm} WPM). Deliberately introduce brief pauses between major points for clarity."
        })

    if not improvement_areas:
        improvement_areas.append({
            'area': "Advanced Edge Cases",
            'priority': 'low',
            'recommendation': "Continue practicing senior-level architectural trade-offs and latency considerations."
        })

    # ── 9. Detailed Dimension Feedback Narrative ─────────────────────────────
    detailed_feedback = {
        'technical': (
            f"Overall technical score: {int(float(technical_score) * 100)}%. "
            f"You meaningfully answered {meaningful_answers_count} of {total_q_count} questions presented."
        ),
        'communication': (
            f"Communication score: {int(float(communication_score) * 100)}%. "
            f"Total words transcribed: {total_words_spoken}. Speech rate: {wpm} WPM."
        ),
        'behavioural': (
            f"Behavioral poise score: {int(float(behavioural_score) * 100)}%. "
            f"Eye contact ratio: {int(eye_contact_pct)}%. Participation factor: {int(participation_ratio * 100)}%."
        ),
        'proctoring_summary': {
            'status': behavioural_metrics.get('integrity_status', 'verified'),
            'single_human_compliance': f"{behavioural_metrics.get('single_human_compliance', 100)}%",
            'mobile_phone_detected': int(behavioural_metrics.get('phone_detected_incidents', 0)) > 0,
            'phone_incidents_count': int(behavioural_metrics.get('phone_detected_incidents', 0)),
            'multiple_faces_count': int(behavioural_metrics.get('multiple_faces_incidents', 0)),
            'proctoring_strikes': int(behavioural_metrics.get('proctoring_strikes', 0)),
        },
        'quantum_prep_recommendations': (
            f"Identified {len(gaps_to_create)} priority skill gaps to calibrate into your "
            "Quantum (QAOA) preparation roadmap."
        )
    }

    # ── 10. Save or Update Assessment Model ───────────────────────────────────
    assessment, _ = Assessment.objects.update_or_create(
        session=session,
        defaults={
            'overall_score': overall_score,
            'technical_score': technical_score,
            'communication_score': communication_score,
            'behavioural_score': behavioural_score,
            'coding_score': coding_score_val,
            'problem_solving_score': problem_solving_score,
            'strengths': strengths,
            'improvement_areas': improvement_areas,
            'detailed_feedback': detailed_feedback,
            'speech_metrics': speech_metrics,
            'behavioural_metrics': behavioural_metrics,
        }
    )

    # ── 11. Populate SkillGap Records for Student ─────────────────────────────
    student_profile = session.student
    if student_profile and gaps_to_create:
        for gap_info in gaps_to_create:
            SkillGap.objects.update_or_create(
                student=student_profile,
                skill_name=gap_info['skill_name'],
                resolved_at__isnull=True,
                defaults={
                    'assessment': assessment,
                    'category': gap_info['category'],
                    'current_level': gap_info['current_level'],
                    'target_level': gap_info['target_level'],
                    'priority': gap_info['priority'],
                }
            )

    logger.info(
        "Genuine assessment generated: session=%s overall=%s tech=%s answered=%d/%d",
        session.id, overall_score, technical_score, meaningful_answers_count, total_q_count
    )

    return assessment

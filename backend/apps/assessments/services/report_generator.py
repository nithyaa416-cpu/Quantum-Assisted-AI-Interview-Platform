"""
Assessment & Report Generation Service.

Aggregates:
1. Technical, conceptual, and problem-solving responses from InterviewSession turns
2. Coding phase submissions & test execution metrics (if applicable)
3. Speech & Voice analysis: Fluency (WPM), articulation quality, pitch modulation dynamics
4. Behavioral & Facial analysis: Eye contact %, posture stability, facial confidence, expression
5. Proctoring & Integrity audit: Single-human compliance, mobile phone flags, tab switches

Produces:
- Assessment record with multi-dimensional scores (0.00–1.00)
- Structured strengths and improvement recommendations
- Targeted SkillGap records for feeding the QAOA quantum preparation optimizer
"""
import logging
from decimal import Decimal
from typing import Optional, Dict, Any, List
from django.utils import timezone

from apps.sessions.models import InterviewSession, CandidateResponse
from apps.assessments.models import Assessment, SkillGap, CodingSubmission

logger = logging.getLogger(__name__)


def generate_assessment_report(
    session: InterviewSession,
    speech_metrics: Optional[Dict[str, Any]] = None,
    behavioural_metrics: Optional[Dict[str, Any]] = None,
) -> Assessment:
    """
    Generate or update the Assessment report for a completed InterviewSession.
    """
    speech_metrics = speech_metrics or {}
    behavioural_metrics = behavioural_metrics or {}

    responses = list(session.responses.select_related('question').all())
    coding_submissions = list(session.coding_submissions.all())

    # ── 1. Technical & Problem-Solving Scoring ────────────────────────────────
    tech_scores: List[float] = []
    prob_scores: List[float] = []
    comm_scores: List[float] = []
    topic_scores: Dict[str, List[float]] = {}

    for r in responses:
        score = float(r.score) if r.score is not None else 0.5
        q = r.question
        phase = q.phase if q else 'technical'
        topic = q.topic if q else 'General'

        topic_scores.setdefault(topic, []).append(score)

        if phase in ('technical', 'warmup'):
            tech_scores.append(score)
        elif phase in ('project', 'coding'):
            prob_scores.append(score)
            tech_scores.append(score)
        elif phase == 'hr':
            comm_scores.append(score)

        # Candidate response length and depth contributes to baseline communication
        words = len((r.response_text or '').split())
        if words >= 40:
            comm_scores.append(min(1.0, score * 0.7 + 0.3))
        elif words >= 15:
            comm_scores.append(min(1.0, score * 0.6 + 0.2))
        else:
            comm_scores.append(max(0.2, score * 0.5))

    avg_tech = sum(tech_scores) / len(tech_scores) if tech_scores else 0.65
    avg_prob = sum(prob_scores) / len(prob_scores) if prob_scores else avg_tech

    # ── 2. Coding Assessment Scoring (if coding occurred) ────────────────────
    coding_score_val: Optional[Decimal] = None
    if coding_submissions:
        c_scores = [float(cs.overall_score) for cs in coding_submissions if cs.overall_score is not None]
        if c_scores:
            coding_score_val = Decimal(f"{sum(c_scores) / len(c_scores):.2f}")
        else:
            coding_score_val = Decimal("0.50")

    # ── 3. Voice & Speech Analysis Scoring ───────────────────────────────────
    # speech_metrics: words_per_minute, fluency_score (0-100), pitch_modulation_score (0-100)
    fluency_raw = speech_metrics.get('fluency_score', 80)
    modulation_raw = speech_metrics.get('pitch_modulation_score', 80)
    wpm = speech_metrics.get('words_per_minute', 130)

    # Convert 0-100 to 0.00-1.00
    fluency_factor = max(0.2, min(1.0, float(fluency_raw) / 100.0))
    modulation_factor = max(0.2, min(1.0, float(modulation_raw) / 100.0))

    if comm_scores:
        verbal_answer_avg = sum(comm_scores) / len(comm_scores)
        comm_score_calc = (verbal_answer_avg * 0.40) + (fluency_factor * 0.35) + (modulation_factor * 0.25)
    else:
        comm_score_calc = (fluency_factor * 0.55) + (modulation_factor * 0.45)

    communication_score = Decimal(f"{max(0.1, min(1.0, comm_score_calc)):.2f}")

    # ── 4. Behavioral & Facial Analysis Scoring ──────────────────────────────
    # behavioural_metrics: eye_contact_percentage, confidence_score, posture_stability_score
    eye_contact_pct = behavioural_metrics.get('eye_contact_percentage', 85)
    confidence_raw = behavioural_metrics.get('confidence_score', 82)
    posture_raw = behavioural_metrics.get('posture_stability_score', 88)

    eye_factor = max(0.0, min(1.0, float(eye_contact_pct) / 100.0))
    confidence_factor = max(0.0, min(1.0, float(confidence_raw) / 100.0))
    posture_factor = max(0.0, min(1.0, float(posture_raw) / 100.0))

    beh_calc = (eye_factor * 0.40) + (confidence_factor * 0.35) + (posture_factor * 0.25)

    # Proctoring Deductions (Phone detected, Multiple humans, Tab switches)
    phone_incidents = behavioural_metrics.get('phone_detected_incidents', 0)
    multi_faces = behavioural_metrics.get('multiple_faces_incidents', 0)
    strikes = behavioural_metrics.get('proctoring_strikes', 0)

    penalty = (phone_incidents * 0.20) + (min(multi_faces, 3) * 0.10) + (min(strikes, 4) * 0.05)
    beh_calc = max(0.15, beh_calc - penalty)
    behavioural_score = Decimal(f"{beh_calc:.2f}")

    # ── 5. Overall Multi-Modal Score Calculation ─────────────────────────────
    technical_score = Decimal(f"{max(0.1, min(1.0, avg_tech)):.2f}")
    problem_solving_score = Decimal(f"{max(0.1, min(1.0, avg_prob)):.2f}")

    if coding_score_val is not None:
        overall_calc = (
            float(technical_score) * 0.30 +
            float(coding_score_val) * 0.20 +
            float(communication_score) * 0.20 +
            float(behavioural_score) * 0.15 +
            float(problem_solving_score) * 0.15
        )
    else:
        overall_calc = (
            float(technical_score) * 0.35 +
            float(communication_score) * 0.25 +
            float(behavioural_score) * 0.20 +
            float(problem_solving_score) * 0.20
        )

    overall_score = Decimal(f"{max(0.1, min(1.0, overall_calc)):.2f}")

    # ── 6. Synthesize Personalized Strengths ─────────────────────────────────
    strengths: List[str] = []

    # High-scoring topics
    for topic, sc_list in topic_scores.items():
        if len(sc_list) > 0 and (sum(sc_list) / len(sc_list)) >= 0.70:
            strengths.append(f"Demonstrated solid conceptual mastery and depth in {topic}.")

    # Speech fluency & modulation highlights
    if wpm >= 110 and wpm <= 165:
        strengths.append(f"Fluent verbal communication with an ideal pace of {wpm} WPM.")
    if modulation_factor >= 0.75:
        strengths.append("Engaging vocal variety and dynamic pitch modulation, avoiding monotone delivery.")
    elif modulation_factor >= 0.60:
        strengths.append("Clear and audible speech delivery across technical questions.")

    # Behavioral & facial poise
    if eye_factor >= 0.75:
        strengths.append(f"Consistent eye contact maintained ({eye_contact_pct}%), displaying high composure and attentiveness.")
    if confidence_factor >= 0.75:
        strengths.append("High poise and upright posture maintained under live interview pressure.")
    if phone_incidents == 0 and multi_faces == 0 and strikes == 0:
        strengths.append("Strict proctoring compliance verified with zero room or device infractions.")

    if not strengths:
        strengths.append("Engaged actively and attempted all technical interview questions.")

    # ── 7. Synthesize Improvement Areas & Skill Gaps ─────────────────────────
    improvement_areas: List[Dict[str, str]] = []
    gaps_to_create: List[Dict[str, Any]] = []

    # Identify low scoring topics (< 0.65)
    for topic, sc_list in topic_scores.items():
        avg = sum(sc_list) / len(sc_list) if sc_list else 0.5
        if avg < 0.65:
            priority = 'high' if avg < 0.40 else 'medium'
            improvement_areas.append({
                'area': f"Technical Depth in {topic}",
                'priority': priority,
                'recommendation': f"Review core fundamentals, internal mechanisms, and standard interview trade-offs for {topic}."
            })
            gaps_to_create.append({
                'skill_name': topic,
                'category': 'concept',
                'current_level': Decimal(f"{avg:.2f}"),
                'target_level': Decimal("0.85"),
                'priority': priority,
            })

    # Speech & Communication improvement points
    if wpm < 100:
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

    if modulation_factor < 0.65:
        improvement_areas.append({
            'area': "Voice Modulation & Emphasis",
            'priority': 'medium',
            'recommendation': "Add vocal inflection and dynamic range to emphasize critical architectural decisions and results."
        })

    # Behavioral / Proctoring improvement points
    if eye_factor < 0.65:
        improvement_areas.append({
            'area': "Camera Eye Contact",
            'priority': 'medium',
            'recommendation': f"Eye contact dropped to {eye_contact_pct}%. Position your camera near eye-level and maintain gaze toward the interviewer."
        })

    if phone_incidents > 0:
        improvement_areas.append({
            'area': "Proctoring Integrity (Mobile Phone Detected)",
            'priority': 'high',
            'recommendation': "Keep mobile phones and secondary screens completely outside the interview room."
        })

    if multi_faces > 0:
        improvement_areas.append({
            'area': "Private Environment",
            'priority': 'high',
            'recommendation': "Ensure you are alone in a quiet, closed room to avoid multiple-face flags."
        })

    # Fallback if no issues found
    if not improvement_areas:
        improvement_areas.append({
            'area': "Advanced Edge Cases",
            'priority': 'low',
            'recommendation': "Continue practicing senior-level architectural trade-offs and latency considerations."
        })

    # ── 8. Detailed Dimension Feedback Narrative ─────────────────────────────
    detailed_feedback = {
        'technical': (
            f"Overall technical performance achieved {int(float(technical_score) * 100)}%. "
            f"You tackled {len(responses)} verbal questions across multiple interview topics."
        ),
        'communication': (
            f"Communication score: {int(float(communication_score) * 100)}%. "
            f"Speech rate averaged {wpm} WPM with a fluency index of {fluency_raw}%. "
            f"Voice modulation reached {modulation_raw}% dynamic range."
        ),
        'behavioural': (
            f"Behavioral poise score: {int(float(behavioural_score) * 100)}%. "
            f"Eye contact was maintained {eye_contact_pct}% of the interview duration. "
            f"Facial confidence registered at {confidence_raw}% with posture stability at {posture_raw}%."
        ),
        'proctoring_summary': {
            'status': behavioural_metrics.get('integrity_status', 'verified'),
            'single_human_compliance': f"{behavioural_metrics.get('single_human_compliance', 100)}%",
            'mobile_phone_detected': phone_incidents > 0,
            'phone_incidents_count': phone_incidents,
            'multiple_faces_count': multi_faces,
            'proctoring_strikes': strikes,
        },
        'quantum_prep_recommendations': (
            f"Identified {len(gaps_to_create)} priority skill gaps to calibrate into your "
            "Quantum (QAOA) preparation roadmap."
        )
    }

    # ── 9. Save or Update Assessment Model ───────────────────────────────────
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

    # ── 10. Populate SkillGap Records for Student ─────────────────────────────
    student_profile = session.student
    if student_profile and gaps_to_create:
        for gap_info in gaps_to_create:
            # Avoid duplicating existing unresolved gaps for the same skill
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
        "Assessment generated: session=%s overall=%s tech=%s comm=%s beh=%s",
        session.id, overall_score, technical_score, communication_score, behavioural_score
    )

    return assessment

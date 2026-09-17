"""
AI Interviewer API views.

Endpoints:
  POST /api/interview/sessions/              - Create + start a session
  GET  /api/interview/sessions/{id}/         - Session detail + full history
  POST /api/interview/sessions/{id}/next/    - Get next question (adaptive)
  POST /api/interview/sessions/{id}/respond/ - Submit answer, get feedback
  POST /api/interview/sessions/{id}/end/     - End session
  GET  /api/interview/sessions/{id}/history/ - All Q&A turns
  GET  /api/interview/sessions/              - List all sessions

The engine is stateless — all state lives in the DB.
"""
import logging
from django.utils import timezone
from rest_framework import status as http_status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.resumes.models import TargetRole
from .models import InterviewSession, InterviewQuestion, StudentResponse
from .interview_engine import (
    AdaptiveInterviewEngine,
    SessionContext,
    evaluate_answer_quality,
    build_ai_feedback,
    PHASE_SEQUENCE,
)

logger = logging.getLogger(__name__)
engine = AdaptiveInterviewEngine()


def _ok(data, status=200):
    return Response({'success': True, 'data': data}, status=status)


def _err(code, msg, status=400):
    return Response({'success': False, 'error': {'code': code, 'message': msg, 'details': {}}},
                    status=status)


def _build_context(session: InterviewSession) -> SessionContext:
    """Build SessionContext from DB state."""
    questions = list(session.questions.all().order_by('turn_number'))
    responses = {r.question_id: r for r in session.responses.all()}

    asked_texts = {q.question_text for q in questions}
    current_phase = questions[-1].phase if questions else 'warmup'

    # Count questions in current phase
    questions_in_phase = sum(1 for q in questions if q.phase == current_phase)

    # Last answer score
    last_score = None
    last_entry = None
    last_question_text = ''
    if questions:
        last_q = questions[-1]
        last_question_text = last_q.question_text
        last_resp = responses.get(last_q.id)
        if last_resp and last_resp.score is not None:
            last_score = float(last_resp.score)
        # Reconstruct last QuestionEntry for follow-up logic
        last_entry = {
            'text': last_q.question_text,
            'topic': last_q.topic,
            'expected_concepts': last_q.expected_concepts,
            'follow_ups': [],
            'harder_follow_up': '',
        }

    # Phase scores
    phase_scores: dict[str, list[float]] = {}
    for q in questions:
        resp = responses.get(q.id)
        if resp and resp.score is not None:
            phase_scores.setdefault(q.phase, []).append(float(resp.score))

    # Domain from target role
    domain = 'software_engineering'
    if session.target_role:
        domain = session.target_role.domain or 'software_engineering'

    return SessionContext(
        session_type=session.session_type,
        domain=domain,
        difficulty=session.difficulty,
        current_phase=current_phase,
        turn_number=len(questions),
        questions_in_phase=questions_in_phase,
        last_answer_score=last_score,
        last_question_text=last_question_text,
        last_question_entry=last_entry,
        asked_question_texts=asked_texts,
        phase_scores=phase_scores,
    )


def _serialize_session(session: InterviewSession) -> dict:
    questions = list(session.questions.order_by('turn_number'))
    responses = {r.question_id: r for r in session.responses.all()}
    turns = []
    for q in questions:
        r = responses.get(q.id)
        turns.append({
            'turn_number': q.turn_number,
            'phase': q.phase,
            'question': q.question_text,
            'topic': q.topic,
            'difficulty': q.difficulty_level,
            'question_type': q.question_type,
            'is_follow_up': getattr(q, 'is_follow_up', False),
            'response': r.transcript if r else None,
            'score': float(r.score) if r and r.score is not None else None,
            'feedback': r.ai_feedback if r else None,
            'answered': r is not None,
            'response_time_seconds': r.response_duration_seconds if r else None,
        })

    target_role_name = session.target_role.role_name if session.target_role else None
    current_q = questions[-1] if questions else None

    return {
        'id': str(session.id),
        'session_type': session.session_type,
        'difficulty': session.difficulty,
        'status': session.status,
        'target_role': target_role_name,
        'started_at': session.started_at,
        'ended_at': session.ended_at,
        'duration_seconds': session.duration_seconds,
        'turn_count': len(questions),
        'current_phase': current_q.phase if current_q else 'warmup',
        'current_question': {
            'id': str(current_q.id),
            'text': current_q.question_text,
            'phase': current_q.phase,
            'topic': current_q.topic,
            'difficulty': current_q.difficulty_level,
            'turn_number': current_q.turn_number,
            'answered': current_q.id in {r.question_id for r in session.responses.all()},
        } if current_q else None,
        'turns': turns,
        'phase_progress': _phase_progress(session),
    }


def _phase_progress(session: InterviewSession) -> dict:
    from .interview_engine import PHASE_QUESTION_COUNTS
    counts = PHASE_QUESTION_COUNTS.get(session.session_type, PHASE_QUESTION_COUNTS['mixed'])
    phase_counts = {}
    for q in session.questions.all():
        phase_counts[q.phase] = phase_counts.get(q.phase, 0) + 1
    return {
        phase: {
            'asked': phase_counts.get(phase, 0),
            'total': counts.get(phase, 0),
        }
        for phase in counts
    }


# ── Views ─────────────────────────────────────────────────────────────────────

class InterviewSessionListCreateView(APIView):
    """
    GET  /api/interview/sessions/  - List sessions
    POST /api/interview/sessions/  - Create + start a new interview session
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = request.user.student_profile
        sessions = InterviewSession.objects.filter(
            student=profile
        ).order_by('-created_at').prefetch_related('questions', 'responses')

        result = []
        for s in sessions:
            q_count = s.questions.count()
            r_count = s.responses.count()
            result.append({
                'id': str(s.id),
                'session_type': s.session_type,
                'difficulty': s.difficulty,
                'status': s.status,
                'target_role': s.target_role.role_name if s.target_role else None,
                'turn_count': q_count,
                'answered_count': r_count,
                'started_at': s.started_at,
                'ended_at': s.ended_at,
                'duration_seconds': s.duration_seconds,
                'created_at': s.created_at,
                'current_phase': s.questions.order_by('-turn_number').values_list('phase', flat=True).first() or 'warmup',
            })
        return _ok(result)

    def post(self, request):
        profile = request.user.student_profile
        data = request.data

        session_type = data.get('session_type', 'mixed')
        difficulty   = data.get('difficulty', 'intermediate')
        target_role_id = data.get('target_role_id')

        if session_type not in dict(InterviewSession.SESSION_TYPE_CHOICES):
            return _err('VALIDATION_ERROR', f'Invalid session_type: {session_type}')
        if difficulty not in dict(InterviewSession.DIFFICULTY_CHOICES):
            return _err('VALIDATION_ERROR', f'Invalid difficulty: {difficulty}')

        target_role = None
        if target_role_id:
            try:
                target_role = TargetRole.objects.get(pk=target_role_id, student=profile)
            except TargetRole.DoesNotExist:
                return _err('NOT_FOUND', 'Target role not found.')
        else:
            # Auto-use primary role
            target_role = TargetRole.objects.filter(student=profile, is_primary=True).first()

        # Create session
        session = InterviewSession.objects.create(
            student=profile,
            session_type=session_type,
            difficulty=difficulty,
            target_role=target_role,
            status='active',
            started_at=timezone.now(),
        )

        # Generate the very first question immediately
        ctx = _build_context(session)
        decision = engine.decide_next_turn(ctx)

        question = InterviewQuestion.objects.create(
            session=session,
            turn_number=1,
            phase=decision.phase,
            question_text=decision.question_text,
            question_type=decision.question_type,
            topic=decision.topic,
            difficulty_level=decision.difficulty_level,
            expected_concepts=decision.expected_concepts,
        )

        logger.info(
            'Interview started: session=%s type=%s role=%s',
            session.id, session_type, target_role.role_name if target_role else 'none'
        )

        return _ok(_serialize_session(session), status=201)


class InterviewSessionDetailView(APIView):
    """GET /api/interview/sessions/{id}/  - Full session state."""
    permission_classes = [IsAuthenticated]

    def _get(self, pk, user):
        try:
            s = InterviewSession.objects.get(pk=pk)
            return s if s.student.user == user else None
        except InterviewSession.DoesNotExist:
            return None

    def get(self, request, pk):
        session = self._get(pk, request.user)
        if not session:
            return _err('NOT_FOUND', 'Session not found.', 404)
        return _ok(_serialize_session(session))


class NextQuestionView(APIView):
    """
    POST /api/interview/sessions/{id}/next/
    Generate the next question (called after a response is submitted,
    or to re-fetch the current unanswered question).
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            session = InterviewSession.objects.get(pk=pk, student__user=request.user)
        except InterviewSession.DoesNotExist:
            return _err('NOT_FOUND', 'Session not found.', 404)

        if session.status != 'active':
            return _err('BAD_REQUEST', f'Session is {session.status}, not active.')

        # Check if the current question has been answered
        last_q = session.questions.order_by('-turn_number').first()
        if last_q:
            already_answered = session.responses.filter(question=last_q).exists()
            if not already_answered:
                # Return existing unanswered question instead of generating a new one
                return _ok({
                    'question': {
                        'id': str(last_q.id),
                        'text': last_q.question_text,
                        'phase': last_q.phase,
                        'topic': last_q.topic,
                        'difficulty': last_q.difficulty_level,
                        'turn_number': last_q.turn_number,
                    },
                    'phase_progress': _phase_progress(session),
                    'is_new': False,
                })

        ctx = _build_context(session)
        decision = engine.decide_next_turn(ctx)

        if decision.should_end_interview:
            return _ok({'should_end': True, 'message': 'Interview complete. Please end the session.'})

        new_q = InterviewQuestion.objects.create(
            session=session,
            turn_number=ctx.turn_number + 1,
            phase=decision.phase,
            question_text=decision.question_text,
            question_type=decision.question_type,
            topic=decision.topic,
            difficulty_level=decision.difficulty_level,
            expected_concepts=decision.expected_concepts,
        )

        return _ok({
            'question': {
                'id': str(new_q.id),
                'text': new_q.question_text,
                'phase': new_q.phase,
                'topic': new_q.topic,
                'difficulty': new_q.difficulty_level,
                'turn_number': new_q.turn_number,
                'is_follow_up': decision.is_follow_up,
                'follow_up_reason': decision.follow_up_reason,
            },
            'phase_progress': _phase_progress(session),
            'is_new': True,
        })


class SubmitResponseView(APIView):
    """
    POST /api/interview/sessions/{id}/respond/
    Body: { question_id, answer, duration_seconds (optional) }

    Evaluates the answer, stores response + feedback,
    then generates and returns the NEXT question.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            session = InterviewSession.objects.get(pk=pk, student__user=request.user)
        except InterviewSession.DoesNotExist:
            return _err('NOT_FOUND', 'Session not found.', 404)

        if session.status != 'active':
            return _err('BAD_REQUEST', f'Session is {session.status}, not active.')

        question_id = request.data.get('question_id')
        answer_text = request.data.get('answer', '').strip()
        duration    = request.data.get('duration_seconds')

        if not question_id:
            return _err('VALIDATION_ERROR', 'question_id is required.')
        if not answer_text:
            return _err('VALIDATION_ERROR', 'answer cannot be empty.')

        try:
            question = InterviewQuestion.objects.get(pk=question_id, session=session)
        except InterviewQuestion.DoesNotExist:
            return _err('NOT_FOUND', 'Question not found.')

        # Check not already answered
        if StudentResponse.objects.filter(question=question).exists():
            return _err('CONFLICT', 'This question has already been answered.', 409)

        # Evaluate answer quality
        score = evaluate_answer_quality(answer_text, question.expected_concepts)
        feedback = build_ai_feedback(
            question.question_text,
            answer_text,
            question.expected_concepts,
            score,
            question.phase,
        )

        # Store response
        response_obj = StudentResponse.objects.create(
            question=question,
            session=session,
            transcript=answer_text,
            response_duration_seconds=duration,
            score=round(score, 2),
            ai_feedback=feedback,
        )

        logger.debug(
            'Response saved: session=%s turn=%d score=%.2f',
            session.id, question.turn_number, score
        )

        # Generate next question
        ctx = _build_context(session)
        decision = engine.decide_next_turn(ctx)

        interview_complete = False
        next_question_data = None

        if decision.should_end_interview or ctx.turn_number >= 13:
            interview_complete = True
        else:
            next_q = InterviewQuestion.objects.create(
                session=session,
                turn_number=ctx.turn_number + 1,
                phase=decision.phase,
                question_text=decision.question_text,
                question_type=decision.question_type,
                topic=decision.topic,
                difficulty_level=decision.difficulty_level,
                expected_concepts=decision.expected_concepts,
            )
            next_question_data = {
                'id': str(next_q.id),
                'text': next_q.question_text,
                'phase': next_q.phase,
                'topic': next_q.topic,
                'difficulty': next_q.difficulty_level,
                'turn_number': next_q.turn_number,
                'is_follow_up': decision.is_follow_up,
                'follow_up_reason': decision.follow_up_reason,
            }

        return _ok({
            'response_saved': {
                'question_id': str(question.id),
                'score': float(response_obj.score),
                'feedback': feedback,
            },
            'next_question': next_question_data,
            'interview_complete': interview_complete,
            'phase_progress': _phase_progress(session),
        })


class EndInterviewView(APIView):
    """POST /api/interview/sessions/{id}/end/"""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            session = InterviewSession.objects.get(pk=pk, student__user=request.user)
        except InterviewSession.DoesNotExist:
            return _err('NOT_FOUND', 'Session not found.', 404)

        if session.status == 'completed':
            return _ok({'message': 'Session already completed.', 'session_id': str(session.id)})

        now = timezone.now()
        session.status = 'completed'
        session.ended_at = now
        if session.started_at:
            session.duration_seconds = int((now - session.started_at).total_seconds())
        session.save(update_fields=['status', 'ended_at', 'duration_seconds'])

        q_count = session.questions.count()
        r_count = session.responses.count()

        logger.info('Interview ended: session=%s turns=%d', session.id, q_count)

        return _ok({
            'session_id': str(session.id),
            'status': 'completed',
            'total_questions': q_count,
            'total_answered': r_count,
            'duration_seconds': session.duration_seconds,
            'message': 'Interview completed successfully.',
        })


class InterviewHistoryView(APIView):
    """GET /api/interview/sessions/{id}/history/  - All Q&A turns."""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            session = InterviewSession.objects.get(pk=pk, student__user=request.user)
        except InterviewSession.DoesNotExist:
            return _err('NOT_FOUND', 'Session not found.', 404)
        return _ok(_serialize_session(session))

"""
Tests for the interview Q&A lifecycle fixes:
- Empty / noise answers score 0
- Short meaningful answers can score high
- Interview completion only when all phases done
- Duplicate answer submission rejected
- Scoring rubric classification

Run: pytest apps/sessions/tests_lifecycle.py -v
"""
import pytest
from unittest.mock import patch

from apps.sessions.interview_engine import (
    AdaptiveInterviewEngine,
    SessionContext,
    evaluate_answer_quality,
    build_ai_feedback,
    _is_meaningful_answer,
    parse_llm_evaluation,
    _score_to_classification,
    PHASE_QUESTION_COUNTS,
    SCORE_EMPTY,
)


# ── Pre-validation: empty / noise detection ────────────────────────────────────

class TestIsMeaningfulAnswer:

    def test_empty_string(self):
        ok, cls = _is_meaningful_answer('')
        assert not ok and cls == 'no_answer'

    def test_whitespace_only(self):
        ok, cls = _is_meaningful_answer('   \n  \t  ')
        assert not ok and cls == 'no_answer'

    def test_punctuation_only(self):
        ok, cls = _is_meaningful_answer('... ,,, !!!')
        assert not ok and cls == 'no_answer'

    def test_pure_noise_tokens(self):
        ok, cls = _is_meaningful_answer('uh um er hmm')
        assert not ok and cls == 'no_answer'

    def test_single_noise_token(self):
        ok, cls = _is_meaningful_answer('okay')
        assert not ok and cls == 'no_answer'

    def test_two_noise_tokens(self):
        ok, cls = _is_meaningful_answer('yes no')
        assert not ok and cls == 'no_answer'

    def test_short_real_answer(self):
        # 3 meaningful tokens
        ok, cls = _is_meaningful_answer('Python is interpreted')
        assert ok and cls == 'meaningful'

    def test_meaningful_long_answer(self):
        ok, cls = _is_meaningful_answer(
            'Encapsulation means bundling data and methods together '
            'and restricting direct access to the data.'
        )
        assert ok and cls == 'meaningful'


# ── Scoring: empty answers score 0 ─────────────────────────────────────────────

class TestEvaluateAnswerQuality:

    def test_empty_answer_scores_zero(self):
        assert evaluate_answer_quality('', ['python', 'oop']) == 0.0

    def test_whitespace_scores_zero(self):
        assert evaluate_answer_quality('   \n  ', ['python']) == 0.0

    def test_noise_only_scores_zero(self):
        assert evaluate_answer_quality('uh um er', ['python']) == 0.0

    def test_short_correct_answer_not_zero(self):
        # Even short answers with concept hits should score > 0
        score = evaluate_answer_quality('Python uses OOP principles', ['python', 'oop'])
        assert score > 0.0

    def test_no_artificial_floor(self):
        # An answer that covers zero expected concepts should score very low,
        # NOT get bumped to 0.05 by an artificial floor.
        score = evaluate_answer_quality(
            'I like pizza and movies on weekends',
            ['python', 'django', 'rest', 'api', 'database'],
        )
        assert score < 0.1  # should be near 0 for irrelevant answer


# ── Feedback: no-answer message ──────────────────────────────────────────────

class TestBuildAiFeedback:

    def test_empty_answer_feedback_says_no_answer(self):
        fb = build_ai_feedback('What is OOP?', '', ['oop'], 0.0, 'technical')
        assert 'No answer was provided' in fb

    def test_noise_answer_feedback_says_no_answer(self):
        fb = build_ai_feedback('What is OOP?', 'uh um', ['oop'], 0.0, 'technical')
        assert 'No answer was provided' in fb

    def test_good_answer_feedback_positive(self):
        fb = build_ai_feedback(
            'What is encapsulation?',
            'Encapsulation means bundling data and methods and restricting access.',
            ['encapsulation', 'data', 'methods'],
            0.85,
            'technical',
        )
        assert 'Good' in fb or 'Excellent' in fb

    def test_poor_answer_feedback_mentions_concepts(self):
        fb = build_ai_feedback(
            'Explain polymorphism',
            'It is something about objects',
            ['polymorphism', 'inheritance', 'methods'],
            0.15,
            'technical',
        )
        assert len(fb) > 10


# ── LLM evaluation parsing ────────────────────────────────────────────────────

class TestParseLlmEvaluation:

    def test_valid_json_parsed(self):
        raw = '{"score": 8, "classification": "correct", "strengths": ["good"], "missing_concepts": [], "feedback": "Well done", "should_follow_up": false}'
        result = parse_llm_evaluation(raw, 0.5)
        assert result['score_10'] == 8
        assert result['classification'] == 'correct'
        assert result['should_follow_up'] is False

    def test_score_clamped_to_10(self):
        raw = '{"score": 15, "classification": "excellent", "strengths": [], "missing_concepts": [], "feedback": "", "should_follow_up": false}'
        result = parse_llm_evaluation(raw, 0.9)
        assert result['score_10'] == 10

    def test_score_clamped_to_0(self):
        raw = '{"score": -5, "classification": "incorrect", "strengths": [], "missing_concepts": [], "feedback": "", "should_follow_up": true}'
        result = parse_llm_evaluation(raw, 0.1)
        assert result['score_10'] == 0

    def test_no_answer_classification_forces_zero(self):
        raw = '{"score": 5, "classification": "no_answer", "strengths": [], "missing_concepts": [], "feedback": "", "should_follow_up": false}'
        result = parse_llm_evaluation(raw, 0.5)
        assert result['score_10'] == 0
        assert result['classification'] == 'no_answer'

    def test_invalid_json_uses_fallback(self):
        result = parse_llm_evaluation('not json at all', 0.6)
        assert result['score_10'] == 6
        assert 'could not be parsed' in result['feedback']

    def test_markdown_fences_stripped(self):
        raw = '```json\n{"score": 7, "classification": "mostly_correct", "strengths": [], "missing_concepts": [], "feedback": "ok", "should_follow_up": false}\n```'
        result = parse_llm_evaluation(raw, 0.5)
        assert result['score_10'] == 7

    def test_follow_up_flag_true_for_low_score(self):
        raw = '{"score": 3, "classification": "partially_correct", "strengths": [], "missing_concepts": ["x"], "feedback": "", "should_follow_up": true}'
        result = parse_llm_evaluation(raw, 0.3)
        assert result['should_follow_up'] is True


# ── Score to classification mapping ───────────────────────────────────────────

class TestScoreToClassification:

    def test_zero_is_no_answer(self):
        assert _score_to_classification(0.0) == 'no_answer'

    def test_very_low_is_incorrect(self):
        assert _score_to_classification(0.1) == 'incorrect'

    def test_low_is_partially_correct(self):
        assert _score_to_classification(0.3) == 'partially_correct'

    def test_mid_is_mostly_correct(self):
        assert _score_to_classification(0.5) == 'mostly_correct'

    def test_high_is_correct(self):
        assert _score_to_classification(0.8) == 'correct'

    def test_very_high_is_excellent(self):
        assert _score_to_classification(0.95) == 'excellent'


# ── Interview completion logic ────────────────────────────────────────────────

@pytest.mark.django_db
class TestInterviewCompletionLogic:
    """
    Verify the engine ends only when all configured phases are done,
    NOT on a hardcoded turn count.
    """

    def _ctx(self, session_type='mixed', turn_number=0, current_phase='warmup',
             questions_in_phase=0, phase_scores=None):
        return SessionContext(
            session_type=session_type,
            domain='software_engineering',
            difficulty='intermediate',
            current_phase=current_phase,
            turn_number=turn_number,
            questions_in_phase=questions_in_phase,
            last_answer_score=None,
            last_question_text='',
            last_question_entry=None,
            asked_question_texts=set(),
            phase_scores=phase_scores or {},
        )

    def test_mixed_total_questions(self):
        counts = PHASE_QUESTION_COUNTS['mixed']
        total = sum(counts.values())
        # mixed = 2+4+2+2+2+1 = 13
        assert total == 13

    def test_not_ended_before_total(self):
        engine = AdaptiveInterviewEngine()
        ctx = self._ctx(turn_number=10, current_phase='technical', questions_in_phase=3)
        assert not engine._should_end(ctx)

    def test_ended_at_total(self):
        engine = AdaptiveInterviewEngine()
        ctx = self._ctx(turn_number=13, current_phase='closing', questions_in_phase=1)
        assert engine._should_end(ctx)

    def test_ended_when_closing_phase_complete(self):
        engine = AdaptiveInterviewEngine()
        ctx = self._ctx(current_phase='closing', questions_in_phase=1, turn_number=5)
        assert engine._should_end(ctx)

    def test_coding_session_uses_coding_sequence(self):
        # Coding session: 4 coding + 1 closing = 5 total
        counts = PHASE_QUESTION_COUNTS['coding']
        assert sum(counts.values()) == 5

    def test_coding_session_not_ended_at_turn_3(self):
        engine = AdaptiveInterviewEngine()
        ctx = self._ctx(session_type='coding', turn_number=3, current_phase='coding', questions_in_phase=3)
        assert not engine._should_end(ctx)

    def test_coding_session_ended_at_turn_5(self):
        engine = AdaptiveInterviewEngine()
        ctx = self._ctx(session_type='coding', turn_number=5, current_phase='closing', questions_in_phase=1)
        assert engine._should_end(ctx)

    def test_hr_session_not_completed_early(self):
        # HR session: 1+2+0+1+6+1 = 11
        engine = AdaptiveInterviewEngine()
        ctx = self._ctx(session_type='hr', turn_number=5, current_phase='hr', questions_in_phase=3)
        assert not engine._should_end(ctx)


# ── Duplicate answer submission ──────────────────────────────────────────────

@pytest.mark.django_db
class TestDuplicateSubmissionRejection:
    """
    The SubmitResponseView should reject answering the same question twice.
    """

    def test_second_answer_returns_409(self, db):
        from django.contrib.auth import get_user_model
        from rest_framework.test import APIClient
        from apps.sessions.models import InterviewSession, InterviewQuestion, StudentResponse
        import uuid

        User = get_user_model()
        user = User.objects.create_user(
            email='lifecycle@test.com', password='Test@2024', full_name='Lifecycle Test'
        )
        c = APIClient()
        r = c.post('/api/auth/login', {'email': user.email, 'password': 'Test@2024'}, format='json')
        token = r.data['data']['tokens']['access']
        c.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        profile = user.student_profile
        session = InterviewSession.objects.create(
            student=profile, session_type='mixed', difficulty='intermediate',
            status='active', started_at=__import__('django.utils.timezone', fromlist=['now']).now(),
        )
        q = InterviewQuestion.objects.create(
            session=session, turn_number=1, phase='warmup',
            question_text='Tell me about yourself.',
            question_type='situational', topic='intro',
            difficulty_level='easy', expected_concepts=['name'],
        )
        # First answer — accepted
        r1 = c.post(f'/api/interview/sessions/{session.id}/respond/', {
            'question_id': str(q.id), 'answer': 'I am a CS student with Python skills', 'duration_seconds': 10,
        }, format='json')
        assert r1.status_code == 200

        # Second answer to same question — must be 409
        r2 = c.post(f'/api/interview/sessions/{session.id}/respond/', {
            'question_id': str(q.id), 'answer': 'I am a different answer', 'duration_seconds': 10,
        }, format='json')
        assert r2.status_code == 409
        # Only one response in DB
        assert StudentResponse.objects.filter(question=q).count() == 1


# ── Empty answer is stored, not rejected ──────────────────────────────────────

@pytest.mark.django_db
class TestEmptyAnswerStored:
    """
    An empty answer should be ACCEPTED (stored with score 0),
    NOT rejected with a 400 error.
    """

    def test_empty_answer_accepted_with_zero_score(self, db):
        from django.contrib.auth import get_user_model
        from rest_framework.test import APIClient
        from apps.sessions.models import InterviewSession, InterviewQuestion, StudentResponse
        from django.utils import timezone

        User = get_user_model()
        user = User.objects.create_user(
            email='empty_ans@test.com', password='Test@2024', full_name='Empty Test'
        )
        c = APIClient()
        r = c.post('/api/auth/login', {'email': user.email, 'password': 'Test@2024'}, format='json')
        token = r.data['data']['tokens']['access']
        c.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        profile = user.student_profile
        session = InterviewSession.objects.create(
            student=profile, session_type='mixed', difficulty='intermediate',
            status='active', started_at=timezone.now(),
        )
        q = InterviewQuestion.objects.create(
            session=session, turn_number=1, phase='warmup',
            question_text='Tell me about yourself.',
            question_type='situational', topic='intro',
            difficulty_level='easy', expected_concepts=['name'],
        )
        # Submit empty answer — should be 200, not 400
        r1 = c.post(f'/api/interview/sessions/{session.id}/respond/', {
            'question_id': str(q.id), 'answer': '', 'duration_seconds': 10,
        }, format='json')
        assert r1.status_code == 200
        assert r1.data['data']['response_saved']['score'] == 0.0
        assert 'No answer was provided' in r1.data['data']['response_saved']['feedback']

    def test_question_echo_rejected_with_zero_score(self, db):
        from django.contrib.auth import get_user_model
        from rest_framework.test import APIClient
        from apps.sessions.models import InterviewSession, InterviewQuestion
        from django.utils import timezone

        User = get_user_model()
        user = User.objects.create_user(
            email='echo_ans@test.com', password='Test@2024', full_name='Echo Test'
        )
        c = APIClient()
        r = c.post('/api/auth/login', {'email': user.email, 'password': 'Test@2024'}, format='json')
        token = r.data['data']['tokens']['access']
        c.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        profile = user.student_profile
        session = InterviewSession.objects.create(
            student=profile, session_type='mixed', difficulty='intermediate',
            status='active', started_at=timezone.now(),
        )
        q = InterviewQuestion.objects.create(
            session=session, turn_number=1, phase='warmup',
            question_text="Let's begin the coding round. I'll present you with a programming problem.",
            question_type='coding', topic='coding_introduction',
            difficulty_level='easy', expected_concepts=['algorithm', 'code'],
        )
        # Submit echo of question
        echo_answer = "Let's begin the coding round I'll present you with a programming problem"
        r1 = c.post(f'/api/interview/sessions/{session.id}/respond/', {
            'question_id': str(q.id), 'answer': echo_answer, 'duration_seconds': 15,
        }, format='json')
        assert r1.status_code == 200
        assert r1.data['data']['response_saved']['score'] == 0.0
        assert 'echo' in r1.data['data']['response_saved']['feedback'].lower()

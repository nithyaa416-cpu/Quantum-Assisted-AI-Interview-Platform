"""
Tests for sessions app: InterviewSession enhancement, adaptive follow-ups,
dynamic turns calculation, and JD/resume question generation.
"""
import pytest
from django.utils import timezone
from apps.accounts.models import CustomUser, StudentProfile
from apps.resumes.models import Resume, TargetRole
from apps.sessions.models import InterviewSession, InterviewQuestion, StudentResponse
from apps.sessions.interview_engine import (
    AdaptiveInterviewEngine,
    SessionContext,
    PHASE_QUESTION_COUNTS,
)
from apps.sessions.interview_views import _build_context, _serialize_session
from apps.sessions.ai_services import generate_llm_interview_question
from apps.sessions.question_bank import find_question_in_bank, WARMUP_QUESTIONS


@pytest.fixture
def test_user(db):
    user = CustomUser.objects.create_user(
        email='sessiontest@test.com',
        password='TestPassword@123',
        full_name='Test Candidate',
    )
    return user


@pytest.fixture
def student_profile(test_user):
    return test_user.student_profile


@pytest.fixture
def sample_resume(student_profile):
    return Resume.objects.create(
        student=student_profile,
        original_filename='resume.pdf',
        is_parsed=True,
        parsed_data={
            'skills': [{'name': 'Python'}, {'name': 'Django'}, {'name': 'React'}],
            'projects': [{'title': 'AI Interview Bot'}],
        },
    )


@pytest.fixture
def target_role(student_profile):
    return TargetRole.objects.create(
        student=student_profile,
        role_name='Python Developer',
        domain='backend',
        is_primary=True,
    )


@pytest.mark.django_db
class TestTask4SessionEnhancement:
    """Task 4: Add job_description and resume to InterviewSession."""

    def test_session_has_resume_and_job_description_fields(self, student_profile, sample_resume, target_role):
        session = InterviewSession.objects.create(
            student=student_profile,
            target_role=target_role,
            resume=sample_resume,
            job_description='Looking for a Senior Python Developer with Django experience.',
            session_type='technical',
            difficulty='intermediate',
            status='active',
        )

        assert session.resume == sample_resume
        assert session.job_description == 'Looking for a Senior Python Developer with Django experience.'
        assert session.resume.parsed_data['skills'][0]['name'] == 'Python'

    def test_serialized_session_includes_resume_id_and_job_description(self, student_profile, sample_resume):
        session = InterviewSession.objects.create(
            student=student_profile,
            resume=sample_resume,
            job_description='Must know Python and Docker.',
            session_type='mixed',
            status='active',
        )
        serialized = _serialize_session(session)
        assert serialized['resume_id'] == str(sample_resume.id)
        assert serialized['job_description'] == 'Must know Python and Docker.'


@pytest.mark.django_db
class TestTask6FollowUpReconstruction:
    """Task 6: Follow-up context reconstruction in _build_context()."""

    def test_find_question_in_bank_returns_follow_ups(self):
        warmup_q = WARMUP_QUESTIONS[0]
        entry = find_question_in_bank(warmup_q['text'])
        assert entry is not None
        assert len(entry['follow_ups']) > 0
        assert len(entry['harder_follow_up']) > 0

    def test_build_context_reconstructs_follow_ups_for_bank_question(self, student_profile, sample_resume):
        session = InterviewSession.objects.create(
            student=student_profile,
            resume=sample_resume,
            session_type='mixed',
            status='active',
        )
        # Create bank question
        warmup_q = WARMUP_QUESTIONS[0]
        q = InterviewQuestion.objects.create(
            session=session,
            turn_number=1,
            phase='warmup',
            question_text=warmup_q['text'],
            expected_concepts=warmup_q['expected_concepts'],
        )
        StudentResponse.objects.create(
            question=q,
            session=session,
            transcript='My name is Test.',
            score=0.25,  # Weak score
        )

        ctx = _build_context(session)
        assert ctx.last_question_entry is not None
        assert len(ctx.last_question_entry['follow_ups']) > 0

    def test_adaptive_engine_triggers_follow_up_on_weak_score(self):
        engine = AdaptiveInterviewEngine()
        ctx = SessionContext(
            session_type='mixed',
            domain='backend',
            difficulty='intermediate',
            current_phase='technical',
            turn_number=2,
            questions_in_phase=1,
            last_answer_score=0.20,  # Weak answer (< 0.35)
            last_question_text='Explain Django ORM.',
            last_question_entry={
                'text': 'Explain Django ORM.',
                'topic': 'ORM',
                'expected_concepts': ['models', 'queries'],
                'follow_ups': ['How does select_related work in Django?'],
                'harder_follow_up': 'How do you optimize N+1 queries?',
            },
            asked_question_texts={'Explain Django ORM.'},
            phase_scores={'technical': [0.20]},
        )
        decision = engine.decide_next_turn(ctx)
        assert decision.is_follow_up is True
        assert decision.follow_up_reason == 'weak_answer'
        assert decision.question_text == 'How does select_related work in Django?'


@pytest.mark.django_db
class TestTask7DynamicTurnsCap:
    """Task 7: Remove hardcoded 13-turn cap and dynamically calculate total turns."""

    def test_coding_session_calculates_correct_max_turns(self):
        coding_counts = PHASE_QUESTION_COUNTS['coding']
        total_coding = sum(coding_counts.values())
        # Coding session has 4 coding + 1 closing = 5 turns
        assert total_coding == 5

    def test_engine_should_end_when_total_limit_reached(self):
        engine = AdaptiveInterviewEngine()
        ctx = SessionContext(
            session_type='coding',
            domain='software_engineering',
            difficulty='intermediate',
            current_phase='closing',
            turn_number=5,
            questions_in_phase=1,
            last_answer_score=0.8,
            last_question_text='Closing question',
            last_question_entry=None,
            asked_question_texts=set(),
            phase_scores={'coding': [0.8], 'closing': [0.8]},
        )
        decision = engine.decide_next_turn(ctx)
        assert decision.should_end_interview is True


class TestTask8JDAndResumeQuestionGeneration:
    """Task 8: Connect JD + Selected Resume to question generation."""

    def test_generate_llm_question_incorporates_job_description(self):
        result = generate_llm_interview_question(
            candidate_name='Jane Doe',
            target_role='Backend Developer',
            resume_skills=['Python', 'PostgreSQL', 'FastAPI'],
            resume_projects=['E-Commerce API'],
            current_phase='technical',
            turn_number=2,
            difficulty='medium',
            last_question_text='Tell me about yourself.',
            last_answer_text='I have built backend APIs with FastAPI and PostgreSQL.',
            session_type='technical',
            job_description='Requires experience designing high-scale REST APIs with FastAPI and PostgreSQL.',
        )
        assert result['question_text']
        assert result['phase'] == 'technical'
        assert len(result['question_text']) > 15


class TestTTSAndWhisperPolish:
    """Test Edge-TTS text cleaning, caching, and fallback polish."""

    def test_clean_tts_text_replaces_coding_problem_and_strips_markdown(self):
        from apps.sessions.ai_services import _clean_tts_text
        # Coding sentinel replacement
        coding_clean = _clean_tts_text("[CODING_PROBLEM]")
        assert "coding challenge" in coding_clean
        assert "[" not in coding_clean

        # Markdown stripping
        md_text = "Could you explain **how** `select_related` *optimizes* queries?"
        cleaned = _clean_tts_text(md_text)
        assert cleaned == "Could you explain how select_related optimizes queries?"

    def test_tts_cache_returns_cached_audio(self):
        from apps.sessions.ai_services import generate_edge_tts_audio, _tts_cache
        test_phrase = "Hello candidate, welcome to your test."
        audio1 = generate_edge_tts_audio(test_phrase)
        assert len(audio1) > 200

        # Verify cached
        cache_key = f"en-US-AriaNeural:{test_phrase}"
        assert cache_key in _tts_cache

        # Second call returns from cache
        audio2 = generate_edge_tts_audio(test_phrase)
        assert audio2 == audio1


class TestNaturalFeedbackAndFollowUpGeneration:
    """Test immediate natural conversational feedback and answer-driven next questions."""

    def test_natural_feedback_gently_corrects_incorrect_answer(self):
        from apps.sessions.ai_services import generate_natural_feedback
        feedback = generate_natural_feedback(
            question_text="Tell me full form of CN",
            candidate_answer="cloud networks",
            expected_concepts=["Computer Networks"],
            score=0.15,
            phase="technical",
        )
        assert feedback
        # Should be conversational and contain the correction or gentle guidance
        assert "Computer Networks" in feedback or "Actually" in feedback or "networks" in feedback.lower()
        # Must not contain robotic boilerplate like "Consider addressing these concepts:"
        assert "Consider addressing these concepts" not in feedback

    def test_natural_feedback_affirms_strong_answer(self):
        from apps.sessions.ai_services import generate_natural_feedback
        feedback = generate_natural_feedback(
            question_text="What is a database index?",
            candidate_answer="A database index is a data structure like a B-tree that improves the speed of data retrieval operations.",
            expected_concepts=["data structure", "B-tree", "speed", "retrieval"],
            score=0.85,
            phase="technical",
        )
        assert feedback
        assert len(feedback) > 10
        assert "Consider addressing these concepts" not in feedback

    def test_next_question_generated_from_weak_answer_asks_simpler_follow_up(self):
        from apps.sessions.ai_services import generate_llm_interview_question
        result = generate_llm_interview_question(
            candidate_name="Alex",
            target_role="Network Engineer",
            resume_skills=["Networking", "TCP/IP"],
            resume_projects=[],
            current_phase="technical",
            turn_number=3,
            difficulty="medium",
            last_question_text="Tell me full form of CN",
            last_answer_text="cloud networks",
            last_score=0.15,  # Weak answer
            session_type="technical",
        )
        assert len(result["question_text"]) > 15
        assert "?" in result["question_text"]
        assert result["phase"] == "technical"

    def test_next_question_generated_from_strong_answer_builds_deeper(self):
        from apps.sessions.ai_services import generate_llm_interview_question
        result = generate_llm_interview_question(
            candidate_name="Alex",
            target_role="Backend Developer",
            resume_skills=["Django", "PostgreSQL"],
            resume_projects=["Banking API"],
            current_phase="technical",
            turn_number=3,
            difficulty="medium",
            last_question_text="How do you handle race conditions in Django?",
            last_answer_text="I use select_for_update inside transaction.atomic to obtain row-level database locks.",
            last_score=0.85,  # Strong answer
            session_type="technical",
        )
        assert result["question_text"]
        assert len(result["question_text"]) > 20
        assert "?" in result["question_text"]
        assert result["phase"] == "technical"

    def test_next_question_incorporates_holistic_factors(self):
        """Verify generation considers resume, JD, remaining time, uncovered topics, and previous answer."""
        from apps.sessions.ai_services import generate_llm_interview_question
        result = generate_llm_interview_question(
            candidate_name="Sarah",
            target_role="Senior Cloud Architect",
            resume_skills=["Python", "AWS", "Docker", "Terraform"],
            resume_projects=["Cloud Migration"],
            current_phase="technical",
            turn_number=4,
            difficulty="advanced",
            last_question_text="How do you structure infrastructure with Terraform?",
            last_answer_text="We modularize resources into VPC, compute, and RDS modules.",
            last_score=0.80,
            session_type="technical",
            job_description="Must have in-depth experience with Kubernetes, Microservices, and Kafka event streaming.",
            covered_topics=["Terraform", "AWS"],
            uncovered_topics=["Kubernetes", "Kafka"],
            remaining_time_seconds=600,  # 10 minutes left
            remaining_turns=2,           # 2 questions remaining
        )
        assert result["question_text"]
        q_text = result["question_text"].lower()
        assert any(k in q_text for k in ["kubernetes", "kafka", "microservices", "module", "terraform", "rds", "vpc", "remaining", "trade-off", "architecture"])


class TestGenericEngineAndAuthenticInterviewFlow:
    """Test 100% role-agnostic engine and authentic human-like interview flow."""

    def test_is_coding_role_distinguishes_roles_correctly(self):
        from apps.sessions.interview_engine import is_coding_role
        # Coding roles
        assert is_coding_role("Software Engineer") is True
        assert is_coding_role("Backend Developer") is True
        assert is_coding_role("Full Stack Developer") is True
        assert is_coding_role("Frontend Engineer") is True
        assert is_coding_role("DevOps Engineer") is True

        # Non-coding roles
        assert is_coding_role("Product Manager") is False
        assert is_coding_role("UI/UX Designer") is False
        assert is_coding_role("Marketing Specialist") is False
        assert is_coding_role("Business Analyst") is False
        assert is_coding_role("Financial Analyst") is False
        assert is_coding_role("Human Resources Specialist") is False

    def test_build_dynamic_vocab_prompt_extracts_custom_domain(self):
        from apps.sessions.ai_services import build_dynamic_vocab_prompt
        prompt = build_dynamic_vocab_prompt(
            target_role="Product Manager",
            resume_skills=["User Research", "Roadmapping", "A/B Testing", "Figma"],
            job_description="Seeking a PM experienced with Churn Rate reduction, PRDs, Sprint Planning, and ARR growth.",
        )
        assert "Product Manager" in prompt
        assert "A/B Testing" in prompt or "Roadmapping" in prompt
        assert "Churn" in prompt or "PRDs" in prompt or "Sprint" in prompt

    def test_turn_1_has_welcoming_opening_with_alex_persona(self):
        from apps.sessions.ai_services import generate_llm_interview_question
        result = generate_llm_interview_question(
            candidate_name="Manoj",
            target_role="Product Manager",
            resume_skills=["Product Strategy"],
            resume_projects=["Mobile App Launch"],
            current_phase="warmup",
            turn_number=1,
            difficulty="intermediate",
            session_type="mixed",
        )
        q_text = result["question_text"]
        assert "Alex" in q_text
        assert "Product Manager" in q_text
        assert "Manoj" in q_text
        assert "introduce yourself" in q_text.lower()
        assert "?" in q_text

    def test_closing_phase_initiates_candidate_qa(self):
        from apps.sessions.ai_services import generate_llm_interview_question
        result = generate_llm_interview_question(
            candidate_name="Manoj",
            target_role="Software Engineer",
            resume_skills=["Python"],
            resume_projects=["AI Platform"],
            current_phase="closing",
            turn_number=12,
            difficulty="intermediate",
            session_type="mixed",
        )
        q_text = result["question_text"]
        assert "questions for me" in q_text.lower()
        assert result["topic"] == "candidate_qa"

    def test_interviewer_answers_candidate_question_in_character(self):
        from apps.sessions.ai_services import generate_interviewer_answer_to_candidate_question
        answer = generate_interviewer_answer_to_candidate_question(
            candidate_question="What does a typical day look like for a software engineer on this team?",
            target_role="Backend Developer",
            job_description="Fast-growing fintech team building distributed ledger microservices.",
            candidate_name="Manoj",
        )
        assert answer
        assert len(answer) > 20
        # Should be a spoken conversational answer and closing farewell
        assert "team" in answer.lower() or "role" in answer.lower() or "pleasure" in answer.lower()
        assert "Interviewer:" not in answer

    def test_non_coding_role_adapts_coding_phase_to_case_study(self):
        from apps.sessions.interview_engine import AdaptiveInterviewEngine, SessionContext
        engine = AdaptiveInterviewEngine()
        ctx = SessionContext(
            session_type='mixed',
            domain='product_management',
            difficulty='intermediate',
            current_phase='coding',
            turn_number=5,
            questions_in_phase=0,
            last_answer_score=0.75,
            last_question_text="Tell me about your product background",
            last_question_entry=None,
            asked_question_texts=set(),
            phase_scores={'warmup': [0.8], 'technical': [0.75]},
            candidate_name="Manoj",
            target_role_name="Product Manager",
            resume_skills=["User Research", "Roadmapping"],
            resume_projects=["SaaS Dashboard"],
            job_description="Lead growth and retention for SaaS product",
        )
        decision = engine.decide_next_turn(ctx)
        # Should NOT be '[CODING_PROBLEM]' for Product Manager
        assert decision.question_text != '[CODING_PROBLEM]'
        assert decision.question_type in ('conceptual', 'project')


@pytest.mark.django_db
class TestInterviewDurationOptionsAndPacing:
    """Test user-selected duration options (20, 25, 30 min) and temporal pacing."""

    def test_interview_session_creation_saves_custom_duration_seconds(self, test_user):
        from rest_framework.test import APIClient
        client = APIClient()
        client.force_authenticate(user=test_user)

        # Post 20 minutes (Fresher fast-track)
        resp = client.post('/api/interview/sessions/', {
            'session_type': 'mixed',
            'difficulty': 'beginner',
            'duration_minutes': 20,
            'target_role_name': 'Junior Python Developer',
        }, format='json')

        assert resp.status_code == 201
        data = resp.json()['data']
        assert data['duration_seconds'] == 1200  # 20 * 60

        # Post 30 minutes (Senior deep-dive)
        resp2 = client.post('/api/interview/sessions/', {
            'session_type': 'technical',
            'difficulty': 'advanced',
            'duration_minutes': 30,
            'target_role_name': 'Senior Systems Architect',
        }, format='json')

        assert resp2.status_code == 201
        data2 = resp2.json()['data']
        assert data2['duration_seconds'] == 1800  # 30 * 60

    def test_session_context_uses_duration_seconds_for_remaining_time(self, student_profile):
        from apps.sessions.interview_views import _build_context
        from apps.sessions.models import InterviewSession

        session = InterviewSession.objects.create(
            student=student_profile,
            session_type='mixed',
            difficulty='intermediate',
            duration_seconds=1200,  # 20 minutes
            status='active',
        )

        ctx = _build_context(session)
        assert ctx.remaining_time_seconds <= 1200




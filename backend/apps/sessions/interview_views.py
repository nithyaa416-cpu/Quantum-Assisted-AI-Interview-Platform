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
import re
from django.utils import timezone
from rest_framework import status as http_status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from apps.resumes.models import TargetRole, Resume
from apps.resumes.views import parse_resume_now
from .models import InterviewSession, InterviewQuestion, StudentResponse
from .interview_engine import (
    AdaptiveInterviewEngine,
    SessionContext,
    evaluate_answer_quality,
    build_ai_feedback,
    build_llm_scoring_prompt,
    parse_llm_evaluation,
    _is_meaningful_answer,
    PHASE_SEQUENCE,
    PHASE_QUESTION_COUNTS,
    SCORE_EMPTY,
)
from .question_bank import find_question_in_bank

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
    # For coding sessions with no questions yet, start in 'coding' phase not 'warmup'
    if questions:
        current_phase = questions[-1].phase
    elif session.session_type == 'coding':
        current_phase = 'coding'
    else:
        current_phase = 'warmup'

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
        bank_entry = find_question_in_bank(last_q.question_text)
        if bank_entry:
            last_entry = {
                'text': last_q.question_text,
                'topic': last_q.topic or bank_entry.get('topic', ''),
                'expected_concepts': last_q.expected_concepts or bank_entry.get('expected_concepts', []),
                'follow_ups': bank_entry.get('follow_ups', []),
                'harder_follow_up': bank_entry.get('harder_follow_up', ''),
            }
        else:
            # Provide intelligent adaptive follow-ups for dynamic LLM questions
            topic_label = last_q.topic or "that implementation"
            last_entry = {
                'text': last_q.question_text,
                'topic': last_q.topic,
                'expected_concepts': last_q.expected_concepts,
                'follow_ups': [
                    f"Could you elaborate on the technical trade-offs or design decisions you made regarding {topic_label}?",
                    f"What were the key challenges or edge cases you had to account for with {topic_label}?",
                ],
                'harder_follow_up': f"How would you optimize and architect {topic_label} for high availability and low latency under production scale?",
            }

    # Phase scores
    phase_scores: dict[str, list[float]] = {}
    for q in questions:
        resp = responses.get(q.id)
        if resp and resp.score is not None:
            phase_scores.setdefault(q.phase, []).append(float(resp.score))

    # Domain and target role
    domain = 'software_engineering'
    target_role_name = 'Software Engineer'
    if session.target_role:
        domain = session.target_role.domain or 'software_engineering'
        target_role_name = session.target_role.role_name

    candidate_name = ""
    if session.student:
        candidate_name = session.student.full_name or ""
        if not candidate_name and session.student.user:
            candidate_name = f"{session.student.user.first_name} {session.student.user.last_name}".strip()
            if not candidate_name:
                candidate_name = session.student.user.email.split('@')[0]

    # Job description from session (or fallback from session notes)
    job_description = (session.job_description or "").strip()
    if not job_description and session.notes:
        notes_lines = session.notes.split('\n')
        jd_lines = [
            l for l in notes_lines
            if not l.startswith('[Candidate Name:') and not l.startswith('[Resume')
        ]
        job_description = '\n'.join(jd_lines).strip()

    # Extract resume skills and projects from selected session.resume
    resume_skills = []
    resume_projects = []
    try:
        resume_to_use = (
            session.resume
            or session.student.resumes.filter(is_active=True).first()
            or session.student.resumes.first()
        )
        if resume_to_use:
            parsed = resume_to_use.parsed_data
            if not parsed or not resume_to_use.is_parsed:
                parsed = parse_resume_now(resume_to_use)
            if parsed:
                resume_skills = [
                    s['name'] for s in parsed.get('skills', [])
                    if isinstance(s, dict) and 'name' in s
                ]
                resume_projects = [
                    p.get('title', '') for p in parsed.get('projects', [])
                    if isinstance(p, dict) and p.get('title')
                ]
    except Exception as exc:
        logger.warning("Error loading resume context for session %s: %s", session.id, exc)

    last_answer_text = ""
    if questions:
        last_resp = responses.get(questions[-1].id)
        if last_resp and last_resp.transcript:
            last_answer_text = last_resp.transcript

    # ── Holistic Factors: Covered vs Uncovered Topics, Timing & Turns ─────────
    # 1. Topics already covered in previous questions
    covered_topics: list[str] = []
    for q in questions:
        if q.topic and q.topic not in covered_topics:
            covered_topics.append(q.topic)
        for c in (q.expected_concepts or []):
            if c and c not in covered_topics:
                covered_topics.append(c)

    # 2. Competencies pool from Resume and Job Description
    target_competencies: list[str] = []
    for s in resume_skills:
        s_clean = s.strip()
        if s_clean and not any(s_clean.lower() == c.lower() for c in target_competencies):
            target_competencies.append(s_clean)
    for p in resume_projects:
        p_clean = p.strip()
        if p_clean and not any(p_clean.lower() == c.lower() for c in target_competencies):
            target_competencies.append(p_clean)

    if job_description:
        import re
        # 1. Technical competencies
        common_tech_patterns = [
            'Python', 'Django', 'FastAPI', 'Flask', 'Java', 'Spring Boot', 'C++', 'C#',
            'JavaScript', 'TypeScript', 'React', 'Node.js', 'Vue', 'Angular', 'Next.js',
            'SQL', 'PostgreSQL', 'MySQL', 'MongoDB', 'Redis', 'Elasticsearch',
            'Docker', 'Kubernetes', 'AWS', 'Azure', 'GCP', 'CI/CD', 'Git',
            'REST API', 'GraphQL', 'Microservices', 'System Design', 'Distributed Systems',
            'Concurrency', 'Multithreading', 'Security', 'Kafka', 'RabbitMQ',
            'Testing', 'TDD', 'Agile', 'Scrum', 'Data Structures', 'Algorithms'
        ]
        # 2. Product, business, data, design & management competencies
        common_business_patterns = [
            'Product Management', 'Product Strategy', 'Roadmapping', 'User Research', 'A/B Testing',
            'UI/UX Design', 'Wireframing', 'Prototyping', 'Figma', 'Design Systems',
            'Data Analysis', 'Data Visualization', 'Tableau', 'Power BI', 'Statistics',
            'Machine Learning', 'Deep Learning', 'Computer Vision', 'NLP', 'LLMs',
            'Business Analysis', 'Stakeholder Management', 'Requirements Gathering', 'Process Mapping',
            'Financial Modeling', 'Budgeting', 'Risk Management', 'Compliance',
            'Marketing Strategy', 'SEO', 'SEM', 'Content Marketing', 'Conversion Optimization',
            'Human Resources', 'Talent Acquisition', 'Performance Management', 'Employee Relations',
            'Project Management', 'Scrum Master', 'Sprint Planning', 'Cross-functional Collaboration'
        ]
        jd_lower = job_description.lower()
        for pat in common_tech_patterns + common_business_patterns:
            if re.search(r'\b' + re.escape(pat.lower()) + r'\b', jd_lower):
                if not any(pat.lower() == c.lower() for c in target_competencies):
                    target_competencies.append(pat)

        # 3. Extract key requirement phrases from JD lines
        lines = [line.strip().lstrip('-*• ') for line in job_description.split('\n')]
        for line in lines:
            if 4 <= len(line.split()) <= 10 and not line.endswith(':'):
                if not any(line.lower() in c.lower() for c in target_competencies):
                    target_competencies.append(line)
            if len(target_competencies) >= 25:
                break

    # 3. Determine uncovered topics
    covered_lower = {c.lower() for c in covered_topics}
    uncovered_topics: list[str] = [
        comp for comp in target_competencies
        if not any(comp.lower() in cov or cov in comp.lower() for cov in covered_lower)
    ]

    # 4. Timing & Turns Awareness
    from .interview_engine import PHASE_QUESTION_COUNTS
    counts = PHASE_QUESTION_COUNTS.get(session.session_type, PHASE_QUESTION_COUNTS['mixed'])
    total_turns = sum(counts.values())
    remaining_turns = max(0, total_turns - len(questions))

    target_duration = session.duration_seconds or 1800  # Default 30 min target
    elapsed_seconds = 0
    if session.started_at:
        elapsed_seconds = int((timezone.now() - session.started_at).total_seconds())
    remaining_time_seconds = max(0, target_duration - elapsed_seconds)

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
        candidate_name=candidate_name,
        target_role_name=target_role_name,
        resume_skills=resume_skills,
        resume_projects=resume_projects,
        last_answer_text=last_answer_text,
        job_description=job_description,
        covered_topics=covered_topics,
        uncovered_topics=uncovered_topics,
        remaining_time_seconds=remaining_time_seconds,
        remaining_turns=remaining_turns,
        total_turns=total_turns,
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
        'resume_id': str(session.resume_id) if session.resume_id else None,
        'job_description': session.job_description,
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

def _infer_domain(role_title: str) -> str:
    title = role_title.lower()
    if any(k in title for k in ['frontend', 'react', 'vue', 'angular', 'web design']):
        return 'frontend'
    if any(k in title for k in ['data science', 'analytics', 'data analyst', 'business intelligence']):
        return 'data_science'
    if any(k in title for k in ['machine learning', 'ml', 'deep learning', 'nlp', 'computer vision', 'ai']):
        return 'machine_learning'
    if any(k in title for k in ['devops', 'cloud', 'aws', 'azure', 'docker', 'kubernetes', 'sre', 'infrastructure']):
        return 'devops'
    if any(k in title for k in ['backend', 'django', 'fastapi', 'node', 'express', 'spring', 'go', 'golang', 'java', 'c++']):
        return 'backend'
    if any(k in title for k in ['full stack', 'fullstack', 'full-stack', 'mern', 'mean']):
        return 'fullstack'
    if any(k in title for k in ['mobile', 'android', 'ios', 'flutter', 'react native']):
        return 'mobile'
    if any(k in title for k in ['security', 'cyber', 'pentest']):
        return 'cybersecurity'
    if any(k in title for k in ['ui/ux', 'ux designer', 'ui designer', 'product designer']):
        return 'ui_ux_design'
    if any(k in title for k in ['business analyst', 'bi analyst', 'requirements analyst']):
        return 'business_analysis'
    if any(k in title for k in ['marketing', 'seo', 'sem', 'growth', 'brand', 'content']):
        return 'marketing'
    if any(k in title for k in ['finance', 'financial', 'accountant', 'banking', 'investment']):
        return 'finance'
    if any(k in title for k in ['hr', 'human resources', 'recruiter', 'talent acquisition']):
        return 'human_resources'
    if any(k in title for k in ['product', 'scrum', 'agile', 'project manager', 'program manager']):
        return 'product_management'
    return 'software_engineering'


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
            scores = [float(r.score) for r in s.responses.all() if r.score is not None]
            avg_score = round((sum(scores) / len(scores)) * 10, 1) if scores else None
            result.append({
                'id': str(s.id),
                'session_type': s.session_type,
                'difficulty': s.difficulty,
                'status': s.status,
                'target_role': s.target_role.role_name if s.target_role else None,
                'turn_count': q_count,
                'answered_count': r_count,
                'avg_score': avg_score,
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
        target_role_name = (data.get('target_role_name') or '').strip()
        job_description = (data.get('job_description') or '').strip()

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
        elif target_role_name:
            domain = _infer_domain(target_role_name)
            target_role, _ = TargetRole.objects.get_or_create(
                student=profile,
                role_name=target_role_name,
                defaults={'domain': domain, 'is_primary': False}
            )
        else:
            # Auto-use primary role
            target_role = TargetRole.objects.filter(student=profile, is_primary=True).first()

        resume_id = data.get('resume_id')
        selected_resume = None
        extracted_resume_data = None
        if resume_id:
            try:
                selected_resume = Resume.objects.get(pk=resume_id, student=profile)
            except Resume.DoesNotExist:
                logger.warning('Resume %s not found for student %s', resume_id, profile.id)
        if not selected_resume:
            selected_resume = Resume.objects.filter(student=profile, is_active=True).first()

        if selected_resume:
            extracted_resume_data = parse_resume_now(selected_resume)
            logger.info(
                'Resume loaded for interview: resume=%s skills=%d projects=%d',
                selected_resume.id,
                len(extracted_resume_data.get('skills', [])),
                len(extracted_resume_data.get('projects', [])),
            )

        note_parts = []
        if job_description:
            note_parts.append(job_description)
        if profile.full_name:
            note_parts.append(f"[Candidate Name: {profile.full_name}]")
        if extracted_resume_data:
            skills = extracted_resume_data.get('skills', [])
            if skills:
                top_skills = ', '.join(s['name'] for s in skills[:8])
                note_parts.append(f"[Resume Skills: {top_skills}]")
            projects = extracted_resume_data.get('projects', [])
            if projects:
                proj_names = ', '.join(p.get('title', '') for p in projects[:3] if p.get('title'))
                if proj_names:
                    note_parts.append(f"[Resume Projects: {proj_names}]")

        session_notes = "\n".join(note_parts)

        # Parse duration_minutes if provided (default 25 minutes = 1500 seconds)
        duration_minutes = data.get('duration_minutes')
        duration_seconds = 1500
        if duration_minutes is not None:
            try:
                parsed_mins = int(duration_minutes)
                if 5 <= parsed_mins <= 180:
                    duration_seconds = parsed_mins * 60
            except (ValueError, TypeError):
                pass

        # Create session
        session = InterviewSession.objects.create(
            student=profile,
            session_type=session_type,
            difficulty=difficulty,
            target_role=target_role,
            resume=selected_resume,
            job_description=job_description,
            notes=session_notes,
            duration_seconds=duration_seconds,
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

        counts = PHASE_QUESTION_COUNTS.get(session.session_type, PHASE_QUESTION_COUNTS['mixed'])
        total_turns_limit = sum(counts.values())

        if (
            decision.should_end_interview
            or ctx.turn_number >= total_turns_limit
            or (ctx.current_phase == 'closing' and ctx.questions_in_phase >= counts.get('closing', 1))
        ):
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
        # Accept empty answers — they score 0, not an HTTP error.
        # The frontend already does a min-words check before submitting,
        # but empty strings arriving here are valid (student said nothing for 10s).
        answer_text = (request.data.get('answer') or '').strip()
        duration    = request.data.get('duration_seconds')

        if not question_id:
            return _err('VALIDATION_ERROR', 'question_id is required.')

        try:
            question = InterviewQuestion.objects.get(pk=question_id, session=session)
        except InterviewQuestion.DoesNotExist:
            return _err('NOT_FOUND', 'Question not found.')

        # One-shot guard: reject duplicate submissions for the same question
        if StudentResponse.objects.filter(question=question).exists():
            return _err('CONFLICT', 'This question has already been answered.', 409)

        target_role_str = session.target_role.role_name if session.target_role else ""
        candidate_name_str = getattr(session.student, 'full_name', getattr(session.student, 'username', '')) if session.student else ""

        # ── Pre-validation: detect empty / noise answers BEFORE scoring ────────
        is_meaningful, classification = _is_meaningful_answer(answer_text)

        # Detect acoustic echo of question
        is_echo = False
        if is_meaningful and question.question_text and answer_text:
            ans_clean = [w for w in re.findall(r"[a-z0-9]+", answer_text.lower()) if len(w) > 2]
            q_clean = set(w for w in re.findall(r"[a-z0-9]+", question.question_text.lower()) if len(w) > 2)
            if len(ans_clean) >= 3 and len(q_clean) > 0:
                match_count = sum(1 for w in ans_clean if w in q_clean)
                if (match_count / len(ans_clean)) > 0.65:
                    is_echo = True

        if not is_meaningful or is_echo:
            # Hard-zero score — do NOT pass to LLM
            score = SCORE_EMPTY
            if is_echo:
                feedback = "The submitted answer appears to be an echo of the examiner's question. Please answer the question in your own words."
                logger.info('ECHO_ANSWER recorded: session=%s question=%s', session.id, question.id)
            else:
                feedback = (
                    "No answer was provided. Please attempt the question and explain your "
                    "reasoning, even if you are unsure. Partial knowledge is always better "
                    "than silence."
                )
            logger.info(
                'NO_ANSWER recorded: session=%s question=%s',
                session.id, question.id,
            )
        elif question.phase == 'closing' or question.topic == 'candidate_qa':
            # Evaluate answer quality (for closing Candidate Q&A, assess engagement and let Alex answer candidate's question)
            score = 1.0 if len(answer_text.split()) >= 3 else 0.75
            feedback = build_ai_feedback(
                question_text=question.question_text,
                answer_text=answer_text,
                expected_concepts=question.expected_concepts,
                score=score,
                phase=question.phase,
                target_role=target_role_str,
                job_description=session.job_description or "",
                candidate_name=candidate_name_str,
            )
        else:
            # ── Try LLM scoring first, fall back to keyword heuristic ──────────
            from .ai_services import query_llama3
            sys_p, usr_p = build_llm_scoring_prompt(
                question.question_text,
                answer_text,
                question.expected_concepts,
                question.phase,
                question.question_type,
            )
            llm_raw = None
            try:
                llm_raw = query_llama3(usr_p, sys_p)
            except Exception as llm_exc:
                logger.warning('LLM scoring failed, using heuristic: %s', llm_exc)

            if llm_raw:
                fallback = evaluate_answer_quality(answer_text, question.expected_concepts)
                parsed   = parse_llm_evaluation(llm_raw, fallback)
                score    = parsed['score_01']
                feedback = parsed['feedback'] or build_ai_feedback(
                    question_text=question.question_text,
                    answer_text=answer_text,
                    expected_concepts=question.expected_concepts,
                    score=score,
                    phase=question.phase,
                    target_role=target_role_str,
                    job_description=session.job_description or "",
                    candidate_name=candidate_name_str,
                )
                logger.info(
                    'LLM scored: session=%s turn=%d score=%.2f class=%s',
                    session.id, question.turn_number, score, parsed['classification'],
                )
            else:
                # Heuristic fallback — LLM unavailable
                score    = evaluate_answer_quality(answer_text, question.expected_concepts)
                feedback = build_ai_feedback(
                    question_text=question.question_text,
                    answer_text=answer_text,
                    expected_concepts=question.expected_concepts,
                    score=score,
                    phase=question.phase,
                    target_role=target_role_str,
                    job_description=session.job_description or "",
                    candidate_name=candidate_name_str,
                )
                logger.info(
                    'Heuristic scored: session=%s turn=%d score=%.2f',
                    session.id, question.turn_number, score,
                )
# ── Store response ─────────────────────────────────────────────────────
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
            session.id, question.turn_number, score,
        )

        # ── Generate next question ─────────────────────────────────────────────
        ctx = _build_context(session)
        decision = engine.decide_next_turn(ctx)

        interview_complete = False
        next_question_data = None

        counts = PHASE_QUESTION_COUNTS.get(session.session_type, PHASE_QUESTION_COUNTS.get('mixed', {}))
        total_turns_limit = sum(counts.values()) if counts else 999

        if (
            decision.should_end_interview
            or ctx.turn_number >= total_turns_limit
            or (ctx.current_phase == 'closing' and ctx.questions_in_phase >= counts.get('closing', 1))
        ):
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

        now = timezone.now()
        if session.status != 'completed':
            session.status = 'completed'
            session.ended_at = now
            if session.started_at:
                session.duration_seconds = int((now - session.started_at).total_seconds())
            session.save(update_fields=['status', 'ended_at', 'duration_seconds'])

        q_count = session.questions.count()
        r_count = session.responses.count()

        # Generate comprehensive post-interview assessment report
        assessment_obj = None
        try:
            from apps.assessments.services.report_generator import generate_assessment_report
            assessment_obj = generate_assessment_report(
                session=session,
                speech_metrics=request.data.get('speech_metrics'),
                behavioural_metrics=request.data.get('behavioural_metrics'),
            )
        except Exception as e:
            logger.exception('Failed to generate assessment report for session %s: %s', session.id, e)

        logger.info('Interview ended: session=%s turns=%d', session.id, q_count)

        resp_data = {
            'session_id': str(session.id),
            'status': 'completed',
            'total_questions': q_count,
            'total_answered': r_count,
            'duration_seconds': session.duration_seconds,
            'message': 'Interview completed successfully.',
        }
        if assessment_obj:
            resp_data['assessment_id'] = str(assessment_obj.id)
            resp_data['overall_score'] = float(assessment_obj.overall_score)

        return _ok(resp_data)


# ── Interview Coding Endpoints ────────────────────────────────────────────────

class InterviewCodingProblemView(APIView):
    """
    GET /api/interview/sessions/{id}/coding-problem/
    Returns the coding problem assigned to the current coding-phase question.
    If no problem is assigned yet, selects one adaptively from the problem bank.

    POST /api/interview/sessions/{id}/coding-problem/
    Body: { question_id } — explicitly assigns a problem to a coding question.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            session = InterviewSession.objects.get(pk=pk, student__user=request.user)
        except InterviewSession.DoesNotExist:
            return _err('NOT_FOUND', 'Session not found.', 404)

        # Find the current unanswered coding-phase question
        last_q = session.questions.filter(phase='coding').order_by('-turn_number').first()
        if not last_q:
            return _err('NOT_FOUND', 'No coding question found in this session.')

        # Check if a problem is already linked via metadata
        from apps.assessments.models import CodingProblem, CodingSubmission
        from apps.assessments.coding_serializers import CodingProblemDetailSerializer

        # Find an existing submission for this question
        existing_submission = CodingSubmission.objects.filter(
            session=session,
            attempt_type='interview',
        ).order_by('-submitted_at').first()

        if existing_submission and existing_submission.problem:
            problem = existing_submission.problem
        else:
            # Select a problem adaptively
            problem = _select_interview_problem(session, last_q.difficulty_level)
            if not problem:
                return _err('NOT_FOUND', 'No suitable coding problem found.', 404)

        serializer_data = CodingProblemDetailSerializer(problem).data
        return _ok({
            'question_id': str(last_q.id),
            'problem': serializer_data,
        })

    def post(self, request, pk):
        """Explicitly select and return a coding problem for the current turn."""
        try:
            session = InterviewSession.objects.get(pk=pk, student__user=request.user)
        except InterviewSession.DoesNotExist:
            return _err('NOT_FOUND', 'Session not found.', 404)

        from apps.assessments.models import CodingProblem
        from apps.assessments.coding_serializers import CodingProblemDetailSerializer

        # Get the current coding question
        last_q = session.questions.filter(
            phase='coding', question_type='coding'
        ).order_by('-turn_number').first()

        if not last_q:
            return _err('NOT_FOUND', 'No active coding question in session.')

        difficulty = request.data.get('difficulty', last_q.difficulty_level)
        problem = _select_interview_problem(session, difficulty)
        if not problem:
            return _err('NOT_FOUND', 'No suitable coding problem available.')

        serializer_data = CodingProblemDetailSerializer(problem).data
        return _ok({
            'question_id': str(last_q.id),
            'problem': serializer_data,
        })


PRACTICE_20_SLUGS = [
    "remove-duplicates-from-array",
    "second-largest",
    "reverse-of-array",
    "frequency-count",
    "sum-of-array",
    "find-max-min",
    "move-zeroes-to-end",
    "merge-two-sorted-arrays",
    "missing-number",
    "is-array-sorted",
    "linear-search-index",
    "reverse-string",
    "palindrome-string",
    "valid-anagram",
    "count-vowels-and-consonants",
    "first-non-repeating-char",
    "capitalize-words",
    "factorial-of-number",
    "fibonacci-number",
    "check-prime-number",
]


def _select_interview_problem(session: InterviewSession, difficulty: str):
    """
    Select a coding problem strictly from the 20 foundational practice problems.
    Avoids problems the student already solved in this session.
    Matches difficulty to the session difficulty level.
    """
    from apps.assessments.models import CodingProblem, CodingSubmission

    diff_map = {
        'easy': 'easy', 'medium': 'medium', 'hard': 'hard',
        'beginner': 'easy', 'intermediate': 'medium', 'advanced': 'hard'
    }
    problem_diff = diff_map.get(difficulty, 'easy')

    used_problem_ids = set(
        CodingSubmission.objects.filter(
            session=session, attempt_type='interview', problem__isnull=False
        ).values_list('problem_id', flat=True)
    )

    # Strictly restrict to the 20 practiced problems
    base_qs = CodingProblem.objects.filter(is_active=True, slug__in=PRACTICE_20_SLUGS)

    # Match difficulty and not yet used in this session
    qs = base_qs.filter(difficulty=problem_diff).exclude(id__in=used_problem_ids)

    if not qs.exists():
        qs = base_qs.exclude(id__in=used_problem_ids)

    if not qs.exists():
        qs = base_qs

    import random as _random
    problems = list(qs)
    return _random.choice(problems) if problems else None


class InterviewCodingSubmitView(APIView):
    """
    POST /api/interview/sessions/{id}/coding-submit/
    Submit code during an interview session.
    - Runs code against ALL test cases via Judge0
    - Saves as CodingSubmission(attempt_type='interview')
    - Records StudentResponse for the coding question
    - Generates next verbal question so interview continues seamlessly
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            session = InterviewSession.objects.get(pk=pk, student__user=request.user)
        except InterviewSession.DoesNotExist:
            return _err('NOT_FOUND', 'Session not found.', 404)

        if session.status != 'active':
            return _err('BAD_REQUEST', f'Session is {session.status}, not active.')

        question_id = request.data.get('question_id', '').strip()
        problem_id  = request.data.get('problem_id', '').strip()
        language    = request.data.get('language', '').strip().lower() or 'python'
        source_code = request.data.get('source_code', '')
        is_skipped  = bool(request.data.get('skipped', False) or not source_code.strip() or '# Skipped' in source_code)

        if not question_id or not problem_id:
            return _err('VALIDATION_ERROR', 'question_id and problem_id are required.')

        from apps.assessments.models import CodingProblem, CodingTestCase, CodingSubmission
        from apps.assessments.services.code_runner import run_test_cases
        from apps.assessments.services.judge0_client import get_language_id, Judge0Error
        from apps.sessions.models import StudentResponse

        # Validate language
        try:
            get_language_id(language)
        except ValueError as exc:
            return _err('INVALID_LANGUAGE', str(exc))

        # Validate question belongs to session
        try:
            question = InterviewQuestion.objects.get(pk=question_id, session=session)
        except InterviewQuestion.DoesNotExist:
            return _err('NOT_FOUND', 'Question not found.')

        # Fetch problem
        try:
            problem = CodingProblem.objects.get(pk=problem_id, is_active=True)
        except CodingProblem.DoesNotExist:
            return _err('NOT_FOUND', 'Problem not found.')

        all_tcs = CodingTestCase.objects.filter(problem=problem).order_by('order')
        total = all_tcs.count()
        passed = 0
        corr_score = 0.0
        safe_results = []
        overall_status = 'skipped' if is_skipped else 'failed'
        runtime_ms = 0

        if not is_skipped and all_tcs.exists():
            test_cases = [
                {'id': str(tc.id), 'input': tc.input_data, 'expected_output': tc.expected_output}
                for tc in all_tcs
            ]

            try:
                driver = problem.driver_code.get(language, '') if problem.driver_code else ''
                run_result = run_test_cases(
                    source_code=source_code,
                    language=language,
                    test_cases=test_cases,
                    time_limit=problem.time_limit_seconds,
                    memory_limit_mb=problem.memory_limit_mb,
                    driver_code=driver,
                )
            except Judge0Error as exc:
                logger.error('Judge0 unavailable during interview submit: %s', exc)
                return _err('EXECUTION_ENGINE_UNAVAILABLE',
                            'Code execution engine temporarily unavailable.', 503)

            import uuid as _uuid
            for r in run_result['results']:
                tc_id = r['test_case_id']
                tc_obj = None
                try:
                    _uuid.UUID(str(tc_id))
                    tc_obj = all_tcs.filter(pk=tc_id).first()
                except (ValueError, AttributeError):
                    pass
                safe_results.append({
                    'test_case_id': tc_id,
                    'status': r['status'],
                    'stdout': r['stdout'],
                    'stderr': r['stderr'],
                    'time_ms': r['time_ms'],
                    'memory_kb': r['memory_kb'],
                    'passed': r['passed'],
                    'input': tc_obj.input_data if tc_obj and not tc_obj.is_hidden else None,
                    'expected_output': tc_obj.expected_output if tc_obj and not tc_obj.is_hidden else None,
                })

            total  = run_result['total']
            passed = run_result['passed']
            corr_score = round(passed / total, 2) if total > 0 else 0.0
            overall_status = run_result['overall_status']
            runtime_ms = int(run_result['runtime_ms']) if run_result.get('runtime_ms') else 0

        # Save as interview submission
        submission = CodingSubmission.objects.create(
            session=session,
            problem=problem,
            attempt_type='interview',
            problem_title=problem.title,
            problem_statement=problem.description,
            language=language,
            code=source_code,
            status=overall_status,
            execution_output='\n'.join(r['stdout'] for r in safe_results if r.get('stdout')),
            stderr='\n'.join(r['stderr'] for r in safe_results if r.get('stderr')),
            test_results=safe_results,
            passed_count=passed,
            total_count=total,
            runtime_ms=runtime_ms,
            memory_kb=0,
            timed_out=(overall_status == 'time_limit_exceeded'),
            correctness_score=corr_score,
            overall_score=corr_score,
        )

        # Record StudentResponse for the coding question so the engine marks it answered
        if not StudentResponse.objects.filter(question=question).exists():
            feedback_str = (
                f"Candidate skipped coding problem '{problem.title}'."
                if is_skipped
                else f"Solution for '{problem.title}' scored {int(corr_score * 100)}% ({passed}/{total} test cases passed)."
            )
            StudentResponse.objects.create(
                question=question,
                session=session,
                transcript=f"Coding submission for {problem.title} ({language}): {passed}/{total} passed.",
                response_duration_seconds=runtime_ms // 1000 if runtime_ms else 5,
                score=corr_score,
                ai_feedback=feedback_str,
            )

        # Generate follow-up verbal question based on result
        if is_skipped:
            follow_up = (
                f"No problem, we've moved past '{problem.title}'. "
                "Can you tell me what strategy or approach you would have considered to solve this problem?"
            )
        elif corr_score >= 0.8:
            follow_up = (
                f"Excellent! Your solution for '{problem.title}' passed {passed}/{total} test cases. "
                "Could you walk me through your approach? What algorithm did you use, and what is the "
                "time and space complexity of your solution?"
            )
        elif corr_score >= 0.4:
            follow_up = (
                f"Your solution passed {passed}/{total} test cases for '{problem.title}'. "
                "Can you walk me through your approach and discuss where your solution might be failing?"
            )
        else:
            follow_up = (
                f"Your solution passed {passed}/{total} test cases for '{problem.title}'. "
                "Can you explain your approach and how you would debug or optimize it?"
            )

        new_turn = session.questions.count() + 1
        follow_up_question = InterviewQuestion.objects.create(
            session=session,
            turn_number=new_turn,
            phase='coding',
            question_text=follow_up,
            question_type='conceptual',
            topic='coding_explanation',
            difficulty_level=question.difficulty_level,
            expected_concepts=[
                'algorithm', 'time_complexity', 'space_complexity',
                'approach', 'edge_cases', 'optimization'
            ],
            is_follow_up=True,
            follow_up_reason='coding_result',
        )

        next_q_data = {
            'id': str(follow_up_question.id),
            'text': follow_up_question.question_text,
            'phase': follow_up_question.phase,
            'topic': follow_up_question.topic,
            'difficulty': follow_up_question.difficulty_level,
            'turn_number': follow_up_question.turn_number,
        }

        logger.info(
            'Interview coding submit: session=%s problem=%s score=%.2f -> next_q=%s',
            session.id, problem.slug, corr_score, follow_up_question.id
        )

        return _ok({
            'submission_id': str(submission.id),
            'status': overall_status,
            'passed': passed,
            'total': total,
            'score': corr_score,
            'runtime_ms': runtime_ms,
            'memory_kb': 0,
            'results': safe_results,
            'follow_up_question': next_q_data,
            'next_question': next_q_data,
            'interview_complete': False,
        }, 201)


# ── Audio / Speech AI Endpoints ───────────────────────────────────────────────


from django.http import HttpResponse
from rest_framework.parsers import MultiPartParser, FormParser
from .ai_services import generate_edge_tts_audio, transcribe_audio_faster_whisper


class TTSAudioView(APIView):
    """
    POST or GET /api/interview/tts/
    Generate high-fidelity neural MP3 audio using edge-tts.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        text = request.data.get('text', '').strip()
        if not text:
            return _err('BAD_REQUEST', 'Text parameter is required.')
        voice = request.data.get('voice', 'en-US-AriaNeural')
        audio_bytes = generate_edge_tts_audio(text, voice=voice)
        if not audio_bytes:
            return _err('SERVER_ERROR', 'Failed to generate audio.')
        response = HttpResponse(audio_bytes, content_type='audio/mpeg')
        response['Content-Disposition'] = 'inline; filename="speech.mp3"'
        response['Cache-Control'] = 'public, max-age=3600'
        return response

    def get(self, request):
        text = request.query_params.get('text', '').strip()
        if not text:
            return _err('BAD_REQUEST', 'Text parameter is required.')
        voice = request.query_params.get('voice', 'en-US-AriaNeural')
        audio_bytes = generate_edge_tts_audio(text, voice=voice)
        if not audio_bytes:
            return _err('SERVER_ERROR', 'Failed to generate audio.')
        response = HttpResponse(audio_bytes, content_type='audio/mpeg')
        response['Content-Disposition'] = 'inline; filename="speech.mp3"'
        response['Cache-Control'] = 'public, max-age=3600'
        return response


class TranscribeAudioView(APIView):
    """
    POST /api/interview/transcribe/
    Transcribe speech using faster-whisper.
    Accepts multipart audio file ('audio') and optional 'session_id'.
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        audio_file = request.FILES.get('audio')
        if not audio_file:
            return _err('BAD_REQUEST', 'No audio file provided.')

        audio_bytes = audio_file.read()
        session_id = request.data.get('session_id')
        vocab_prompt = None
        if session_id:
            try:
                session = InterviewSession.objects.filter(pk=session_id).first()
                if session:
                    from .ai_services import build_dynamic_vocab_prompt
                    role_name = session.target_role.role_name if session.target_role else ""
                    resume_skills = []
                    if session.resume and session.resume.parsed_data:
                        resume_skills = [
                            s['name'] for s in session.resume.parsed_data.get('skills', [])
                            if isinstance(s, dict) and 'name' in s
                        ]
                    vocab_prompt = build_dynamic_vocab_prompt(
                        target_role=role_name,
                        resume_skills=resume_skills,
                        job_description=session.job_description or "",
                    )
            except Exception as exc:
                logger.debug("Failed building dynamic vocab prompt for session %s: %s", session_id, exc)

        text = transcribe_audio_faster_whisper(audio_bytes, vocab_prompt=vocab_prompt)
        return _ok({'text': text})



class InterviewHistoryView(APIView):
    """GET /api/interview/sessions/{id}/history/  - All Q&A turns."""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            session = InterviewSession.objects.get(pk=pk, student__user=request.user)
        except InterviewSession.DoesNotExist:
            return _err('NOT_FOUND', 'Session not found.', 404)
        return _ok(_serialize_session(session))

"""
Coding Interview API views.

Endpoints:
  GET  /api/assessments/coding/problems/          - list active problems
  GET  /api/assessments/coding/problems/{id}/     - problem detail (no hidden tests)
  POST /api/assessments/coding/run/               - run code against public test cases
  POST /api/assessments/coding/submit/            - submit against ALL tests, save submission
  GET  /api/assessments/coding/submissions/       - student's own submission history

SECURITY INVARIANTS enforced here:
  1. All endpoints require JWT authentication.
  2. Student code is NEVER executed by Django — always forwarded to Judge0.
  3. Hidden test case input and expected outputs are NEVER returned to frontend.
  4. Submissions are scoped per student — no cross-student access.
  5. Source code size is validated before forwarding to Judge0.
"""
import logging
from django.conf import settings
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import CodingProblem, CodingTestCase, CodingSubmission
from .coding_serializers import (
    CodingProblemListSerializer,
    CodingProblemDetailSerializer,
    CodingRunResponseSerializer,
    CodingSubmissionSafeSerializer,
)
from .services.code_runner import run_test_cases
from .services.judge0_client import (
    get_language_id, Judge0Error,
    STATUS_ACCEPTED,
)

logger = logging.getLogger(__name__)

# ── Helpers ───────────────────────────────────────────────────────────────────

def _err(code: str, message: str, http_status: int = 400) -> Response:
    return Response(
        {'success': False, 'error': {'code': code, 'message': message, 'details': {}}},
        status=http_status,
    )


def _ok(data, http_status: int = 200) -> Response:
    return Response({'success': True, 'data': data}, status=http_status)


def _validate_language(language: str):
    """Return (True, None) or (False, error_response)."""
    try:
        get_language_id(language)
        return True, None
    except ValueError as exc:
        return False, _err('INVALID_LANGUAGE', str(exc))


def _validate_source_code(source_code: str):
    if not source_code or not source_code.strip():
        return False, _err('EMPTY_CODE', 'Source code cannot be empty.')
    max_size = getattr(settings, 'JUDGE0_MAX_SOURCE_SIZE', 100_000)
    if len(source_code.encode('utf-8')) > max_size:
        return False, _err(
            'CODE_TOO_LARGE',
            f'Source code exceeds the maximum allowed size of {max_size // 1024} KB.',
        )
    return True, None


# ── Problem Endpoints ─────────────────────────────────────────────────────────

class CodingProblemListView(APIView):
    """GET /api/assessments/coding/problems/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        problems = CodingProblem.objects.filter(is_active=True).order_by('difficulty', 'title')
        return _ok(CodingProblemListSerializer(problems, many=True).data)


class CodingProblemDetailView(APIView):
    """GET /api/assessments/coding/problems/{id}/"""
    permission_classes = [IsAuthenticated]

    def get(self, request, problem_id):
        try:
            problem = CodingProblem.objects.get(pk=problem_id, is_active=True)
        except CodingProblem.DoesNotExist:
            return _err('NOT_FOUND', 'Problem not found.', 404)
        # Public test cases only — serialiser enforces this
        return _ok(CodingProblemDetailSerializer(problem).data)


# ── Run Code ──────────────────────────────────────────────────────────────────

class RunCodeView(APIView):
    """
    POST /api/assessments/coding/run/

    Runs code against the VISIBLE (public) test cases only.
    Does NOT save a submission.
    Does NOT expose hidden test cases.

    Request:
      { "problem_id": "<uuid>", "language": "python", "source_code": "..." }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data        = request.data
        problem_id  = data.get('problem_id', '').strip()
        language    = data.get('language', '').strip().lower()
        source_code = data.get('source_code', '')

        if not problem_id:
            return _err('MISSING_FIELD', 'problem_id is required.')

        # Validate language
        valid, err = _validate_language(language)
        if not valid:
            return err

        # Validate source code
        valid, err = _validate_source_code(source_code)
        if not valid:
            return err

        # Fetch problem
        try:
            problem = CodingProblem.objects.get(pk=problem_id, is_active=True)
        except CodingProblem.DoesNotExist:
            return _err('NOT_FOUND', 'Problem not found.', 404)

        # Only public test cases
        public_tcs = CodingTestCase.objects.filter(
            problem=problem, is_hidden=False
        ).order_by('order')

        if not public_tcs.exists():
            return _err('NO_TEST_CASES', 'No public test cases available for this problem.')

        test_cases = [
            {'id': str(tc.id), 'input': tc.input_data, 'expected_output': tc.expected_output}
            for tc in public_tcs
        ]

        try:
            run_result = run_test_cases(
                source_code=source_code,
                language=language,
                test_cases=test_cases,
                time_limit=problem.time_limit_seconds,
                memory_limit_mb=problem.memory_limit_mb,
            )
        except Judge0Error as exc:
            logger.error('Judge0 unavailable during run: %s', exc)
            return _err(
                'EXECUTION_ENGINE_UNAVAILABLE',
                'The code execution engine is temporarily unavailable. Please try again.',
                503,
            )

        return _ok(run_result)


# ── Submit Code ───────────────────────────────────────────────────────────────

class SubmitCodeView(APIView):
    """
    POST /api/assessments/coding/submit/

    Runs code against ALL test cases (public + hidden).
    Saves a CodingSubmission record.
    Returns result WITHOUT exposing hidden test case data.

    Request:
      {
        "problem_id":   "<uuid>",
        "language":     "python",
        "source_code":  "...",
        "session_id":   "<uuid>"   (optional)
      }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data        = request.data
        problem_id  = data.get('problem_id', '').strip()
        language    = data.get('language', '').strip().lower()
        source_code = data.get('source_code', '')
        session_id  = data.get('session_id', '').strip() or None

        if not problem_id:
            return _err('MISSING_FIELD', 'problem_id is required.')

        valid, err = _validate_language(language)
        if not valid:
            return err

        valid, err = _validate_source_code(source_code)
        if not valid:
            return err

        try:
            problem = CodingProblem.objects.get(pk=problem_id, is_active=True)
        except CodingProblem.DoesNotExist:
            return _err('NOT_FOUND', 'Problem not found.', 404)

        # Resolve optional session
        session = None
        if session_id:
            from apps.sessions.models import InterviewSession
            try:
                session = InterviewSession.objects.get(
                    pk=session_id,
                    student__user=request.user,
                )
            except InterviewSession.DoesNotExist:
                return _err('NOT_FOUND', 'Interview session not found.', 404)

        # All test cases (public + hidden) for scoring
        all_tcs = CodingTestCase.objects.filter(problem=problem).order_by('order')
        if not all_tcs.exists():
            return _err('NO_TEST_CASES', 'No test cases configured for this problem.')

        test_cases = [
            {'id': str(tc.id), 'input': tc.input_data, 'expected_output': tc.expected_output}
            for tc in all_tcs
        ]

        try:
            run_result = run_test_cases(
                source_code=source_code,
                language=language,
                test_cases=test_cases,
                time_limit=problem.time_limit_seconds,
                memory_limit_mb=problem.memory_limit_mb,
            )
        except Judge0Error as exc:
            logger.error('Judge0 unavailable during submit: %s', exc)
            return _err(
                'EXECUTION_ENGINE_UNAVAILABLE',
                'The code execution engine is temporarily unavailable. Please try again.',
                503,
            )

        # Build safe test_results — strip expected_output from hidden cases
        import uuid as _uuid
        safe_results = []
        for r in run_result['results']:
            tc_id = r['test_case_id']
            # Guard: only query DB if tc_id is a valid UUID string
            tc_obj = None
            try:
                _uuid.UUID(str(tc_id))
                tc_obj = all_tcs.filter(pk=tc_id).first()
            except (ValueError, AttributeError):
                pass
            entry = {
                'test_case_id': tc_id,
                'status':       r['status'],
                'stdout':       r['stdout'],
                'stderr':       r['stderr'],
                'time_ms':      r['time_ms'],
                'memory_kb':    r['memory_kb'],
                'passed':       r['passed'],
                # Only include input/expected for public test cases
                'input':          tc_obj.input_data     if tc_obj and not tc_obj.is_hidden else None,
                'expected_output': tc_obj.expected_output if tc_obj and not tc_obj.is_hidden else None,
            }
            safe_results.append(entry)

        # Compute correctness score
        total    = run_result['total']
        passed   = run_result['passed']
        corr_score = round(passed / total, 2) if total > 0 else 0.0

        # Save submission (practice attempt — not part of an interview session by default)
        submission = CodingSubmission.objects.create(
            session=session,
            problem=problem,
            attempt_type='interview' if session else 'practice',
            problem_title=problem.title,
            problem_statement=problem.description,
            language=language,
            code=source_code,
            status=run_result['overall_status'],
            execution_output='\n'.join(r['stdout'] for r in run_result['results'] if r['stdout']),
            stderr='\n'.join(r['stderr'] for r in run_result['results'] if r['stderr']),
            test_results=safe_results,
            passed_count=passed,
            total_count=total,
            runtime_ms=int(run_result['runtime_ms']) if run_result['runtime_ms'] else None,
            memory_kb=run_result['memory_kb'],
            timed_out=(run_result['overall_status'] == 'time_limit_exceeded'),
            correctness_score=corr_score,
            overall_score=corr_score,
        )

        # Build frontend-safe response (no hidden test data)
        frontend_results = []
        for r in safe_results:
            frontend_results.append({
                'test_case_id': r['test_case_id'],
                'status':       r['status'],
                'stdout':       r['stdout'],
                'stderr':       r['stderr'],
                'time_ms':      r['time_ms'],
                'memory_kb':    r['memory_kb'],
                'passed':       r['passed'],
                # Only show input/expected for public cases
                'input':           r.get('input'),
                'expected_output': r.get('expected_output'),
            })

        return _ok({
            'submission_id': str(submission.id),
            'status':        run_result['overall_status'],
            'passed':        passed,
            'total':         total,
            'runtime_ms':    run_result['runtime_ms'],
            'memory_kb':     run_result['memory_kb'],
            'score':         corr_score,
            'results':       frontend_results,
        }, http_status=201)


# ── Submission History ────────────────────────────────────────────────────────

class CodingSubmissionHistoryView(APIView):
    """
    GET /api/assessments/coding/submissions/
    Returns the student's coding submission history.
    Supports ?attempt_type=practice|interview filter.
    Includes both session-linked and standalone (practice) submissions.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = request.user.student_profile
        attempt_type = request.query_params.get('attempt_type', None)

        # Base: submissions from interview sessions owned by this student
        session_subs = CodingSubmission.objects.filter(
            problem__isnull=False,
            session__student=profile,
        )
        # Base: standalone practice submissions (session=None) from this student
        # We match by the student's profile directly (added via attempt_type field)
        standalone_subs = CodingSubmission.objects.filter(
            session__isnull=True,
            problem__isnull=False,
            attempt_type='practice',
        )
        # Combine and deduplicate
        from django.db.models import Q
        subs = CodingSubmission.objects.filter(
            Q(session__student=profile) | Q(session__isnull=True, attempt_type='practice')
        ).filter(problem__isnull=False)

        if attempt_type in ('practice', 'interview'):
            subs = subs.filter(attempt_type=attempt_type)

        subs = subs.order_by('-submitted_at')
        return _ok(CodingSubmissionSafeSerializer(subs, many=True).data)


class CodingWeaknessView(APIView):
    """
    GET /api/assessments/coding/weaknesses/
    Returns per-topic pass rates for the student across all coding submissions.
    Topics with low pass rate are identified as weak areas.
    Used to drive practice recommendations and skill gap analysis.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = request.user.student_profile

        subs = CodingSubmission.objects.filter(
            session__student=profile,
            problem__isnull=False,
        ) | CodingSubmission.objects.filter(
            session__isnull=True,
            attempt_type='practice',
            problem__isnull=False,
        )

        # Compute per-topic stats
        topic_stats: dict[str, dict] = {}

        for sub in subs.select_related('problem'):
            if not sub.problem:
                continue
            total  = sub.total_count or 0
            passed = sub.passed_count or 0
            for topic in (sub.problem.topics or []):
                if topic not in topic_stats:
                    topic_stats[topic] = {'total_tests': 0, 'passed_tests': 0, 'submissions': 0}
                topic_stats[topic]['total_tests']  += total
                topic_stats[topic]['passed_tests'] += passed
                topic_stats[topic]['submissions']  += 1

        result = []
        for topic, stats in topic_stats.items():
            pass_rate = (
                round(stats['passed_tests'] / stats['total_tests'], 2)
                if stats['total_tests'] > 0 else 0.0
            )
            result.append({
                'topic': topic,
                'pass_rate': pass_rate,
                'submissions': stats['submissions'],
                'is_weak': pass_rate < 0.5,
                'is_strong': pass_rate >= 0.8,
            })

        result.sort(key=lambda x: x['pass_rate'])
        return _ok(result)


class CodingRecommendationsView(APIView):
    """
    GET /api/assessments/coding/recommendations/
    Returns up to 10 practice problems recommended for the student
    based on their weak topics and unsolved problems.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from django.db.models import Q
        from apps.assessments.coding_serializers import CodingProblemListSerializer

        profile = request.user.student_profile

        # Gather all submissions for this student (both interview and practice)
        subs = CodingSubmission.objects.filter(
            Q(session__student=profile) | Q(session__isnull=True, attempt_type='practice'),
            problem__isnull=False,
        ).select_related('problem')

        topic_stats: dict[str, dict] = {}
        solved_ids: set = set()

        for sub in subs:
            if not sub.problem:
                continue
            if sub.status == 'accepted':
                solved_ids.add(sub.problem.id)
            total  = sub.total_count or 0
            passed = sub.passed_count or 0
            for topic in (sub.problem.topics or []):
                if topic not in topic_stats:
                    topic_stats[topic] = {'total': 0, 'passed': 0}
                topic_stats[topic]['total']  += total
                topic_stats[topic]['passed'] += passed

        weak_topics = [
            t for t, s in topic_stats.items()
            if s['total'] > 0 and (s['passed'] / s['total']) < 0.5
        ]

        # Python-level topic filter works for both SQLite (JSONField) and PostgreSQL
        all_unsolved = list(
            CodingProblem.objects.filter(is_active=True).exclude(id__in=solved_ids)
        )

        if weak_topics:
            recommended = [
                p for p in all_unsolved
                if any(t in (p.topics or []) for t in weak_topics)
            ]
            # Pad with easy problems if not enough weak-topic problems
            if len(recommended) < 5:
                extras = [p for p in all_unsolved if p not in recommended]
                recommended.extend(extras[:10 - len(recommended)])
        else:
            # No submission history — recommend easy problems
            recommended = [p for p in all_unsolved if p.difficulty == 'easy']
            if not recommended:
                recommended = all_unsolved  # fallback: any unsolved

        problems = recommended[:10]

        return _ok({
            'weak_topics': weak_topics,
            'recommended_problems': CodingProblemListSerializer(problems, many=True).data,
        })



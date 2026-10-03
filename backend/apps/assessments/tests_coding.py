"""
Backend tests for the Coding Interview module.
Judge0 is mocked via patch('apps.assessments.coding_views.run_test_cases').
No live Judge0 instance required.

Run: pytest apps/assessments/tests_coding.py -v
"""
import json
import uuid
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.assessments.models import CodingProblem, CodingTestCase, CodingSubmission
from apps.assessments.services.evaluator import normalise_output, outputs_match
from apps.assessments.services.judge0_client import (
    STATUS_ACCEPTED,
    STATUS_COMPILATION_ERROR,
    STATUS_RUNTIME_ERROR,
    Judge0Error,
)

User = get_user_model()

# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def auth_client(db):
    user = User.objects.create_user(
        email="coder@test.com", password="Coder@2024", full_name="Coder Test"
    )
    c = APIClient()
    r = c.post("/api/auth/login", {"email": user.email, "password": "Coder@2024"}, format="json")
    token = r.data["data"]["tokens"]["access"]
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return c, user


@pytest.fixture
def problem(db):
    p = CodingProblem.objects.create(
        title="Two Sum Test",
        slug="two-sum-test-unique",
        difficulty="easy",
        description="Find two indices.",
        input_format="nums target",
        output_format="indices",
        starter_code={"python": "pass", "java": "// java", "cpp": "// cpp"},
        time_limit_seconds=2.0,
        memory_limit_mb=256,
        is_active=True,
    )
    CodingTestCase.objects.create(problem=p, input_data="2 7 11 15\n9", expected_output="0 1", is_hidden=False, order=0)
    CodingTestCase.objects.create(problem=p, input_data="3 2 4\n6",    expected_output="1 2", is_hidden=False, order=1)
    CodingTestCase.objects.create(problem=p, input_data="3 3\n6",      expected_output="0 1", is_hidden=True,  order=2)
    CodingTestCase.objects.create(problem=p, input_data="-1 -2 -3\n-3",expected_output="0 1", is_hidden=True,  order=3)
    return p


def _run_ok(n=2):
    """Return a run_test_cases result with n passing test cases."""
    results = [
        {"test_case_id": str(i), "status": STATUS_ACCEPTED, "stdout": "0 1",
         "stderr": "", "time_ms": 50.0, "memory_kb": 4096, "passed": True}
        for i in range(n)
    ]
    return {"overall_status": STATUS_ACCEPTED, "passed": n, "total": n,
            "runtime_ms": 50.0, "memory_kb": 4096, "results": results}


def _run_wa(n=2):
    results = [
        {"test_case_id": str(i), "status": "wrong_answer", "stdout": "9 9",
         "stderr": "", "time_ms": 60.0, "memory_kb": 4096, "passed": False}
        for i in range(n)
    ]
    return {"overall_status": "wrong_answer", "passed": 0, "total": n,
            "runtime_ms": 60.0, "memory_kb": 4096, "results": results}


def _run_ce():
    results = [{"test_case_id": "0", "status": STATUS_COMPILATION_ERROR,
                "stdout": "", "stderr": "SyntaxError", "time_ms": None, "memory_kb": None, "passed": False}]
    return {"overall_status": STATUS_COMPILATION_ERROR, "passed": 0, "total": 1,
            "runtime_ms": None, "memory_kb": None, "results": results}


def _run_re():
    results = [{"test_case_id": "0", "status": STATUS_RUNTIME_ERROR,
                "stdout": "", "stderr": "RuntimeError", "time_ms": 30.0, "memory_kb": 3000, "passed": False}]
    return {"overall_status": STATUS_RUNTIME_ERROR, "passed": 0, "total": 1,
            "runtime_ms": 30.0, "memory_kb": 3000, "results": results}


MOCK_TARGET = "apps.assessments.coding_views.run_test_cases"


# ── Authentication ─────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestCodingAuth:

    def test_problems_list_requires_auth(self, client):
        assert client.get("/api/assessments/coding/problems/").status_code == 401

    def test_problem_detail_requires_auth(self, client, problem):
        assert client.get(f"/api/assessments/coding/problems/{problem.id}/").status_code == 401

    def test_run_requires_auth(self, client):
        assert client.post("/api/assessments/coding/run/", {}, format="json").status_code == 401

    def test_submit_requires_auth(self, client):
        assert client.post("/api/assessments/coding/submit/", {}, format="json").status_code == 401


# ── Problem list / detail ──────────────────────────────────────────────────────

@pytest.mark.django_db
class TestCodingProblems:

    def test_list_authenticated(self, auth_client, problem):
        c, _ = auth_client
        r = c.get("/api/assessments/coding/problems/")
        assert r.status_code == 200
        ids = [p["id"] for p in r.data["data"]]
        assert str(problem.id) in ids

    def test_inactive_excluded(self, auth_client, problem):
        c, _ = auth_client
        problem.is_active = False
        problem.save()
        r = c.get("/api/assessments/coding/problems/")
        ids = [p["id"] for p in r.data["data"]]
        assert str(problem.id) not in ids

    def test_detail_has_only_public_test_cases(self, auth_client, problem):
        c, _ = auth_client
        r = c.get(f"/api/assessments/coding/problems/{problem.id}/")
        assert r.status_code == 200
        assert len(r.data["data"]["public_test_cases"]) == 2

    def test_hidden_input_not_in_response(self, auth_client, problem):
        c, _ = auth_client
        r = c.get(f"/api/assessments/coding/problems/{problem.id}/")
        assert "-1 -2 -3" not in json.dumps(r.data)

    def test_starter_code_present(self, auth_client, problem):
        c, _ = auth_client
        r = c.get(f"/api/assessments/coding/problems/{problem.id}/")
        sc = r.data["data"]["starter_code"]
        assert "python" in sc and "java" in sc and "cpp" in sc

    def test_unknown_id_returns_404(self, auth_client):
        c, _ = auth_client
        assert c.get(f"/api/assessments/coding/problems/{uuid.uuid4()}/").status_code == 404


# ── Run Code ───────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestRunCode:

    def test_missing_problem_id(self, auth_client):
        c, _ = auth_client
        r = c.post("/api/assessments/coding/run/", {"language": "python", "source_code": "pass"}, format="json")
        assert r.status_code == 400

    def test_invalid_language(self, auth_client, problem):
        c, _ = auth_client
        r = c.post("/api/assessments/coding/run/", {"problem_id": str(problem.id), "language": "cobol", "source_code": "pass"}, format="json")
        assert r.status_code == 400

    def test_empty_code(self, auth_client, problem):
        c, _ = auth_client
        r = c.post("/api/assessments/coding/run/", {"problem_id": str(problem.id), "language": "python", "source_code": ""}, format="json")
        assert r.status_code == 400

    def test_oversized_code(self, auth_client, problem):
        c, _ = auth_client
        r = c.post("/api/assessments/coding/run/", {"problem_id": str(problem.id), "language": "python", "source_code": "x" * 200_001}, format="json")
        assert r.status_code == 400

    @patch(MOCK_TARGET)
    def test_run_accepted(self, mock_rtc, auth_client, problem):
        mock_rtc.return_value = _run_ok(2)
        c, _ = auth_client
        r = c.post("/api/assessments/coding/run/", {"problem_id": str(problem.id), "language": "python", "source_code": 'print("0 1")'}, format="json")
        assert r.status_code == 200
        assert r.data["data"]["passed"] == 2
        assert r.data["data"]["overall_status"] == STATUS_ACCEPTED

    @patch(MOCK_TARGET)
    def test_run_wrong_answer(self, mock_rtc, auth_client, problem):
        mock_rtc.return_value = _run_wa(2)
        c, _ = auth_client
        r = c.post("/api/assessments/coding/run/", {"problem_id": str(problem.id), "language": "python", "source_code": 'print("9 9")'}, format="json")
        assert r.status_code == 200
        assert r.data["data"]["passed"] == 0

    @patch(MOCK_TARGET)
    def test_run_compilation_error(self, mock_rtc, auth_client, problem):
        mock_rtc.return_value = _run_ce()
        c, _ = auth_client
        r = c.post("/api/assessments/coding/run/", {"problem_id": str(problem.id), "language": "python", "source_code": "!!!"}, format="json")
        assert r.data["data"]["overall_status"] == STATUS_COMPILATION_ERROR

    @patch(MOCK_TARGET)
    def test_run_runtime_error(self, mock_rtc, auth_client, problem):
        mock_rtc.return_value = _run_re()
        c, _ = auth_client
        r = c.post("/api/assessments/coding/run/", {"problem_id": str(problem.id), "language": "python", "source_code": "1/0"}, format="json")
        assert r.data["data"]["overall_status"] == STATUS_RUNTIME_ERROR

    @patch(MOCK_TARGET)
    def test_judge0_unavailable_returns_503(self, mock_rtc, auth_client, problem):
        mock_rtc.side_effect = Judge0Error("down")
        c, _ = auth_client
        r = c.post("/api/assessments/coding/run/", {"problem_id": str(problem.id), "language": "python", "source_code": "pass"}, format="json")
        assert r.status_code == 503

    @patch(MOCK_TARGET)
    def test_run_never_exposes_hidden_input(self, mock_rtc, auth_client, problem):
        mock_rtc.return_value = _run_ok(2)
        c, _ = auth_client
        r = c.post("/api/assessments/coding/run/", {"problem_id": str(problem.id), "language": "python", "source_code": "pass"}, format="json")
        assert "-1 -2 -3" not in json.dumps(r.data)


# ── Submit Code ────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestSubmitCode:

    @patch(MOCK_TARGET)
    def test_submit_accepted_creates_submission(self, mock_rtc, auth_client, problem):
        mock_rtc.return_value = _run_ok(4)
        c, _ = auth_client
        r = c.post("/api/assessments/coding/submit/", {"problem_id": str(problem.id), "language": "python", "source_code": 'print("0 1")'}, format="json")
        assert r.status_code == 201
        assert r.data["data"]["status"] == STATUS_ACCEPTED
        assert r.data["data"]["passed"] == 4
        assert CodingSubmission.objects.filter(problem=problem).count() == 1

    @patch(MOCK_TARGET)
    def test_submit_wrong_answer(self, mock_rtc, auth_client, problem):
        mock_rtc.return_value = _run_wa(4)
        c, _ = auth_client
        r = c.post("/api/assessments/coding/submit/", {"problem_id": str(problem.id), "language": "python", "source_code": 'print("9 9")'}, format="json")
        assert r.status_code == 201
        assert r.data["data"]["passed"] == 0

    @patch(MOCK_TARGET)
    def test_hidden_output_never_exposed(self, mock_rtc, auth_client, problem):
        mock_rtc.return_value = _run_ok(4)
        c, _ = auth_client
        r = c.post("/api/assessments/coding/submit/", {"problem_id": str(problem.id), "language": "python", "source_code": "pass"}, format="json")
        assert "-1 -2 -3" not in json.dumps(r.data)

    def test_invalid_problem_404(self, auth_client):
        c, _ = auth_client
        r = c.post("/api/assessments/coding/submit/", {"problem_id": str(uuid.uuid4()), "language": "python", "source_code": "pass"}, format="json")
        assert r.status_code == 404

    def test_invalid_language_400(self, auth_client, problem):
        c, _ = auth_client
        r = c.post("/api/assessments/coding/submit/", {"problem_id": str(problem.id), "language": "haskell", "source_code": "pass"}, format="json")
        assert r.status_code == 400

    def test_empty_code_400(self, auth_client, problem):
        c, _ = auth_client
        r = c.post("/api/assessments/coding/submit/", {"problem_id": str(problem.id), "language": "python", "source_code": "   "}, format="json")
        assert r.status_code == 400

    @patch(MOCK_TARGET)
    def test_bad_session_id_returns_404(self, mock_rtc, auth_client, problem):
        mock_rtc.return_value = _run_ok(4)
        c, _ = auth_client
        r = c.post("/api/assessments/coding/submit/", {"problem_id": str(problem.id), "language": "python", "source_code": "pass", "session_id": str(uuid.uuid4())}, format="json")
        assert r.status_code == 404


# ── Evaluator unit tests (pure Python, no DB, no network) ──────────────────────

class TestOutputNormalisation:

    def test_strips_trailing_newline(self):         assert outputs_match("0 1\n", "0 1")
    def test_strips_trailing_spaces(self):          assert outputs_match("0 1  ", "0 1")
    def test_normalises_crlf(self):                 assert outputs_match("0 1\r\n", "0 1\n")
    def test_case_sensitive(self):                  assert not outputs_match("True", "true")
    def test_different_values_no_match(self):       assert not outputs_match("0 1", "1 0")
    def test_empty_vs_empty(self):                  assert outputs_match("", "")
    def test_multiline_match(self):                 assert outputs_match("1\n2\n3\n", "1\n2\n3")
    def test_trailing_blank_lines_stripped(self):   assert normalise_output("hello\n\n\n") == "hello"
    def test_whitespace_only_is_empty(self):        assert normalise_output("   \n  \n") == ""

"""
Automated Test Suite for QAOA-Based Preparation Planning System.

Tests cover:
1. Multi-objective value function & priority multipliers
2. QUBO formulation & Ising Hamiltonian equivalence
3. Deterministic feasibility repair for capacity & prerequisite dependencies
4. Exact classical knapsack benchmark solver
5. QAOA quantum circuit execution & statevector probability measurement
6. Interview feedback extraction (mock interview vs resume cold-start)
7. Plan generation, daily timetable scheduling & database persistence
8. REST API endpoints (feedback analysis, generate, active plan, module patch, quantum benchmark)
"""

import uuid
import numpy as np
import pytest
from decimal import Decimal
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.accounts.models import StudentProfile
from apps.resumes.models import TargetRole
from apps.sessions.models import InterviewSession, InterviewQuestion, StudentResponse
from apps.assessments.services.report_generator import generate_assessment_report
from apps.preparation.models import PreparationPlan, PracticeModule
from apps.preparation.services.qaoa_optimizer import (
    calculate_activity_value,
    build_qubo_matrix,
    qubo_to_ising,
    repair_solution,
    solve_classical_knapsack,
    run_qaoa_optimization,
)
from apps.preparation.services.feedback_extractor import (
    extract_feedback_and_activity_pool,
    TOPIC_CURRICULUM,
)
from apps.preparation.services.plan_generator import (
    schedule_activities_into_days,
    generate_preparation_plan,
)

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def student_user(db):
    user = User.objects.create_user(
        email=f'qaoa_{uuid.uuid4().hex[:6]}@example.com',
        full_name='Quantum Candidate',
        password='TestPassword123!',
    )
    profile = user.student_profile
    profile.department = 'Computer Science'
    profile.graduation_year = 2026
    profile.save()
    return user, profile


@pytest.fixture
def target_role(db, student_user):
    _, profile = student_user
    return TargetRole.objects.create(
        student=profile,
        role_name='Full Stack Quantum Software Engineer',
        domain='software_engineering',
        is_primary=True,
    )


# -----------------------------------------------------------------------------
# Unit Tests: QAOA Optimizer Mathematical Formulations
# -----------------------------------------------------------------------------

def test_activity_value_calculation():
    """Verify value function weights: 40% gap, 35% relevance, 25% impact + 15% priority boost."""
    act = {
        'id': 'arrays_hashing',
        'topic': 'Arrays & Hashing',
        'category': 'coding',
        'skill_gap_severity': 0.60,
        'role_relevance': 0.80,
        'selection_impact_estimate': 0.70,
    }
    # Expected base: 100 * (0.40 * 0.60 + 0.35 * 0.80 + 0.25 * 0.70) = 100 * (0.24 + 0.28 + 0.175) = 69.5
    val_base = calculate_activity_value(act, priority_areas=None)
    assert val_base == pytest.approx(69.5, abs=0.1)

    # With priority boost on 'coding'
    val_boosted = calculate_activity_value(act, priority_areas=['coding'])
    assert val_boosted == pytest.approx(69.5 * 1.15, abs=0.1)
    assert 1.0 <= val_boosted <= 100.0


def test_qubo_and_ising_energy_equivalence():
    """Verify QUBO cost matches Ising Hamiltonian energy for all bitstrings."""
    values = [50.0, 40.0, 30.0]
    weights = [2.0, 2.0, 1.5]
    capacity = 4.0
    prereqs = [(0, 1)]  # item 1 requires item 0

    Q, offset = build_qubo_matrix(values, weights, capacity, prereqs)
    h_coeffs, j_coeffs, ising_offset = qubo_to_ising(Q, offset)

    # Check for all 2^3 = 8 binary configurations
    for x0 in (0, 1):
        for x1 in (0, 1):
            for x2 in (0, 1):
                x = np.array([x0, x1, x2], dtype=float)
                qubo_cost = float(np.dot(x, np.dot(Q, x)) + offset)

                # Ising spin Z = 1 - 2*x
                z0, z1, z2 = 1.0 - 2.0 * x0, 1.0 - 2.0 * x1, 1.0 - 2.0 * x2
                ising_cost = ising_offset + h_coeffs[0]*z0 + h_coeffs[1]*z1 + h_coeffs[2]*z2
                ising_cost += j_coeffs.get((0, 1), 0.0) * z0 * z1
                ising_cost += j_coeffs.get((0, 2), 0.0) * z0 * z2
                ising_cost += j_coeffs.get((1, 2), 0.0) * z1 * z2

                assert qubo_cost == pytest.approx(ising_cost, abs=1e-4)


def test_repair_solution_prerequisite_and_budget():
    """Verify deterministic repair fixes broken prerequisites and knapsack over-budget."""
    values = [60.0, 70.0, 50.0]
    weights = [2.5, 3.0, 2.0]
    capacity = 5.0
    prereqs = [(0, 1)]  # 1 requires 0

    # Initial selection: only item 1 selected (violates prerequisite: requires 0)
    # Total hours: 3.0 (budget ok, but prereq violated)
    # Adding 0 would take 3.0 + 2.5 = 5.5 > 5.0 (exceeds budget)
    # Therefore repair must drop 1 and pack valid alternatives
    repaired = repair_solution(
        initial_indices=[1],
        values=values,
        weights=weights,
        capacity=capacity,
        prereq_pairs=prereqs
    )

    assert repaired['is_feasible'] is True
    assert repaired['total_hours'] <= capacity
    # If 1 is present, 0 must also be present
    if 1 in repaired['selected_indices']:
        assert 0 in repaired['selected_indices']


def test_classical_exact_benchmark():
    """Verify classical solver finds the provably optimal solution."""
    values = [30.0, 50.0, 40.0]
    weights = [1.0, 2.0, 2.0]
    capacity = 3.0
    prereqs = [(0, 1)]  # 1 requires 0

    # Options with capacity <= 3.0:
    # {0} -> w=1.0, v=30
    # {2} -> w=2.0, v=40
    # {0, 1} -> w=3.0, v=80 (valid, 1 has 0)
    # {0, 2} -> w=3.0, v=70
    # Optimal is {0, 1} with value 80.0
    sol = solve_classical_knapsack(values, weights, capacity, prereqs)
    assert set(sol['selected_indices']) == {0, 1}
    assert sol['total_value'] == 80.0
    assert sol['total_hours'] == 3.0
    assert sol['is_optimal'] is True


def test_qaoa_quantum_circuit_execution():
    """Verify live QAOA execution runs Qiskit quantum circuit and returns valid metadata."""
    sample_activities = [
        {'id': 'act_a', 'topic': 'A', 'category': 'coding', 'skill_gap_severity': 0.7, 'role_relevance': 0.8, 'selection_impact_estimate': 0.75, 'estimated_study_hours': 2.0, 'prerequisites': []},
        {'id': 'act_b', 'topic': 'B', 'category': 'coding', 'skill_gap_severity': 0.6, 'role_relevance': 0.7, 'selection_impact_estimate': 0.65, 'estimated_study_hours': 2.5, 'prerequisites': ['act_a']},
        {'id': 'act_c', 'topic': 'C', 'category': 'system_design', 'skill_gap_severity': 0.8, 'role_relevance': 0.9, 'selection_impact_estimate': 0.85, 'estimated_study_hours': 3.0, 'prerequisites': []},
    ]
    res = run_qaoa_optimization(
        activities=sample_activities,
        total_hours_budget=5.0,
        priority_areas=['coding'],
        max_qubits=4,
        p_layers=1
    )

    assert res['success'] is True
    assert res['is_quantum'] is True
    assert res['algorithm_used'] == 'QAOA_Statevector_p1'
    assert res['num_qubits'] == 3
    assert res['circuit_depth'] > 0
    assert res['total_hours'] <= 5.0 + 1e-5
    assert 'classical_comparison' in res
    assert res['classical_comparison']['qaoa_approximation_ratio'] > 0.0


# -----------------------------------------------------------------------------
# Service Tests: Feedback Extractor & Plan Generator
# -----------------------------------------------------------------------------

@pytest.mark.django_db
def test_feedback_extractor_cold_start(student_user, target_role):
    """Verify cold-start feedback extraction without prior mock interview."""
    _, profile = student_user
    feedback = extract_feedback_and_activity_pool(
        student_profile=profile,
        session=None,
        target_role=target_role
    )

    assert feedback['has_mock_interview'] is False
    assert feedback['session_id'] is None
    assert len(feedback['activity_pool']) > 0
    assert feedback['total_activities_available'] >= 8
    # All curriculum items have expected schema
    first = feedback['activity_pool'][0]
    assert 'topic' in first
    assert 'current_score' in first
    assert 'skill_gap_severity' in first
    assert 'role_relevance' in first
    assert 'estimated_study_hours' in first


@pytest.mark.django_db
def test_plan_generator_end_to_end(student_user, target_role):
    """Verify end-to-end plan generation, timetable sequencing, and DB persistence."""
    _, profile = student_user

    plan = generate_preparation_plan(
        student_profile=profile,
        session=None,
        target_role_id=str(target_role.id),
        days_remaining=5,
        daily_hours=2.0,
        total_hours_budget=10.0,
        priority_areas=['coding', 'system_design'],
    )

    assert plan is not None
    assert plan.student == profile
    assert plan.target_role == target_role
    assert plan.is_active is True
    assert plan.preparation_days == 5
    assert plan.daily_hours == 2.0
    assert plan.total_hours_budget == 10.0

    # Modules persisted
    modules = list(plan.practice_modules.all())
    assert len(modules) > 0
    assert sum(float(m.estimated_hours) for m in modules) <= 10.0 + 1e-5

    # Check topological scheduling: prerequisites appear on <= scheduled_day
    mod_day_map = {m.activity_id: m.scheduled_day for m in modules}
    for m in modules:
        for prereq_id in m.prerequisites:
            if prereq_id in mod_day_map:
                assert mod_day_map[prereq_id] <= m.scheduled_day


# -----------------------------------------------------------------------------
# REST API Tests: Endpoints & Permissions
# -----------------------------------------------------------------------------

@pytest.mark.django_db
def test_feedback_analysis_api(api_client, student_user, target_role):
    """Test GET /api/preparation/feedback-analysis/ endpoint."""
    user, profile = student_user
    # Unauthenticated
    res = api_client.get('/api/preparation/feedback-analysis/')
    assert res.status_code == 401

    # Authenticated
    api_client.force_authenticate(user=user)
    res = api_client.get('/api/preparation/feedback-analysis/')
    assert res.status_code == 200
    assert res.data['success'] is True
    assert 'activity_pool' in res.data['data']


@pytest.mark.django_db
def test_generate_and_get_plan_api(api_client, student_user, target_role):
    """Test POST /api/preparation/plans/generate/ and GET /api/preparation/plans/active/."""
    user, profile = student_user
    api_client.force_authenticate(user=user)

    payload = {
        'target_role_id': str(target_role.id),
        'days_remaining': 7,
        'daily_hours': 2.0,
        'total_hours_budget': 14.0,
        'priority_areas': ['coding'],
        'force_algorithm': 'qaoa',
    }
    res = api_client.post('/api/preparation/plans/generate/', data=payload, format='json')
    assert res.status_code == 201
    assert res.data['success'] is True
    plan_data = res.data['data']
    assert plan_data['preparation_days'] == 7
    assert len(plan_data['practice_modules']) > 0

    # Get active plan
    res_active = api_client.get('/api/preparation/plans/active/')
    assert res_active.status_code == 200
    assert res_active.data['data']['id'] == plan_data['id']


@pytest.mark.django_db
def test_practice_module_update_status_api(api_client, student_user, target_role):
    """Test PATCH /api/preparation/modules/<id>/ endpoint."""
    user, profile = student_user
    api_client.force_authenticate(user=user)

    plan = generate_preparation_plan(
        student_profile=profile,
        target_role_id=str(target_role.id),
        days_remaining=5,
        daily_hours=2.0,
    )
    first_module = plan.practice_modules.first()
    assert first_module.status == 'pending'

    # Update to completed
    res = api_client.patch(
        f'/api/preparation/modules/{first_module.id}/',
        data={'status': 'completed'},
        format='json'
    )
    assert res.status_code == 200
    assert res.data['data']['status'] == 'completed'
    assert res.data['data']['completed_at'] is not None

    first_module.refresh_from_db()
    assert first_module.status == 'completed'
    assert first_module.is_completed is True


@pytest.mark.django_db
def test_quantum_benchmark_api(api_client, student_user):
    """Test POST /api/preparation/benchmark/ endpoint."""
    user, profile = student_user
    api_client.force_authenticate(user=user)

    res = api_client.post(
        '/api/preparation/benchmark/',
        data={'num_qubits': 5, 'total_hours_budget': 10.0, 'p_layers': 1},
        format='json'
    )
    assert res.status_code == 200
    assert res.data['success'] is True
    bm_data = res.data['data']
    assert bm_data['problem_size_qubits'] == 5
    assert 'qaoa_execution_time_ms' in bm_data
    assert 'classical_comparison' in bm_data


@pytest.mark.django_db
def test_unanswered_interview_zero_score_and_honest_feedback(student_user, target_role):
    """
    Verify that if a candidate completes an interview but leaves all questions
    unanswered (silence / blank), the assessment report:
    1. Returns overall_score = 0.00 (0%, NOT 60% or 70%)
    2. Returns communication_score = 0.00
    3. Contains NO false strengths
    4. Feedback extractor populates 'weak_areas' with 0% score and high priority
    5. Feedback extractor 'strong_areas' is empty
    6. Activity pool assigns 0.00 score and high gap severity to unanswered topics
    """
    user, profile = student_user
    session = InterviewSession.objects.create(
        student=profile,
        target_role=target_role,
        status='completed',
        started_at=timezone.now(),
        ended_at=timezone.now(),
        duration_seconds=120,
    )
    # 2 questions asked, but 0 answers submitted
    InterviewQuestion.objects.create(
        session=session,
        turn_number=1,
        question_text="Explain indexing and B-Trees in database systems.",
        topic="Databases & Indexing",
    )
    InterviewQuestion.objects.create(
        session=session,
        turn_number=2,
        question_text="How does Dijkstra's algorithm work?",
        topic="Graph Algorithms",
    )
    assessment = generate_assessment_report(session)

    assert float(assessment.overall_score) == 0.0
    assert float(assessment.technical_score) == 0.0
    assert float(assessment.communication_score) == 0.0
    assert len(assessment.strengths) == 0
    assert len(assessment.improvement_areas) >= 2

    feedback = extract_feedback_and_activity_pool(
        student_profile=profile,
        session=session,
        target_role=target_role
    )

    assert feedback['interview_metrics']['total_questions_asked'] == 2
    assert feedback['interview_metrics']['questions_answered'] == 0
    assert feedback['interview_metrics']['overall_score_pct'] == 0
    assert len(feedback['strong_areas']) == 0
    assert len(feedback['weak_areas']) >= 2

    wa_statuses = [wa['status'] for wa in feedback['weak_areas']]
    assert 'unanswered' in wa_statuses
    for wa in feedback['weak_areas']:
        if wa['status'] == 'unanswered':
            assert wa['score_pct'] == 0
            assert wa['priority'] == 'high'

    db_act = next((a for a in feedback['activity_pool'] if 'database' in a['topic'].lower()), None)
    if db_act:
        assert db_act['current_score'] == 0.0
        assert db_act['skill_gap_severity'] >= 0.85


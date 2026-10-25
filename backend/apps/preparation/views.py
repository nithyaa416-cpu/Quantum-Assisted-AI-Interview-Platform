"""
API Views for QAOA Personalized Preparation Planning & Benchmark Suite.
"""
import logging
from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.sessions.models import InterviewSession
from apps.resumes.models import TargetRole
from .models import PreparationPlan, PracticeModule
from .serializers import (
    PreparationPlanSerializer,
    PracticeModuleSerializer,
    GeneratePlanRequestSerializer,
    ModuleStatusUpdateSerializer,
    BenchmarkRequestSerializer,
)
from .services.feedback_extractor import extract_feedback_and_activity_pool
from .services.plan_generator import generate_preparation_plan
from .services.qaoa_optimizer import (
    run_qaoa_optimization,
    solve_classical_knapsack,
    calculate_activity_value,
    repair_solution,
)

logger = logging.getLogger(__name__)


class FeedbackAnalysisView(APIView):
    """
    GET /api/preparation/feedback-analysis/
    Extracts structured skill gaps, candidate strengths, and recommended activities
    based on the student's mock interview (or resume cold-start).
    Query params:
      - session_id (optional UUID of specific mock interview session)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = request.user.student_profile
        session_id = request.query_params.get('session_id')
        session = None

        if session_id:
            try:
                session = InterviewSession.objects.get(id=session_id, student=profile)
            except InterviewSession.DoesNotExist:
                return Response(
                    {'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'Interview session not found.'}},
                    status=status.HTTP_404_NOT_FOUND,
                )
        else:
            # Pick the most recent completed interview session if available
            session = (
                InterviewSession.objects.filter(student=profile, status='completed')
                .order_by('-ended_at', '-created_at')
                .first()
            )

        feedback_data = extract_feedback_and_activity_pool(
            student_profile=profile,
            session=session
        )

        return Response({
            'success': True,
            'data': feedback_data
        })


class GeneratePlanView(APIView):
    """
    POST /api/preparation/plans/generate/
    Generates a personalized, QAOA-optimized preparation plan with daily practice modules.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = GeneratePlanRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'success': False, 'error': {'code': 'VALIDATION_ERROR', 'details': serializer.errors}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data
        profile = request.user.student_profile

        # Resolve optional session
        session = None
        if data.get('session_id'):
            try:
                session = InterviewSession.objects.get(id=data['session_id'], student=profile)
            except InterviewSession.DoesNotExist:
                return Response(
                    {'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'Specified interview session not found.'}},
                    status=status.HTTP_404_NOT_FOUND,
                )
        else:
            # Default to most recent completed interview session if available
            session = (
                InterviewSession.objects.filter(student=profile, status='completed')
                .order_by('-ended_at', '-created_at')
                .first()
            )

        try:
            plan = generate_preparation_plan(
                student_profile=profile,
                session=session,
                target_role_id=str(data['target_role_id']) if data.get('target_role_id') else None,
                days_remaining=data.get('days_remaining', 7),
                daily_hours=data.get('daily_hours', 2.0),
                total_hours_budget=data.get('total_hours_budget'),
                priority_areas=data.get('priority_areas', []),
                preferred_categories=data.get('preferred_categories', []),
                force_algorithm=data.get('force_algorithm', 'qaoa'),
            )
            return Response(
                {'success': True, 'data': PreparationPlanSerializer(plan).data},
                status=status.HTTP_201_CREATED,
            )
        except Exception as exc:
            logger.exception(f"Error generating QAOA preparation plan: {exc}")
            return Response(
                {'success': False, 'error': {'code': 'OPTIMIZATION_ERROR', 'message': str(exc)}},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class PreparationPlanListView(APIView):
    """GET /api/preparation/plans/ — List the student's preparation plans."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = request.user.student_profile
        plans = PreparationPlan.objects.filter(student=profile).order_by('-generated_at')
        return Response(
            {'success': True, 'data': PreparationPlanSerializer(plans, many=True).data}
        )


class ActivePreparationPlanView(APIView):
    """GET /api/preparation/plans/active/ — Get the current active plan with modules."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = request.user.student_profile
        try:
            plan = PreparationPlan.objects.get(student=profile, is_active=True)
        except PreparationPlan.DoesNotExist:
            return Response(
                {'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'No active preparation plan found.'}},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response({'success': True, 'data': PreparationPlanSerializer(plan).data})


class PreparationPlanDetailView(APIView):
    """GET /api/preparation/plans/{id}/ — Get a specific plan by ID."""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        profile = request.user.student_profile
        try:
            plan = PreparationPlan.objects.get(pk=pk, student=profile)
        except PreparationPlan.DoesNotExist:
            return Response(
                {'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'Preparation plan not found.'}},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response({'success': True, 'data': PreparationPlanSerializer(plan).data})


class RegeneratePlanView(APIView):
    """
    POST /api/preparation/plans/{id}/regenerate/
    Regenerates a plan based on existing parameters with optional overrides.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        profile = request.user.student_profile
        try:
            existing_plan = PreparationPlan.objects.get(pk=pk, student=profile)
        except PreparationPlan.DoesNotExist:
            return Response(
                {'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'Preparation plan not found.'}},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = GeneratePlanRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'success': False, 'error': {'code': 'VALIDATION_ERROR', 'details': serializer.errors}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data

        try:
            new_plan = generate_preparation_plan(
                student_profile=profile,
                session=existing_plan.session,
                target_role_id=str(existing_plan.target_role.id) if existing_plan.target_role else None,
                days_remaining=data.get('days_remaining', existing_plan.preparation_days),
                daily_hours=data.get('daily_hours', existing_plan.daily_hours),
                total_hours_budget=data.get('total_hours_budget', existing_plan.total_hours_budget),
                priority_areas=data.get('priority_areas', existing_plan.priority_areas or []),
                preferred_categories=data.get('preferred_categories', []),
                force_algorithm=data.get('force_algorithm', 'qaoa'),
            )
            return Response(
                {'success': True, 'data': PreparationPlanSerializer(new_plan).data},
                status=status.HTTP_201_CREATED,
            )
        except Exception as exc:
            logger.exception(f"Error regenerating QAOA plan: {exc}")
            return Response(
                {'success': False, 'error': {'code': 'OPTIMIZATION_ERROR', 'message': str(exc)}},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class PracticeModuleListView(APIView):
    """
    GET /api/preparation/modules/
    List practice modules for active plan (or by ?plan_id=<uuid>).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = request.user.student_profile
        plan_id = request.query_params.get('plan_id')

        if plan_id:
            modules = PracticeModule.objects.filter(
                student=profile, plan_id=plan_id
            ).order_by('scheduled_day', 'order')
        else:
            modules = PracticeModule.objects.filter(
                student=profile, plan__is_active=True
            ).order_by('scheduled_day', 'order')

        return Response(
            {'success': True, 'data': PracticeModuleSerializer(modules, many=True).data}
        )


class PracticeModuleUpdateView(APIView):
    """
    PATCH /api/preparation/modules/{id}/
    Updates completion status: 'pending', 'in_progress', 'completed', or 'skipped'.
    """
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        try:
            module = PracticeModule.objects.get(pk=pk, student__user=request.user)
        except PracticeModule.DoesNotExist:
            return Response(
                {'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'Practice module not found.'}},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ModuleStatusUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'success': False, 'error': {'code': 'VALIDATION_ERROR', 'details': serializer.errors}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        new_status = serializer.validated_data['status']
        module.status = new_status
        if new_status == 'completed' and not module.completed_at:
            module.completed_at = timezone.now()
        elif new_status != 'completed':
            module.completed_at = None

        module.save(update_fields=['status', 'completed_at'])
        return Response({'success': True, 'data': PracticeModuleSerializer(module).data})


class QuantumBenchmarkView(APIView):
    """
    POST /api/preparation/benchmark/
    Runs a live benchmark comparing QAOA vs Classical Exact Branch-and-Bound on the
    candidate's actual curriculum space.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = BenchmarkRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'success': False, 'error': {'code': 'VALIDATION_ERROR', 'details': serializer.errors}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data
        num_qubits = data.get('num_qubits', 6)
        budget = data.get('total_hours_budget', 12.0)
        p_layers = data.get('p_layers', 1)

        profile = request.user.student_profile
        feedback = extract_feedback_and_activity_pool(student_profile=profile)
        pool = feedback.get('activity_pool', [])

        benchmark_result = run_qaoa_optimization(
            activities=pool,
            total_hours_budget=budget,
            max_qubits=num_qubits,
            p_layers=p_layers
        )

        return Response({
            'success': True,
            'data': {
                'problem_size_qubits': benchmark_result.get('num_qubits'),
                'total_budget_hours': budget,
                'circuit_depth': benchmark_result.get('circuit_depth'),
                'qaoa_execution_time_ms': benchmark_result.get('execution_time_ms'),
                'qaoa_circuit_time_ms': benchmark_result.get('qaoa_circuit_time_ms'),
                'qaoa_total_value': benchmark_result.get('total_value'),
                'qaoa_hours_scheduled': benchmark_result.get('total_hours'),
                'qaoa_is_feasible': benchmark_result.get('raw_solution', {}).get('is_feasible'),
                'repair_applied': benchmark_result.get('repair_applied'),
                'classical_comparison': benchmark_result.get('classical_comparison'),
                'top_measurement_states': benchmark_result.get('top_measurement_states'),
            }
        })

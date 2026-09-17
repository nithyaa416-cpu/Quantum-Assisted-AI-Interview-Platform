"""Views for preparation plans and practice modules."""
import logging
from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import PreparationPlan, PracticeModule
from .serializers import PreparationPlanSerializer, PracticeModuleSerializer

logger = logging.getLogger(__name__)


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
    """GET /api/preparation/plans/active/ — Get the current active plan."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = request.user.student_profile
        try:
            plan = PreparationPlan.objects.get(student=profile, is_active=True)
        except PreparationPlan.DoesNotExist:
            return Response(
                {'success': False, 'error': {'code': 'NOT_FOUND',
                                              'message': 'No active preparation plan found.',
                                              'details': {}}},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response({'success': True, 'data': PreparationPlanSerializer(plan).data})


class PracticeModuleListView(APIView):
    """GET /api/preparation/modules/ — List practice modules for the active plan."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = request.user.student_profile
        modules = PracticeModule.objects.filter(student=profile).order_by('scheduled_day')
        return Response(
            {'success': True, 'data': PracticeModuleSerializer(modules, many=True).data}
        )


class PracticeModuleUpdateView(APIView):
    """PATCH /api/preparation/modules/{id}/ — Mark a module complete/in-progress."""
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        try:
            module = PracticeModule.objects.get(pk=pk, student__user=request.user)
        except PracticeModule.DoesNotExist:
            return Response(
                {'success': False, 'error': {'code': 'NOT_FOUND',
                                              'message': 'Practice module not found.',
                                              'details': {}}},
                status=status.HTTP_404_NOT_FOUND,
            )

        new_status = request.data.get('status')
        if new_status not in dict(PracticeModule.STATUS_CHOICES):
            return Response(
                {'success': False, 'error': {'code': 'VALIDATION_ERROR',
                                              'message': f'Invalid status. Choices: {list(dict(PracticeModule.STATUS_CHOICES).keys())}',
                                              'details': {}}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        module.status = new_status
        if new_status == 'completed' and not module.completed_at:
            module.completed_at = timezone.now()
        module.save(update_fields=['status', 'completed_at'])

        return Response({'success': True, 'data': PracticeModuleSerializer(module).data})

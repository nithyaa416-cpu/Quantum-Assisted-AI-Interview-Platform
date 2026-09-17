"""Views for assessments app."""
import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import CodingSubmission, Assessment, SkillGap
from .serializers import CodingSubmissionSerializer, AssessmentSerializer, SkillGapSerializer

logger = logging.getLogger(__name__)


class AssessmentDetailView(APIView):
    """GET /api/assessments/sessions/{session_id}/ — Get assessment for a session."""
    permission_classes = [IsAuthenticated]

    def get(self, request, session_id):
        try:
            assessment = Assessment.objects.get(
                session__id=session_id,
                session__student__user=request.user
            )
        except Assessment.DoesNotExist:
            return Response(
                {'success': False, 'error': {'code': 'NOT_FOUND',
                                              'message': 'Assessment not found.',
                                              'details': {}}},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response({'success': True, 'data': AssessmentSerializer(assessment).data})


class AssessmentListView(APIView):
    """GET /api/assessments/ — List all assessments for the authenticated student."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = request.user.student_profile
        assessments = Assessment.objects.filter(
            session__student=profile
        ).order_by('-generated_at')
        return Response(
            {'success': True, 'data': AssessmentSerializer(assessments, many=True).data}
        )


class SkillGapListView(APIView):
    """GET /api/assessments/skill-gaps/ — List the student's skill gaps."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = request.user.student_profile
        gaps = SkillGap.objects.filter(student=profile, resolved_at__isnull=True).order_by(
            '-gap_score'
        )
        return Response({'success': True, 'data': SkillGapSerializer(gaps, many=True).data})


class CodingSubmissionListView(APIView):
    """GET /api/assessments/coding/ — List coding submissions for the student."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = request.user.student_profile
        submissions = CodingSubmission.objects.filter(
            session__student=profile
        ).order_by('-submitted_at')
        return Response(
            {'success': True, 'data': CodingSubmissionSerializer(submissions, many=True).data}
        )

"""Views for interview session management."""
import logging
from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import InterviewSession, InterviewQuestion, StudentResponse
from .serializers import (
    InterviewSessionSerializer,
    InterviewQuestionSerializer,
    StudentResponseSerializer,
)

logger = logging.getLogger(__name__)


class InterviewSessionListCreateView(APIView):
    """
    GET  /api/sessions/  - List student's sessions
    POST /api/sessions/  - Create a new session
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = request.user.student_profile
        sessions = InterviewSession.objects.filter(student=profile).order_by('-created_at')
        return Response(
            {'success': True, 'data': InterviewSessionSerializer(sessions, many=True).data}
        )

    def post(self, request):
        profile = request.user.student_profile
        serializer = InterviewSessionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'success': False, 'error': {'code': 'VALIDATION_ERROR',
                                              'message': 'Invalid session data.',
                                              'details': serializer.errors}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        session = serializer.save(student=profile)
        logger.info('Interview session created: %s by %s', session.id, request.user.email)
        return Response(
            {'success': True, 'data': InterviewSessionSerializer(session).data},
            status=status.HTTP_201_CREATED,
        )


class InterviewSessionDetailView(APIView):
    """
    GET   /api/sessions/{id}/ - Session detail
    PATCH /api/sessions/{id}/ - Update notes/difficulty
    """
    permission_classes = [IsAuthenticated]

    def _get_session(self, pk, user):
        try:
            session = InterviewSession.objects.get(pk=pk)
            if session.student.user != user:
                return None
            return session
        except InterviewSession.DoesNotExist:
            return None

    def get(self, request, pk):
        session = self._get_session(pk, request.user)
        if not session:
            return Response(
                {'success': False, 'error': {'code': 'NOT_FOUND',
                                              'message': 'Session not found.',
                                              'details': {}}},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response({'success': True, 'data': InterviewSessionSerializer(session).data})

    def patch(self, request, pk):
        session = self._get_session(pk, request.user)
        if not session:
            return Response(
                {'success': False, 'error': {'code': 'NOT_FOUND',
                                              'message': 'Session not found.',
                                              'details': {}}},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = InterviewSessionSerializer(session, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(
                {'success': False, 'error': {'code': 'VALIDATION_ERROR',
                                              'message': 'Update failed.',
                                              'details': serializer.errors}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer.save()
        return Response({'success': True, 'data': serializer.data})


class SessionStartView(APIView):
    """POST /api/sessions/{id}/start — Move session to 'active'."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            session = InterviewSession.objects.get(pk=pk, student__user=request.user)
        except InterviewSession.DoesNotExist:
            return Response(
                {'success': False, 'error': {'code': 'NOT_FOUND',
                                              'message': 'Session not found.',
                                              'details': {}}},
                status=status.HTTP_404_NOT_FOUND,
            )
        if session.status != 'created':
            return Response(
                {'success': False, 'error': {'code': 'BAD_REQUEST',
                                              'message': f'Cannot start a session with status: {session.status}.',
                                              'details': {}}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        session.status = 'active'
        session.started_at = timezone.now()
        session.save(update_fields=['status', 'started_at'])
        return Response({'success': True, 'data': InterviewSessionSerializer(session).data})


class SessionEndView(APIView):
    """POST /api/sessions/{id}/end — Complete the session and trigger report generation."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            session = InterviewSession.objects.get(pk=pk, student__user=request.user)
        except InterviewSession.DoesNotExist:
            return Response(
                {'success': False, 'error': {'code': 'NOT_FOUND',
                                              'message': 'Session not found.',
                                              'details': {}}},
                status=status.HTTP_404_NOT_FOUND,
            )
        if session.status not in ('active', 'created'):
            return Response(
                {'success': False, 'error': {'code': 'BAD_REQUEST',
                                              'message': f'Cannot end a session with status: {session.status}.',
                                              'details': {}}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        now = timezone.now()
        session.status = 'completed'
        session.ended_at = now
        if session.started_at:
            session.duration_seconds = int((now - session.started_at).total_seconds())
        session.save(update_fields=['status', 'ended_at', 'duration_seconds'])

        logger.info('Session completed: %s', session.id)
        return Response({
            'success': True,
            'data': {
                'session': InterviewSessionSerializer(session).data,
                'message': 'Session completed. Report generation will begin shortly.',
            }
        })

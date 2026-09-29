"""
Resume views — upload, parse (sync), status, detail, edit, delete.
Parsing runs synchronously in this phase (Celery added in Phase 4).
"""
import logging
import threading
from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from .models import Resume, TargetRole
from .serializers import (
    ResumeListSerializer, ResumeDetailSerializer,
    ResumeUploadSerializer, ParsedDataUpdateSerializer,
    TargetRoleSerializer,
)
from .parser.pipeline import parse_resume_file

logger = logging.getLogger(__name__)


def _run_parse(resume_id: str) -> None:
    """
    Parse a resume in a background thread.
    Fetches the Resume, runs the pipeline, saves results.
    Thread-safe: uses its own DB connection via Django's thread-local connections.
    """
    try:
        resume = Resume.objects.get(pk=resume_id)
        resume.parse_status = 'processing'
        resume.save(update_fields=['parse_status'])

        file_path = resume.file.path
        result = parse_resume_file(file_path)

        if result['success']:
            # Store all extracted data in parsed_data JSON
            resume.parsed_data = {
                'contact':        result['contact'],
                'skills':         result['skills'],
                'education':      result['education'],
                'experience':     result['experience'],
                'projects':       result['projects'],
                'certifications': result['certifications'],
                'summary':        result['summary'],
                'raw_text':       result.get('raw_text', ''),
                'word_count':     result['word_count'],
                'parse_time_ms':  result['parse_time_ms'],
            }
            resume.is_parsed     = True
            resume.parse_status  = 'completed'
            resume.parse_error   = ''
            resume.parsed_at     = timezone.now()
        else:
            resume.parse_status = 'failed'
            resume.parse_error  = result.get('error', 'Unknown parsing error.')

        resume.save(update_fields=[
            'parsed_data', 'is_parsed', 'parse_status',
            'parse_error', 'parsed_at'
        ])

        logger.info(
            'Resume %s parsed: status=%s skills=%d projects=%d',
            resume_id, resume.parse_status,
            len(result.get('skills', [])),
            len(result.get('projects', [])),
        )

    except Resume.DoesNotExist:
        logger.error('Resume %s not found for parsing', resume_id)
    except Exception as exc:
        logger.exception('Unexpected error parsing resume %s: %s', resume_id, exc)
        try:
            Resume.objects.filter(pk=resume_id).update(
                parse_status='failed',
                parse_error=str(exc)
            )
        except Exception:
            pass


def parse_resume_now(resume: Resume) -> dict:
    """
    Synchronously extracts text and structured data from a specific resume file.
    Called on-demand when starting an interview with this resume.
    """
    if resume.is_parsed and resume.parsed_data:
        return resume.parsed_data

    file_path = resume.file.path
    result = parse_resume_file(file_path)

    if result.get('success'):
        resume.parsed_data = {
            'contact':        result.get('contact', {}),
            'skills':         result.get('skills', []),
            'education':      result.get('education', []),
            'experience':     result.get('experience', []),
            'projects':       result.get('projects', []),
            'certifications': result.get('certifications', []),
            'summary':        result.get('summary', ''),
            'raw_text':       result.get('raw_text', ''),
            'word_count':     result.get('word_count', 0),
            'parse_time_ms':  result.get('parse_time_ms', 0),
        }
        resume.is_parsed = True
        resume.parse_status = 'completed'
        resume.parse_error = ''
        resume.parsed_at = timezone.now()
    else:
        resume.parse_status = 'failed'
        resume.parse_error = result.get('error', 'Failed to extract text from resume.')

    resume.save(update_fields=['parsed_data', 'is_parsed', 'parse_status', 'parse_error', 'parsed_at'])
    return resume.parsed_data


# ── Upload ────────────────────────────────────────────────────────────────────

class ResumeUploadView(APIView):
    """
    POST /api/resumes/upload
    Upload a resume file. Stored as ready for interview selection.
    Text and skills extraction happens on-demand when starting an interview.
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        profile = request.user.student_profile

        serializer = ResumeUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'success': False, 'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Upload failed.',
                    'details': serializer.errors,
                }},
                status=status.HTTP_400_BAD_REQUEST,
            )

        file = serializer.validated_data['file']

        # Version number
        last = Resume.objects.filter(student=profile).order_by('-version').first()
        next_version = (last.version + 1) if last else 1

        resume = Resume.objects.create(
            student=profile,
            file=file,
            original_filename=file.name,
            version=next_version,
            is_active=True,
            parse_status='pending',
            parsed_data={},
        )

        logger.info('Resume uploaded (stored ready for interview): %s by %s (v%d)', resume.id, request.user.email, next_version)

        return Response(
            {'success': True, 'data': ResumeListSerializer(resume).data},
            status=status.HTTP_201_CREATED,
        )


# ── List ──────────────────────────────────────────────────────────────────────

class ResumeListView(APIView):
    """GET /api/resumes/  — list all resumes for the authenticated student."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = request.user.student_profile
        resumes = Resume.objects.filter(student=profile).order_by('-version')
        return Response(
            {'success': True, 'data': ResumeListSerializer(resumes, many=True).data}
        )


# ── Detail / Delete ───────────────────────────────────────────────────────────

class ResumeDetailView(APIView):
    """
    GET    /api/resumes/{id}/        — full detail with parsed data
    PATCH  /api/resumes/{id}/        — manually edit extracted data
    DELETE /api/resumes/{id}/        — delete resume
    """
    permission_classes = [IsAuthenticated]

    def _get_resume(self, pk, user):
        try:
            r = Resume.objects.get(pk=pk)
            return r if r.student.user == user else None
        except Resume.DoesNotExist:
            return None

    def get(self, request, pk):
        resume = self._get_resume(pk, request.user)
        if not resume:
            return Response(
                {'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'Resume not found.', 'details': {}}},
                status=status.HTTP_404_NOT_FOUND,
            )
        if not resume.is_parsed and resume.file:
            try:
                parse_resume_now(resume)
            except Exception as e:
                logger.warning('Auto parse on view failed: %s', e)
        return Response({'success': True, 'data': ResumeDetailSerializer(resume).data})

    def patch(self, request, pk):
        """Allow student to manually correct parsed data."""
        resume = self._get_resume(pk, request.user)
        if not resume:
            return Response(
                {'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'Resume not found.', 'details': {}}},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = ParsedDataUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'success': False, 'error': {'code': 'VALIDATION_ERROR', 'message': 'Invalid data.', 'details': serializer.errors}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Merge provided fields into parsed_data
        for field, value in serializer.validated_data.items():
            resume.parsed_data[field] = value

        resume.save(update_fields=['parsed_data'])
        return Response({'success': True, 'data': ResumeDetailSerializer(resume).data})

    def delete(self, request, pk):
        resume = self._get_resume(pk, request.user)
        if not resume:
            return Response(
                {'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'Resume not found.', 'details': {}}},
                status=status.HTTP_404_NOT_FOUND,
            )
        resume.file.delete(save=False)
        resume.delete()
        return Response({'success': True, 'data': {'message': 'Resume deleted.'}})


# ── Parse status ──────────────────────────────────────────────────────────────

class ResumeStatusView(APIView):
    """GET /api/resumes/{id}/status/  — poll parsing progress."""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            resume = Resume.objects.get(pk=pk, student__user=request.user)
        except Resume.DoesNotExist:
            return Response(
                {'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'Resume not found.', 'details': {}}},
                status=status.HTTP_404_NOT_FOUND,
            )
        data = {
            'id':           str(resume.id),
            'parse_status': resume.parse_status,
            'parse_error':  resume.parse_error,
            'is_parsed':    resume.is_parsed,
            'parsed_at':    resume.parsed_at,
            'skills_count': len(resume.parsed_data.get('skills', [])),
            'projects_count': len(resume.parsed_data.get('projects', [])),
        }
        return Response({'success': True, 'data': data})


# ── Re-parse ──────────────────────────────────────────────────────────────────

class ResumeReParseView(APIView):
    """POST /api/resumes/{id}/parse/  — trigger re-parsing."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            resume = Resume.objects.get(pk=pk, student__user=request.user)
        except Resume.DoesNotExist:
            return Response(
                {'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'Resume not found.', 'details': {}}},
                status=status.HTTP_404_NOT_FOUND,
            )
        if resume.parse_status == 'processing':
            return Response(
                {'success': False, 'error': {'code': 'CONFLICT', 'message': 'Resume is already being parsed.', 'details': {}}},
                status=status.HTTP_409_CONFLICT,
            )

        resume.parse_status = 'pending'
        resume.parse_error  = ''
        resume.save(update_fields=['parse_status', 'parse_error'])

        t = threading.Thread(target=_run_parse, args=(str(resume.id),), daemon=True)
        t.start()

        return Response({'success': True, 'data': {'message': 'Re-parsing started.', 'parse_status': 'pending'}})


# ── Skills extract endpoint ───────────────────────────────────────────────────

class ResumeSkillsView(APIView):
    """GET /api/resumes/{id}/skills/  — extracted skills only."""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            resume = Resume.objects.get(pk=pk, student__user=request.user)
        except Resume.DoesNotExist:
            return Response(
                {'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'Resume not found.', 'details': {}}},
                status=status.HTTP_404_NOT_FOUND,
            )
        skills = resume.parsed_data.get('skills', [])
        # Group by category
        grouped: dict[str, list] = {}
        for s in skills:
            cat = s.get('category', 'other')
            grouped.setdefault(cat, []).append(s)
        return Response({'success': True, 'data': {'skills': skills, 'grouped': grouped}})


# ── Active resume summary ──────────────────────────────────────────────────────

class ActiveResumeSummaryView(APIView):
    """GET /api/resumes/active/summary/  — summary of the active resume."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = request.user.student_profile
        resume = Resume.objects.filter(student=profile, is_active=True).first()
        if not resume:
            return Response(
                {'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'No active resume found.', 'details': {}}},
                status=status.HTTP_404_NOT_FOUND,
            )
        data = {
            'id':             str(resume.id),
            'original_filename': resume.original_filename,
            'parse_status':   resume.parse_status,
            'summary':        resume.parsed_data.get('summary', ''),
            'skills':         resume.parsed_data.get('skills', []),
            'projects_count': len(resume.parsed_data.get('projects', [])),
            'education_count': len(resume.parsed_data.get('education', [])),
            'experience_count': len(resume.parsed_data.get('experience', [])),
            'word_count':     resume.parsed_data.get('word_count', 0),
        }
        return Response({'success': True, 'data': data})


# ── TargetRole views ──────────────────────────────────────────────────────────

class TargetRoleListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = request.user.student_profile
        roles = TargetRole.objects.filter(student=profile)
        return Response({'success': True, 'data': TargetRoleSerializer(roles, many=True).data})

    def post(self, request):
        profile = request.user.student_profile
        serializer = TargetRoleSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'success': False, 'error': {'code': 'VALIDATION_ERROR', 'message': 'Invalid data.', 'details': serializer.errors}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        role = serializer.save(student=profile)
        return Response({'success': True, 'data': TargetRoleSerializer(role).data}, status=status.HTTP_201_CREATED)


class TargetRoleDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_role(self, pk, user):
        try:
            r = TargetRole.objects.get(pk=pk)
            return r if r.student.user == user else None
        except TargetRole.DoesNotExist:
            return None

    def patch(self, request, pk):
        role = self._get_role(pk, request.user)
        if not role:
            return Response({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'Target role not found.', 'details': {}}}, status=status.HTTP_404_NOT_FOUND)
        serializer = TargetRoleSerializer(role, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response({'success': False, 'error': {'code': 'VALIDATION_ERROR', 'message': 'Update failed.', 'details': serializer.errors}}, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response({'success': True, 'data': serializer.data})

    def delete(self, request, pk):
        role = self._get_role(pk, request.user)
        if not role:
            return Response({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'Target role not found.', 'details': {}}}, status=status.HTTP_404_NOT_FOUND)
        role.delete()
        return Response({'success': True, 'data': {'message': 'Target role deleted.'}})

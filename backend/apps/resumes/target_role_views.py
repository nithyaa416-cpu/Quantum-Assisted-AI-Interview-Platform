"""
Dedicated views for the Target Role module.
Mounted at /api/target-roles/ (top-level, separate from /api/resumes/).

Endpoints:
  GET  /api/target-roles/           - list student's roles
  POST /api/target-roles/           - create a role
  GET  /api/target-roles/{id}/      - detail + catalogue metadata
  PATCH /api/target-roles/{id}/     - update (rename, change domain, set primary)
  DELETE /api/target-roles/{id}/    - delete
  POST /api/target-roles/{id}/set-primary/ - make this the primary role
  GET  /api/target-roles/catalogue/ - full catalogue of supported roles
  GET  /api/target-roles/primary/   - get the primary role
  GET  /api/target-roles/skill-gap/ - required vs extracted skills comparison
"""
import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import TargetRole
from .serializers import TargetRoleSerializer
from .role_catalogue import ROLE_CATALOGUE, find_role

logger = logging.getLogger(__name__)


def _err(code: str, message: str, details: dict | None = None) -> dict:
    return {'success': False, 'error': {'code': code, 'message': message, 'details': details or {}}}


def _ok(data) -> dict:
    return {'success': True, 'data': data}


# ── Catalogue (public-ish, just needs auth) ───────────────────────────────────

class RoleCatalogueView(APIView):
    """
    GET /api/target-roles/catalogue/
    Returns the full curated list of supported roles with metadata.
    Used to populate the suggestion picker in the frontend.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        domain_filter = request.query_params.get('domain')
        search        = request.query_params.get('q', '').strip().lower()

        roles = ROLE_CATALOGUE
        if domain_filter:
            roles = [r for r in roles if r['domain'] == domain_filter]
        if search:
            roles = [
                r for r in roles
                if search in r['display_name'].lower()
                or any(search in a.lower() for a in r['aliases'])
            ]

        return Response(_ok({
            'roles': [
                {
                    'display_name':     r['display_name'],
                    'domain':           r['domain'],
                    'description':      r['description'],
                    'required_skills':  r['required_skills'],
                    'interview_topics': r['interview_topics'],
                    'coding_topics':    r['coding_topics'],
                    'aliases':          r['aliases'],
                }
                for r in roles
            ],
            'total': len(roles),
        }))


# ── List / Create ─────────────────────────────────────────────────────────────

class TargetRoleListCreateView(APIView):
    """
    GET  /api/target-roles/  — list student's target roles
    POST /api/target-roles/  — add a new target role
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = request.user.student_profile
        roles   = TargetRole.objects.filter(student=profile).order_by('-is_primary', 'role_name')
        return Response(_ok(TargetRoleSerializer(roles, many=True).data))

    def post(self, request):
        profile    = request.user.student_profile
        serializer = TargetRoleSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                _err('VALIDATION_ERROR', 'Invalid data.', serializer.errors),
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Auto-detect domain from catalogue if not supplied
        role_name = serializer.validated_data['role_name']
        catalogue_entry = find_role(role_name)
        if catalogue_entry:
            # Normalise role name to catalogue display name
            serializer.validated_data['role_name'] = catalogue_entry['display_name']
            # Auto-detect domain if not explicitly supplied
            if not request.data.get('domain'):
                serializer.validated_data['domain'] = catalogue_entry['domain']

        # If first role, auto-set primary
        is_first = not TargetRole.objects.filter(student=profile).exists()
        if is_first:
            serializer.validated_data['is_primary'] = True

        role = serializer.save(student=profile)

        # Keep student profile target_roles JSON in sync
        _sync_profile_roles(profile)

        logger.info('TargetRole created: %s for %s', role.role_name, request.user.email)
        return Response(_ok(TargetRoleSerializer(role).data), status=status.HTTP_201_CREATED)


# ── Detail / Update / Delete ──────────────────────────────────────────────────

class TargetRoleDetailView(APIView):
    """
    GET    /api/target-roles/{id}/  — detail with catalogue metadata
    PATCH  /api/target-roles/{id}/  — update
    DELETE /api/target-roles/{id}/  — delete
    """
    permission_classes = [IsAuthenticated]

    def _get_role(self, pk, user):
        try:
            r = TargetRole.objects.get(pk=pk)
            return r if r.student.user == user else None
        except TargetRole.DoesNotExist:
            return None

    def get(self, request, pk):
        role = self._get_role(pk, request.user)
        if not role:
            return Response(_err('NOT_FOUND', 'Target role not found.'), status=status.HTTP_404_NOT_FOUND)
        return Response(_ok(TargetRoleSerializer(role).data))

    def patch(self, request, pk):
        role = self._get_role(pk, request.user)
        if not role:
            return Response(_err('NOT_FOUND', 'Target role not found.'), status=status.HTTP_404_NOT_FOUND)

        serializer = TargetRoleSerializer(role, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(
                _err('VALIDATION_ERROR', 'Update failed.', serializer.errors),
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Auto-detect domain when role_name changes
        new_name = serializer.validated_data.get('role_name')
        if new_name:
            cat = find_role(new_name)
            if cat:
                serializer.validated_data['domain']    = cat['domain']
                serializer.validated_data['role_name'] = cat['display_name']

        role = serializer.save()
        _sync_profile_roles(role.student)
        return Response(_ok(TargetRoleSerializer(role).data))

    def delete(self, request, pk):
        role = self._get_role(pk, request.user)
        if not role:
            return Response(_err('NOT_FOUND', 'Target role not found.'), status=status.HTTP_404_NOT_FOUND)

        was_primary = role.is_primary
        profile     = role.student
        role.delete()

        # If we deleted the primary, promote the first remaining role
        if was_primary:
            next_role = TargetRole.objects.filter(student=profile).first()
            if next_role:
                next_role.is_primary = True
                next_role.save(update_fields=['is_primary'])

        _sync_profile_roles(profile)
        return Response(_ok({'message': 'Target role deleted.'}))


# ── Set primary ───────────────────────────────────────────────────────────────

class SetPrimaryRoleView(APIView):
    """POST /api/target-roles/{id}/set-primary/"""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            role = TargetRole.objects.get(pk=pk, student__user=request.user)
        except TargetRole.DoesNotExist:
            return Response(_err('NOT_FOUND', 'Target role not found.'), status=status.HTTP_404_NOT_FOUND)

        # Clear existing primary, set this one
        TargetRole.objects.filter(
            student=role.student, is_primary=True
        ).exclude(pk=role.pk).update(is_primary=False)

        role.is_primary = True
        role.save(update_fields=['is_primary'])
        _sync_profile_roles(role.student)

        return Response(_ok(TargetRoleSerializer(role).data))


# ── Primary role endpoint ─────────────────────────────────────────────────────

class PrimaryRoleView(APIView):
    """GET /api/target-roles/primary/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = request.user.student_profile
        role    = TargetRole.objects.filter(student=profile, is_primary=True).first()
        if not role:
            return Response(
                _err('NOT_FOUND', 'No primary target role set. Please add and set a primary role.'),
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(_ok(TargetRoleSerializer(role).data))


# ── Skill gap analysis ────────────────────────────────────────────────────────

class TargetRoleSkillGapView(APIView):
    """
    GET /api/target-roles/skill-gap/
    Compares required skills from the primary target role against
    the student's profile skills (extracted from resume).
    Returns present, missing, and gap percentage.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = request.user.student_profile

        # Allow ?role_id=... override; default to primary
        role_id = request.query_params.get('role_id')
        if role_id:
            try:
                role = TargetRole.objects.get(pk=role_id, student=profile)
            except TargetRole.DoesNotExist:
                return Response(_err('NOT_FOUND', 'Role not found.'), status=status.HTTP_404_NOT_FOUND)
        else:
            role = TargetRole.objects.filter(student=profile, is_primary=True).first()
            if not role:
                return Response(
                    _err('NOT_FOUND', 'No primary role set.'),
                    status=status.HTTP_404_NOT_FOUND,
                )

        catalogue_entry = find_role(role.role_name)
        if not catalogue_entry:
            return Response(_ok({
                'role': TargetRoleSerializer(role).data,
                'message': 'No catalogue entry found for this role.',
                'required_skills': [],
                'present_skills': [],
                'missing_skills': [],
                'gap_percentage': 0,
            }))

        required  = [s.lower() for s in catalogue_entry['required_skills']]
        student_skills_raw: list = profile.skills or []

        # Also pull from latest active resume parsed_data
        active_resume = profile.resumes.filter(is_active=True, is_parsed=True).first()
        if active_resume:
            resume_skill_names = [
                s.get('name', '').lower()
                for s in active_resume.parsed_data.get('skills', [])
            ]
            student_skills_raw = list(set(student_skills_raw) | set(resume_skill_names))

        student_lower = {s.lower() for s in student_skills_raw}

        present_skills = [s for s in catalogue_entry['required_skills']
                          if s.lower() in student_lower]
        missing_skills = [s for s in catalogue_entry['required_skills']
                          if s.lower() not in student_lower]

        gap_pct = round(len(missing_skills) / len(required) * 100, 1) if required else 0.0

        return Response(_ok({
            'role':            TargetRoleSerializer(role).data,
            'required_skills': catalogue_entry['required_skills'],
            'present_skills':  present_skills,
            'missing_skills':  missing_skills,
            'gap_percentage':  gap_pct,
            'coverage':        round(len(present_skills) / len(required) * 100, 1) if required else 0.0,
            'interview_topics': catalogue_entry['interview_topics'],
            'coding_topics':    catalogue_entry['coding_topics'],
        }))


# ── Helper ────────────────────────────────────────────────────────────────────

def _sync_profile_roles(profile) -> None:
    """Keep StudentProfile.target_roles JSON in sync with TargetRole records."""
    role_names = list(
        TargetRole.objects.filter(student=profile).values_list('role_name', flat=True)
    )
    profile.target_roles = role_names
    profile.save(update_fields=['target_roles'])

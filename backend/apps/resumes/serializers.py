"""Serializers for Resume and TargetRole."""
from rest_framework import serializers
from .models import Resume, TargetRole


class ResumeListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views — excludes heavy parsed_data."""
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    skills_count = serializers.SerializerMethodField()

    class Meta:
        model = Resume
        fields = [
            'id', 'student_name', 'original_filename', 'parse_status',
            'is_parsed', 'parsed_at', 'version', 'is_active',
            'skills_count', 'created_at',
        ]
        read_only_fields = fields

    def get_skills_count(self, obj) -> int:
        return len(obj.parsed_data.get('skills', []))


class ResumeDetailSerializer(serializers.ModelSerializer):
    """Full serializer including all parsed_data fields."""
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    skills       = serializers.SerializerMethodField()
    projects     = serializers.SerializerMethodField()
    education    = serializers.SerializerMethodField()
    experience   = serializers.SerializerMethodField()
    certifications = serializers.SerializerMethodField()
    summary      = serializers.SerializerMethodField()
    contact      = serializers.SerializerMethodField()

    class Meta:
        model = Resume
        fields = [
            'id', 'student_name', 'original_filename', 'parse_status', 'parse_error',
            'is_parsed', 'parsed_at', 'version', 'is_active', 'created_at',
            'contact', 'skills', 'projects', 'education', 'experience',
            'certifications', 'summary',
        ]
        read_only_fields = fields

    def get_skills(self, obj):        return obj.parsed_data.get('skills', [])
    def get_projects(self, obj):      return obj.parsed_data.get('projects', [])
    def get_education(self, obj):     return obj.parsed_data.get('education', [])
    def get_experience(self, obj):    return obj.parsed_data.get('experience', [])
    def get_certifications(self, obj): return obj.parsed_data.get('certifications', [])
    def get_summary(self, obj):       return obj.parsed_data.get('summary', '')
    def get_contact(self, obj):       return obj.parsed_data.get('contact', {})


class ResumeUploadSerializer(serializers.Serializer):
    """Validates the uploaded file before creating a Resume record."""
    file = serializers.FileField()

    ALLOWED_CONTENT_TYPES = [
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    ]
    MAX_SIZE_BYTES = 10 * 1024 * 1024   # 10 MB

    def validate_file(self, value):
        ct = getattr(value, 'content_type', '')
        if ct and ct not in self.ALLOWED_CONTENT_TYPES:
            raise serializers.ValidationError('Only PDF files are accepted.')
        if value.size > self.MAX_SIZE_BYTES:
            raise serializers.ValidationError('File size must be under 10 MB.')
        # Extension check
        name = value.name.lower()
        if not (name.endswith('.pdf') or name.endswith('.docx')):
            raise serializers.ValidationError('Only .pdf files are accepted.')
        return value


class ParsedDataUpdateSerializer(serializers.Serializer):
    """
    Allows students to manually correct extracted information.
    All fields are optional — only provided fields are updated.
    """
    skills = serializers.ListField(
        child=serializers.DictField(), required=False
    )
    projects = serializers.ListField(
        child=serializers.DictField(), required=False
    )
    education = serializers.ListField(
        child=serializers.DictField(), required=False
    )
    experience = serializers.ListField(
        child=serializers.DictField(), required=False
    )
    certifications = serializers.ListField(
        child=serializers.DictField(), required=False
    )
    summary = serializers.CharField(required=False, allow_blank=True, max_length=2000)

    def validate_skills(self, value):
        for s in value:
            if 'name' not in s:
                raise serializers.ValidationError("Each skill must have a 'name' field.")
        return value

    def validate_projects(self, value):
        for p in value:
            if 'title' not in p:
                raise serializers.ValidationError("Each project must have a 'title' field.")
        return value


class TargetRoleSerializer(serializers.ModelSerializer):
    required_skills  = serializers.SerializerMethodField()
    interview_topics = serializers.SerializerMethodField()
    coding_topics    = serializers.SerializerMethodField()
    role_description = serializers.SerializerMethodField()

    class Meta:
        model = TargetRole
        fields = [
            'id', 'role_name', 'domain', 'is_primary', 'created_at',
            'required_skills', 'interview_topics', 'coding_topics', 'role_description',
        ]
        read_only_fields = ['id', 'created_at',
                            'required_skills', 'interview_topics',
                            'coding_topics', 'role_description']

    def _get_catalogue(self, obj):
        from .role_catalogue import find_role
        return find_role(obj.role_name)

    def get_required_skills(self, obj):
        role = self._get_catalogue(obj)
        return role['required_skills'] if role else []

    def get_interview_topics(self, obj):
        role = self._get_catalogue(obj)
        return role['interview_topics'] if role else []

    def get_coding_topics(self, obj):
        role = self._get_catalogue(obj)
        return role['coding_topics'] if role else []

    def get_role_description(self, obj):
        role = self._get_catalogue(obj)
        return role['description'] if role else ''

    def validate_role_name(self, value):
        v = value.strip()
        if len(v) < 2:
            raise serializers.ValidationError('Role name must be at least 2 characters.')
        if len(v) > 255:
            raise serializers.ValidationError('Role name is too long.')
        return v

"""
Resume and TargetRole models.
"""
import uuid
from django.db import models
from apps.accounts.models import StudentProfile


class Resume(models.Model):
    """
    A student's uploaded resume file.
    Supports versioning — only one resume is active at a time.
    AI-parsed data is stored in parsed_data JSON.
    """
    PARSE_STATUS_CHOICES = [
        ('pending',    'Pending'),
        ('processing', 'Processing'),
        ('completed',  'Completed'),
        ('failed',     'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(
        StudentProfile, on_delete=models.CASCADE, related_name='resumes'
    )
    file = models.FileField(upload_to='resumes/%Y/%m/')
    original_filename = models.CharField(max_length=255)

    # Parsing state
    parse_status = models.CharField(
        max_length=20, choices=PARSE_STATUS_CHOICES, default='pending'
    )
    parse_error = models.TextField(blank=True)

    # Extracted structured data
    parsed_data = models.JSONField(default=dict, blank=True)
    is_parsed = models.BooleanField(default=False)
    parsed_at = models.DateTimeField(null=True, blank=True)

    # Versioning
    version = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'resumes_resume'
        verbose_name = 'Resume'
        verbose_name_plural = 'Resumes'
        ordering = ['-version']
        indexes = [
            models.Index(fields=['student', 'is_active']),
            models.Index(fields=['student', 'version']),
            models.Index(fields=['student', 'parse_status']),
        ]

    def __str__(self):
        return f'Resume v{self.version} [{self.parse_status}] — {self.student.full_name}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    @property
    def skills(self) -> list:
        return self.parsed_data.get('skills', [])

    @property
    def projects(self) -> list:
        return self.parsed_data.get('projects', [])

    @property
    def education(self) -> list:
        return self.parsed_data.get('education', [])

    @property
    def experience(self) -> list:
        return self.parsed_data.get('experience', [])

    @property
    def summary(self) -> str:
        return self.parsed_data.get('summary', '')


class TargetRole(models.Model):
    """A specific job role a student is targeting."""
    DOMAIN_CHOICES = [
        ('software_engineering', 'Software Engineering'),
        ('data_science', 'Data Science'),
        ('machine_learning', 'Machine Learning'),
        ('devops', 'DevOps / Cloud'),
        ('frontend', 'Frontend Development'),
        ('backend', 'Backend Development'),
        ('fullstack', 'Full Stack Development'),
        ('mobile', 'Mobile Development'),
        ('cybersecurity', 'Cybersecurity'),
        ('product_management', 'Product Management'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(
        StudentProfile, on_delete=models.CASCADE, related_name='target_roles_list'
    )
    role_name = models.CharField(max_length=255)
    domain = models.CharField(max_length=100, choices=DOMAIN_CHOICES, default='other')
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'resumes_target_role'
        verbose_name = 'Target Role'
        verbose_name_plural = 'Target Roles'
        ordering = ['-is_primary', 'role_name']
        constraints = [
            models.UniqueConstraint(
                fields=['student'],
                condition=models.Q(is_primary=True),
                name='unique_primary_target_role_per_student'
            )
        ]
        indexes = [models.Index(fields=['student', 'is_primary'])]

    def __str__(self):
        tag = ' [Primary]' if self.is_primary else ''
        return f'{self.role_name}{tag} — {self.student.full_name}'

    def save(self, *args, **kwargs):
        if self.is_primary:
            TargetRole.objects.filter(
                student=self.student, is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)

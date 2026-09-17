"""
Preparation models: PreparationPlan, PracticeModule.

PreparationPlan is the QAOA-generated personalised study roadmap.
PracticeModule is one time-block within the plan (one topic, one day).

Both are scoped to the individual student — no ranking or comparison.
"""
import uuid
from django.db import models
from apps.accounts.models import StudentProfile
from apps.resumes.models import TargetRole


class PreparationPlan(models.Model):
    """
    A quantum-optimised (QAOA) study plan generated for a student.
    Contains topic weights, recommended sequence, and QAOA metadata.
    Only one plan is active per student at a time.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='preparation_plans'
    )
    target_role = models.ForeignKey(
        TargetRole,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='preparation_plans'
    )
    preparation_days = models.IntegerField(default=30)
    # QAOA output: topic → priority weight (0.0–1.0)
    # e.g. {"Data Structures": 0.9, "System Design": 0.7, "SQL": 0.5}
    topic_weights = models.JSONField(default=dict, blank=True)
    # Ordered list of {topic, day, hours, sub_topics, practice_question_types}
    recommended_sequence = models.JSONField(default=list, blank=True)
    # QAOA objective energy value (lower = better optimisation)
    qaoa_energy = models.FloatField(null=True, blank=True)
    # QAOA circuit depth used
    circuit_depth = models.IntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'preparation_plan'
        verbose_name = 'Preparation Plan'
        verbose_name_plural = 'Preparation Plans'
        ordering = ['-generated_at']
        indexes = [
            models.Index(fields=['student', 'is_active']),
            models.Index(fields=['student', 'generated_at']),
        ]

    def __str__(self):
        role = self.target_role.role_name if self.target_role else 'General'
        return f'Plan for {self.student.full_name} — {role} ({self.preparation_days} days)'

    def save(self, *args, **kwargs):
        # Deactivate other plans for this student when a new active plan is saved
        if self.is_active and not self.pk:
            PreparationPlan.objects.filter(
                student=self.student, is_active=True
            ).update(is_active=False)
        super().save(*args, **kwargs)


class PracticeModule(models.Model):
    """
    One study block within a PreparationPlan.
    Represents a specific topic the student should study on a given day.
    Tracks completion status individually.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('skipped', 'Skipped'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plan = models.ForeignKey(
        PreparationPlan,
        on_delete=models.CASCADE,
        related_name='practice_modules'
    )
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='practice_modules'
    )
    topic = models.CharField(max_length=255)
    sub_topics = models.JSONField(default=list, blank=True)
    scheduled_day = models.PositiveIntegerField()
    estimated_hours = models.DecimalField(max_digits=4, decimal_places=1, default=2.0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    completed_at = models.DateTimeField(null=True, blank=True)
    # Curated learning resources: [{title, url, type}]
    resources = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'preparation_practice_module'
        verbose_name = 'Practice Module'
        verbose_name_plural = 'Practice Modules'
        ordering = ['scheduled_day', 'topic']
        indexes = [
            models.Index(fields=['plan', 'scheduled_day']),
            models.Index(fields=['student', 'status']),
        ]

    def __str__(self):
        return f'Day {self.scheduled_day}: {self.topic} [{self.status}]'

    @property
    def is_completed(self):
        return self.status == 'completed'

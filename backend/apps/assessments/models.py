"""
Assessment models: CodingSubmission, Assessment, SkillGap.

All scores are individual — no cross-student comparisons exist here.
"""
import uuid
from django.db import models
from apps.accounts.models import StudentProfile
from apps.sessions.models import InterviewSession


class CodingSubmission(models.Model):
    """
    A student's code submission during the coding phase of an interview.
    Stores the problem, code written, execution results, and AI scoring.
    """
    LANGUAGE_CHOICES = [
        ('python', 'Python 3'),
        ('javascript', 'JavaScript (Node.js)'),
        ('java', 'Java'),
        ('cpp', 'C++'),
        ('go', 'Go'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(
        InterviewSession,
        on_delete=models.CASCADE,
        related_name='coding_submissions'
    )
    problem_title = models.CharField(max_length=255)
    problem_statement = models.TextField()
    language = models.CharField(max_length=20, choices=LANGUAGE_CHOICES, default='python')
    code = models.TextField()
    execution_output = models.TextField(blank=True)
    stderr = models.TextField(blank=True)
    # List of {test_id, input, expected_output, actual_output, passed}
    test_results = models.JSONField(default=list, blank=True)
    passed_count = models.IntegerField(default=0)
    total_count = models.IntegerField(default=0)
    runtime_ms = models.IntegerField(null=True, blank=True)
    memory_kb = models.IntegerField(null=True, blank=True)
    timed_out = models.BooleanField(default=False)
    # Individual scores 0.00–1.00
    correctness_score = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    efficiency_score = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    quality_score = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    overall_score = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    llm_review = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'assessments_coding_submission'
        verbose_name = 'Coding Submission'
        verbose_name_plural = 'Coding Submissions'
        ordering = ['-submitted_at']
        indexes = [
            models.Index(fields=['session']),
        ]

    def __str__(self):
        score = f'{self.overall_score:.2f}' if self.overall_score is not None else 'unscored'
        return f'{self.problem_title} [{self.language}] — Score: {score}'

    @property
    def pass_rate(self):
        if self.total_count == 0:
            return 0.0
        return self.passed_count / self.total_count


class Assessment(models.Model):
    """
    The final post-interview assessment report for a completed session.
    Aggregates scores from all dimensions: technical, communication,
    behavioural, coding, and problem-solving.

    This is strictly individual — it is NEVER used to compare students.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.OneToOneField(
        InterviewSession,
        on_delete=models.CASCADE,
        related_name='assessment'
    )
    # Aggregate scores (0.00–1.00 per dimension)
    overall_score = models.DecimalField(max_digits=4, decimal_places=2)
    technical_score = models.DecimalField(max_digits=4, decimal_places=2)
    communication_score = models.DecimalField(max_digits=4, decimal_places=2)
    behavioural_score = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    coding_score = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    problem_solving_score = models.DecimalField(max_digits=4, decimal_places=2)
    # Narrative feedback stored as structured JSON
    strengths = models.JSONField(default=list)          # ["Clear explanation of OOP", ...]
    improvement_areas = models.JSONField(default=list)  # [{"area": "...", "priority": "high"}]
    detailed_feedback = models.JSONField(default=dict)  # Per-dimension narrative text
    # Raw metrics stored for reference
    speech_metrics = models.JSONField(default=dict)
    behavioural_metrics = models.JSONField(default=dict)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'assessments_assessment'
        verbose_name = 'Assessment'
        verbose_name_plural = 'Assessments'
        ordering = ['-generated_at']
        indexes = [
            models.Index(fields=['session']),
        ]

    def __str__(self):
        return f'Assessment for Session {self.session_id} — Overall: {self.overall_score}'


class SkillGap(models.Model):
    """
    An individual skill gap identified for a student from their assessment.
    Tracks current proficiency vs target level for a specific skill.
    Used to feed the QAOA preparation optimiser.

    Scoped entirely to the individual student — no comparisons.
    """
    CATEGORY_CHOICES = [
        ('language', 'Programming Language'),
        ('framework', 'Framework / Library'),
        ('concept', 'CS Concept'),
        ('tool', 'Tool / Platform'),
        ('soft_skill', 'Soft Skill'),
    ]
    PRIORITY_CHOICES = [
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='skill_gaps'
    )
    assessment = models.ForeignKey(
        Assessment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='skill_gaps'
    )
    skill_name = models.CharField(max_length=255)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='concept')
    # 0.00 = no knowledge, 1.00 = expert
    current_level = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    target_level = models.DecimalField(max_digits=3, decimal_places=2, default=1.00)
    # gap_score = target_level - current_level (computed on save)
    gap_score = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    identified_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'assessments_skill_gap'
        verbose_name = 'Skill Gap'
        verbose_name_plural = 'Skill Gaps'
        ordering = ['-gap_score', 'skill_name']
        indexes = [
            models.Index(fields=['student', 'priority']),
            models.Index(fields=['student', 'resolved_at']),
        ]

    def __str__(self):
        return (
            f'{self.skill_name} [{self.category}] — '
            f'Gap: {self.gap_score:.2f} ({self.priority} priority)'
        )

    def save(self, *args, **kwargs):
        # Auto-compute gap score
        self.gap_score = max(float(self.target_level) - float(self.current_level), 0.0)
        # Auto-set priority based on gap magnitude
        if self.gap_score >= 0.6:
            self.priority = 'high'
        elif self.gap_score >= 0.3:
            self.priority = 'medium'
        else:
            self.priority = 'low'
        super().save(*args, **kwargs)

    @property
    def is_resolved(self):
        return self.resolved_at is not None

"""
Interview session models: InterviewSession, InterviewQuestion, StudentResponse.

Every session is owned by a single student and evaluated independently.
No cross-student references exist in this module.
"""
import uuid
from django.db import models
from apps.accounts.models import StudentProfile
from apps.resumes.models import TargetRole


class InterviewSession(models.Model):
    """
    One complete interview attempt by a student.
    Tracks session type, phases, timing, and links to quantum prep plan.
    """
    SESSION_TYPE_CHOICES = [
        ('technical', 'Technical'),
        ('hr', 'HR'),
        ('project', 'Project-Based'),
        ('coding', 'Coding'),
        ('mixed', 'Mixed (All Rounds)'),
    ]
    STATUS_CHOICES = [
        ('created', 'Created'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('aborted', 'Aborted'),
    ]
    DIFFICULTY_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='sessions'
    )
    target_role = models.ForeignKey(
        TargetRole,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sessions'
    )
    # Circular FK to PreparationPlan — declared as string to avoid circular imports
    quantum_plan = models.ForeignKey(
        'preparation.PreparationPlan',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sessions'
    )
    session_type = models.CharField(max_length=20, choices=SESSION_TYPE_CHOICES, default='mixed')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='created')
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='intermediate')
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.IntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'sessions_interview_session'
        verbose_name = 'Interview Session'
        verbose_name_plural = 'Interview Sessions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['student', 'status']),
            models.Index(fields=['student', 'created_at']),
        ]

    def __str__(self):
        return f'{self.session_type.title()} Session [{self.status}] — {self.student.full_name}'

    @property
    def is_active(self):
        return self.status == 'active'

    @property
    def is_completed(self):
        return self.status == 'completed'


class InterviewQuestion(models.Model):
    """
    A single AI-generated question within an interview session.
    Tracks which phase and topic it belongs to, and the expected concepts.
    """
    PHASE_CHOICES = [
        ('warmup', 'Warm-Up'),
        ('technical', 'Technical'),
        ('coding', 'Coding'),
        ('hr', 'HR / Behavioural'),
        ('project', 'Project-Based'),
        ('closing', 'Closing'),
    ]
    QUESTION_TYPE_CHOICES = [
        ('conceptual', 'Conceptual'),
        ('behavioral', 'Behavioural (STAR)'),
        ('coding', 'Coding Problem'),
        ('project', 'Project Discussion'),
        ('situational', 'Situational'),
    ]
    DIFFICULTY_LEVEL_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(
        InterviewSession,
        on_delete=models.CASCADE,
        related_name='questions'
    )
    turn_number = models.PositiveIntegerField()
    phase = models.CharField(max_length=20, choices=PHASE_CHOICES, default='technical')
    question_text = models.TextField()
    question_type = models.CharField(
        max_length=20, choices=QUESTION_TYPE_CHOICES, default='conceptual'
    )
    topic = models.CharField(max_length=255, blank=True)
    difficulty_level = models.CharField(
        max_length=10, choices=DIFFICULTY_LEVEL_CHOICES, default='medium'
    )
    # List of concept strings the AI expects a good answer to cover
    expected_concepts = models.JSONField(default=list, blank=True)
    ai_generated = models.BooleanField(default=True)
    is_follow_up = models.BooleanField(default=False)
    follow_up_reason = models.CharField(max_length=50, blank=True)   # 'weak_answer' | 'strong_answer'
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'sessions_interview_question'
        verbose_name = 'Interview Question'
        verbose_name_plural = 'Interview Questions'
        ordering = ['turn_number']
        unique_together = [('session', 'turn_number')]
        indexes = [
            models.Index(fields=['session', 'turn_number']),
            models.Index(fields=['session', 'phase']),
        ]

    def __str__(self):
        return f'Q{self.turn_number} [{self.phase}] — Session {self.session_id}'


class StudentResponse(models.Model):
    """
    The student's response to a specific interview question.
    Contains transcript, optional audio file, AI scoring, and feedback.
    Score is 0.00–1.00 (individual, never compared across students).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.OneToOneField(
        InterviewQuestion,
        on_delete=models.CASCADE,
        related_name='response'
    )
    session = models.ForeignKey(
        InterviewSession,
        on_delete=models.CASCADE,
        related_name='responses'
    )
    transcript = models.TextField(blank=True)
    audio_file = models.FileField(
        upload_to='responses/audio/%Y/%m/', null=True, blank=True
    )
    response_duration_seconds = models.IntegerField(null=True, blank=True)
    # Concepts the student actually mentioned, extracted by NLP
    concepts_covered = models.JSONField(default=list, blank=True)
    # Individual score 0.00–1.00 — no cross-student comparison
    score = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    ai_feedback = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'sessions_student_response'
        verbose_name = 'Student Response'
        verbose_name_plural = 'Student Responses'
        ordering = ['question__turn_number']
        indexes = [
            models.Index(fields=['session']),
        ]

    def __str__(self):
        score_str = f'{self.score:.2f}' if self.score is not None else 'unscored'
        return f'Response to Q{self.question.turn_number} — Score: {score_str}'

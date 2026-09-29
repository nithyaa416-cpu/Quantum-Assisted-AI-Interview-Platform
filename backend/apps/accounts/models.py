"""
Accounts models: CustomUser, CustomUserManager, StudentProfile.

Design principles:
- CustomUser uses email as the login field (not username).
- StudentProfile is auto-created on user save via post_save signal.
- No cross-student data — all fields are individual.
"""
import uuid
import logging
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


class CustomUserManager(BaseUserManager):
    """Manager for CustomUser using email as the unique identifier."""

    def create_user(self, email: str, password: str, **extra_fields):
        if not email:
            raise ValueError('Email address is required.')
        email = self.normalize_email(email)
        extra_fields.setdefault('is_active', True)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)  # bcrypt via Django's password hasher
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if not extra_fields.get('is_staff'):
            raise ValueError('Superuser must have is_staff=True.')
        if not extra_fields.get('is_superuser'):
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model using email + password authentication.
    No username field — email is the login identifier.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)
    full_name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']

    class Meta:
        db_table = 'accounts_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']

    def __str__(self):
        return f'{self.full_name} <{self.email}>'

    def get_full_name(self):
        return self.full_name

    def get_short_name(self):
        return self.full_name.split()[0] if self.full_name else self.email


class StudentProfile(models.Model):
    """
    Extended profile for each student.
    Auto-created when a CustomUser is registered.
    Stores personal details, skills, and preferences.
    All data is scoped to this individual student.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='student_profile'
    )
    college = models.CharField(max_length=255, blank=True)
    graduation_year = models.IntegerField(null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    bio = models.TextField(blank=True)
    # Skills stored as a JSON list of strings, e.g. ["Python", "Django", "SQL"]
    skills = models.JSONField(default=list, blank=True)
    # Target roles stored as a JSON list, e.g. ["Software Engineer", "Backend Developer"]
    target_roles = models.JSONField(default=list, blank=True)
    linkedin_url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'accounts_student_profile'
        verbose_name = 'Student Profile'
        verbose_name_plural = 'Student Profiles'
        ordering = ['-created_at']

    def __str__(self):
        return f'Profile: {self.user.full_name}'

    @property
    def email(self):
        return self.user.email

    @property
    def full_name(self):
        return self.user.full_name


# ---------------------------------------------------------------------------
# Signal: auto-create StudentProfile when a CustomUser is created
# ---------------------------------------------------------------------------
@receiver(post_save, sender=CustomUser)
def create_student_profile(sender, instance, created, **kwargs):
    """Create a StudentProfile whenever a new CustomUser is saved."""
    if created:
        StudentProfile.objects.create(user=instance)
        logger.info('StudentProfile created for user: %s', instance.email)


class EmailVerificationOTP(models.Model):
    """
    Stores 6-digit OTP codes for email verification during registration.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(db_index=True)
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
    attempts = models.IntegerField(default=0)

    class Meta:
        db_table = 'accounts_email_otp'
        verbose_name = 'Email Verification OTP'
        verbose_name_plural = 'Email Verification OTPs'
        ordering = ['-created_at']

    def __str__(self):
        return f'OTP for {self.email}'

    def is_expired(self, expiry_minutes: int = 10) -> bool:
        from django.utils import timezone
        from datetime import timedelta
        return timezone.now() > self.created_at + timedelta(minutes=expiry_minutes)

    def can_resend(self, cooldown_seconds: int = 60) -> bool:
        from django.utils import timezone
        from datetime import timedelta
        return timezone.now() >= self.created_at + timedelta(seconds=cooldown_seconds)


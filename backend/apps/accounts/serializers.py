"""
Serializers for accounts app:
- RegisterSerializer
- LoginSerializer
- UserSerializer
- StudentProfileSerializer
"""
import re
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import StudentProfile

User = get_user_model()


class RegisterSerializer(serializers.Serializer):
    """Validates registration input and creates User + auto-linked StudentProfile."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, min_length=8)
    full_name = serializers.CharField(max_length=255)

    def validate_email(self, value: str) -> str:
        email = value.lower().strip()
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return email

    def validate_password(self, value: str) -> str:
        # Must contain at least one digit
        if not re.search(r'\d', value):
            raise serializers.ValidationError(
                'Password must contain at least one number.'
            )
        # Run Django's built-in validators (length, common, numeric-only)
        try:
            validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages))
        return value

    def validate(self, attrs: dict) -> dict:
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError(
                {'confirm_password': 'Passwords do not match.'}
            )
        return attrs

    def create(self, validated_data: dict):
        validated_data.pop('confirm_password')
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            full_name=validated_data['full_name'],
        )
        return user


class LoginSerializer(serializers.Serializer):
    """Validates login credentials and returns the authenticated user."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs: dict) -> dict:
        email = attrs.get('email', '').lower().strip()
        password = attrs.get('password', '')

        user = authenticate(request=self.context.get('request'), email=email, password=password)
        if not user:
            raise serializers.ValidationError(
                {'non_field_errors': 'Invalid email or password.'}
            )
        if not user.is_active:
            raise serializers.ValidationError(
                {'non_field_errors': 'This account has been deactivated.'}
            )
        attrs['user'] = user
        return attrs


class UserSerializer(serializers.ModelSerializer):
    """Read-only serializer for CustomUser — never exposes password."""

    class Meta:
        model = User
        fields = ['id', 'email', 'full_name', 'is_active', 'date_joined']
        read_only_fields = fields


class StudentProfileSerializer(serializers.ModelSerializer):
    """
    Full profile serializer.
    On reads: includes nested user info.
    On writes: only accepts profile-level fields (not user fields).
    """
    email = serializers.EmailField(source='user.email', read_only=True)
    full_name = serializers.CharField(source='user.full_name', read_only=True)

    class Meta:
        model = StudentProfile
        fields = [
            'id',
            'email',
            'full_name',
            'college',
            'graduation_year',
            'phone',
            'bio',
            'skills',
            'target_roles',
            'linkedin_url',
            'github_url',
            'avatar',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'email', 'full_name', 'created_at', 'updated_at']

    def validate_graduation_year(self, value):
        if value is not None and (value < 1990 or value > 2100):
            raise serializers.ValidationError('Graduation year must be between 1990 and 2100.')
        return value

    def validate_skills(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError('Skills must be a list of strings.')
        cleaned = [str(s).strip() for s in value if str(s).strip()]
        return cleaned

    def validate_target_roles(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError('Target roles must be a list of strings.')
        cleaned = [str(r).strip() for r in value if str(r).strip()]
        return cleaned


class TokenPairSerializer(serializers.Serializer):
    """Response serializer for access + refresh token pair."""
    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)


class AuthResponseSerializer(serializers.Serializer):
    """Combined auth response: user data + token pair."""
    user = UserSerializer(read_only=True)
    tokens = TokenPairSerializer(read_only=True)


def get_tokens_for_user(user) -> dict:
    """Generate a JWT access + refresh token pair for a user."""
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

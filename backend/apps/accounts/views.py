"""
Authentication and profile views.

Endpoints:
  POST /api/auth/register      - Register + get tokens
  POST /api/auth/login         - Login + get tokens
  POST /api/auth/logout        - Blacklist refresh token
  POST /api/auth/refresh       - Get new access token
  GET  /api/auth/me            - Current user (protected)
  GET  /api/profile/me         - Student profile (protected)
  PATCH/PUT /api/profile/me    - Update profile (protected)
"""
import logging
from django.db import transaction
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken

from django.contrib.auth import get_user_model
from django.core.validators import validate_email
from django.core.exceptions import ValidationError as DjangoValidationError

from .models import StudentProfile
from .otp_service import send_otp_email
from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    UserSerializer,
    StudentProfileSerializer,
    get_tokens_for_user,
)

User = get_user_model()
logger = logging.getLogger(__name__)


class SendOTPView(APIView):
    """
    POST /api/auth/send-otp
    Sends a 6-digit verification code to the specified email for registration.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email', '').strip().lower()

        if not email:
            return Response(
                {
                    'success': False,
                    'error': {
                        'code': 'VALIDATION_ERROR',
                        'message': 'Email address is required.',
                        'details': {'email': ['Email address is required.']},
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            validate_email(email)
        except DjangoValidationError:
            return Response(
                {
                    'success': False,
                    'error': {
                        'code': 'VALIDATION_ERROR',
                        'message': 'Enter a valid email address.',
                        'details': {'email': ['Enter a valid email address.']},
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if User.objects.filter(email=email).exists():
            return Response(
                {
                    'success': False,
                    'error': {
                        'code': 'EMAIL_EXISTS',
                        'message': 'An account with this email already exists.',
                        'details': {'email': ['An account with this email already exists.']},
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        success, message = send_otp_email(email)
        if not success:
            return Response(
                {
                    'success': False,
                    'error': {
                        'code': 'SEND_OTP_FAILED',
                        'message': message,
                        'details': {},
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                'success': True,
                'data': {'message': message},
            },
            status=status.HTTP_200_OK,
        )


class RegisterView(APIView):
    """
    POST /api/auth/register
    Open endpoint. Creates a user + student profile and returns JWT tokens.
    """

    permission_classes = [AllowAny]

    @transaction.atomic
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'success': False, 'error': {'code': 'VALIDATION_ERROR',
                                              'message': 'Registration failed.',
                                              'details': serializer.errors}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = serializer.save()
        tokens = get_tokens_for_user(user)

        logger.info('New user registered: %s', user.email)

        return Response(
            {
                'success': True,
                'data': {
                    'user': UserSerializer(user).data,
                    'tokens': tokens,
                }
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """
    POST /api/auth/login
    Open endpoint. Validates credentials and returns JWT tokens.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(
                {'success': False, 'error': {'code': 'AUTH_FAILED',
                                              'message': 'Invalid email or password.',
                                              'details': serializer.errors}},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        user = serializer.validated_data['user']
        tokens = get_tokens_for_user(user)

        logger.info('User logged in: %s', user.email)

        return Response(
            {
                'success': True,
                'data': {
                    'user': UserSerializer(user).data,
                    'tokens': tokens,
                }
            },
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    """
    POST /api/auth/logout
    Protected. Blacklists the provided refresh token so it cannot be reused.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response(
                {'success': False, 'error': {'code': 'BAD_REQUEST',
                                              'message': 'Refresh token is required.',
                                              'details': {}}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError as exc:
            return Response(
                {'success': False, 'error': {'code': 'INVALID_TOKEN',
                                              'message': str(exc),
                                              'details': {}}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        logger.info('User logged out: %s', request.user.email)
        return Response({'success': True, 'data': {'message': 'Logged out successfully.'}},
                        status=status.HTTP_200_OK)


class TokenRefreshView(APIView):
    """
    POST /api/auth/refresh
    Open endpoint. Exchanges a valid refresh token for a new access token.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response(
                {'success': False, 'error': {'code': 'BAD_REQUEST',
                                              'message': 'Refresh token is required.',
                                              'details': {}}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token = RefreshToken(refresh_token)
            new_access = str(token.access_token)
            # If ROTATE_REFRESH_TOKENS is True, also return new refresh
            new_refresh = str(token) if hasattr(token, 'blacklist') else refresh_token
        except (TokenError, InvalidToken) as exc:
            return Response(
                {'success': False, 'error': {'code': 'INVALID_TOKEN',
                                              'message': str(exc),
                                              'details': {}}},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        return Response(
            {'success': True, 'data': {'access': new_access, 'refresh': new_refresh}},
            status=status.HTTP_200_OK,
        )


class CurrentUserView(APIView):
    """
    GET /api/auth/me
    Protected. Returns the authenticated user's basic data.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            {'success': True, 'data': UserSerializer(request.user).data},
            status=status.HTTP_200_OK,
        )


class StudentProfileView(APIView):
    """
    GET  /api/profile/me  - Retrieve student profile
    PUT  /api/profile/me  - Full update (all fields)
    PATCH /api/profile/me - Partial update (subset of fields)
    """
    permission_classes = [IsAuthenticated]

    def _get_profile(self, user):
        try:
            return user.student_profile
        except StudentProfile.DoesNotExist:
            # Auto-heal: create profile if missing (edge case)
            return StudentProfile.objects.create(user=user)

    def get(self, request):
        profile = self._get_profile(request.user)
        return Response(
            {'success': True, 'data': StudentProfileSerializer(profile).data},
            status=status.HTTP_200_OK,
        )

    def put(self, request):
        profile = self._get_profile(request.user)
        serializer = StudentProfileSerializer(profile, data=request.data)
        if not serializer.is_valid():
            return Response(
                {'success': False, 'error': {'code': 'VALIDATION_ERROR',
                                              'message': 'Profile update failed.',
                                              'details': serializer.errors}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer.save()
        return Response({'success': True, 'data': serializer.data}, status=status.HTTP_200_OK)

    def patch(self, request):
        profile = self._get_profile(request.user)
        serializer = StudentProfileSerializer(profile, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(
                {'success': False, 'error': {'code': 'VALIDATION_ERROR',
                                              'message': 'Profile update failed.',
                                              'details': serializer.errors}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer.save()
        return Response({'success': True, 'data': serializer.data}, status=status.HTTP_200_OK)

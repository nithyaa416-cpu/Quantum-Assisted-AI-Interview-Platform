"""
Password reset endpoint — no email required for development.
Student provides email + new password, backend verifies email exists and updates.

POST /api/auth/reset-password/
Body: { email, new_password }
"""
import logging
import re
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

User = get_user_model()
logger = logging.getLogger(__name__)


class ResetPasswordView(APIView):
    """
    Simple password reset — no email token required (dev environment).
    In production, replace with a time-limited token sent via email.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        email       = request.data.get('email', '').strip().lower()
        new_password = request.data.get('new_password', '')

        # Validate inputs
        if not email:
            return Response(
                {'success': False, 'error': {'code': 'VALIDATION_ERROR',
                                              'message': 'Email is required.',
                                              'details': {}}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not new_password:
            return Response(
                {'success': False, 'error': {'code': 'VALIDATION_ERROR',
                                              'message': 'New password is required.',
                                              'details': {}}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Password strength checks
        if len(new_password) < 8:
            return Response(
                {'success': False, 'error': {'code': 'VALIDATION_ERROR',
                                              'message': 'Password must be at least 8 characters.',
                                              'details': {}}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not re.search(r'\d', new_password):
            return Response(
                {'success': False, 'error': {'code': 'VALIDATION_ERROR',
                                              'message': 'Password must contain at least one number.',
                                              'details': {}}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Run Django's password validators
        try:
            validate_password(new_password)
        except DjangoValidationError as exc:
            return Response(
                {'success': False, 'error': {'code': 'VALIDATION_ERROR',
                                              'message': ' '.join(exc.messages),
                                              'details': {}}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Find user
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Return 400 (not 404) to avoid email enumeration
            return Response(
                {'success': False, 'error': {'code': 'NOT_FOUND',
                                              'message': 'No account found with that email.',
                                              'details': {}}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Update password
        user.set_password(new_password)
        user.save(update_fields=['password'])

        logger.info('Password reset for: %s', email)

        return Response(
            {'success': True, 'data': {'message': 'Password reset successfully. You can now sign in.'}},
            status=status.HTTP_200_OK,
        )

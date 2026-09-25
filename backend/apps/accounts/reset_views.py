"""
Password reset with OTP verification.

Flow:
  1. POST /api/auth/check-email/           — Verify the email belongs to a registered account
  2. POST /api/auth/reset-password/send-otp/ — Send a 6-digit OTP to the verified email
  3. POST /api/auth/reset-password/         — Submit email + otp + new_password to reset

All endpoints are public (AllowAny) since the user is not logged in.
"""
import logging
import re
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from .models import EmailVerificationOTP
from .otp_service import send_otp_email

User = get_user_model()
logger = logging.getLogger(__name__)


def _err(code: str, message: str, details: dict | None = None):
    return Response(
        {'success': False, 'error': {'code': code, 'message': message, 'details': details or {}}},
        status=status.HTTP_400_BAD_REQUEST,
    )


class CheckEmailView(APIView):
    """
    POST /api/auth/check-email/
    Body: { email }

    Checks whether a registered account exists for the given email.
    Returns success with a masked email if found.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email', '').strip().lower()

        if not email:
            return _err('VALIDATION_ERROR', 'Email address is required.')

        try:
            validate_email(email)
        except DjangoValidationError:
            return _err('VALIDATION_ERROR', 'Enter a valid email address.')

        if not User.objects.filter(email=email).exists():
            return _err('NOT_FOUND', 'No account found with that email address.')

        # Mask email for privacy: t***@example.com
        parts = email.split('@')
        masked = parts[0][0] + '***@' + parts[1] if len(parts) == 2 else email

        return Response(
            {'success': True, 'data': {'message': 'Account found.', 'masked_email': masked}},
            status=status.HTTP_200_OK,
        )


class ResetSendOTPView(APIView):
    """
    POST /api/auth/reset-password/send-otp/
    Body: { email }

    Sends a 6-digit OTP to the email for password reset verification.
    Requires that the account exists (call check-email first).
    """
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email', '').strip().lower()

        if not email:
            return _err('VALIDATION_ERROR', 'Email address is required.')

        try:
            validate_email(email)
        except DjangoValidationError:
            return _err('VALIDATION_ERROR', 'Enter a valid email address.')

        # Verify account exists
        if not User.objects.filter(email=email).exists():
            return _err('NOT_FOUND', 'No account found with that email address.')

        # Reuse the existing OTP email service
        success, message = send_otp_email(email)
        if not success:
            return _err('SEND_OTP_FAILED', message)

        return Response(
            {'success': True, 'data': {'message': message}},
            status=status.HTTP_200_OK,
        )


class VerifyResetOTPView(APIView):
    """
    POST /api/auth/reset-password/verify-otp/
    Body: { email, otp }

    Validates the OTP code without resetting the password.
    Called before showing the new-password form.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        email     = request.data.get('email', '').strip().lower()
        otp_input = request.data.get('otp', '').strip()

        if not email:
            return _err('VALIDATION_ERROR', 'Email is required.')
        if not otp_input or len(otp_input) != 6:
            return _err('VALIDATION_ERROR', 'Enter the 6-digit verification code.')

        # Find the latest unverified OTP for this email
        otp_record = EmailVerificationOTP.objects.filter(
            email=email,
            is_verified=False,
        ).order_by('-created_at').first()

        if not otp_record:
            return _err('OTP_INVALID', 'No verification code found. Please request a new one.')

        if otp_record.is_expired():
            return _err('OTP_EXPIRED', 'Verification code has expired. Please request a new one.')

        if otp_record.attempts >= 5:
            return _err('OTP_ATTEMPTS_EXCEEDED', 'Too many incorrect attempts. Please request a new code.')

        if otp_record.otp_code != otp_input:
            otp_record.attempts += 1
            otp_record.save(update_fields=['attempts'])
            remaining = 5 - otp_record.attempts
            return _err('OTP_INVALID', f'Invalid verification code. {remaining} attempt(s) remaining.')

        return Response(
            {'success': True, 'data': {'message': 'Verification code is valid.'}},
            status=status.HTTP_200_OK,
        )



class ResetPasswordView(APIView):
    """
    POST /api/auth/reset-password/
    Body: { email, otp, new_password }

    Validates the OTP, then resets the password.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        email        = request.data.get('email', '').strip().lower()
        otp_input    = request.data.get('otp', '').strip()
        new_password = request.data.get('new_password', '')

        # ── Validate inputs ────────────────────────────────────────────────
        if not email:
            return _err('VALIDATION_ERROR', 'Email is required.')
        if not otp_input:
            return _err('VALIDATION_ERROR', 'Verification code is required.')
        if not new_password:
            return _err('VALIDATION_ERROR', 'New password is required.')

        # ── Password strength checks ───────────────────────────────────────
        if len(new_password) < 8:
            return _err('VALIDATION_ERROR', 'Password must be at least 8 characters.')
        if not re.search(r'\d', new_password):
            return _err('VALIDATION_ERROR', 'Password must contain at least one number.')

        try:
            validate_password(new_password)
        except DjangoValidationError as exc:
            return _err('VALIDATION_ERROR', ' '.join(exc.messages))

        # ── Find user ──────────────────────────────────────────────────────
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return _err('NOT_FOUND', 'No account found with that email.')

        # ── Verify OTP ─────────────────────────────────────────────────────
        otp_record = EmailVerificationOTP.objects.filter(
            email=email,
            is_verified=False,
        ).order_by('-created_at').first()

        if not otp_record:
            return _err('OTP_INVALID', 'No verification code found. Please request a new one.')

        if otp_record.is_expired():
            return _err('OTP_EXPIRED', 'Verification code has expired. Please request a new one.')

        if otp_record.attempts >= 5:
            return _err('OTP_ATTEMPTS_EXCEEDED', 'Too many incorrect attempts. Please request a new code.')

        if otp_record.otp_code != otp_input:
            otp_record.attempts += 1
            otp_record.save(update_fields=['attempts'])
            remaining = 5 - otp_record.attempts
            return _err('OTP_INVALID', f'Invalid verification code. {remaining} attempt(s) remaining.')

        # ── OTP valid — reset password ─────────────────────────────────────
        user.set_password(new_password)
        user.save(update_fields=['password'])

        # Mark OTP as used
        otp_record.is_verified = True
        otp_record.save(update_fields=['is_verified'])

        # Clean up any other unverified OTPs for this email
        EmailVerificationOTP.objects.filter(email=email, is_verified=False).delete()

        logger.info('Password reset (OTP verified) for: %s', email)

        return Response(
            {'success': True, 'data': {'message': 'Password reset successfully. You can now sign in.'}},
            status=status.HTTP_200_OK,
        )

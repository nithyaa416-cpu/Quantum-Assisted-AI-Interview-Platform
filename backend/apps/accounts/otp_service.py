"""
Service for generating, storing, and emailing OTP codes.
"""
import secrets
import logging
from django.conf import settings
from django.core.mail import send_mail
from .models import EmailVerificationOTP

logger = logging.getLogger(__name__)


def generate_otp_code(length: int = 6) -> str:
    """Generate a cryptographically secure numeric OTP code."""
    digits = '0123456789'
    return ''.join(secrets.choice(digits) for _ in range(length))


def send_otp_email(email: str) -> tuple[bool, str]:
    """
    Generate an OTP and send it via email to the user.
    Enforces a 60-second cooldown between requests.
    Returns (success, message).
    """
    email = email.lower().strip()

    # Check for recent active OTP to enforce rate limit
    latest_otp = EmailVerificationOTP.objects.filter(
        email=email,
        is_verified=False
    ).first()

    if latest_otp and not latest_otp.can_resend(cooldown_seconds=60):
        return False, "Please wait at least 60 seconds before requesting a new code."

    # Mark all previous unverified OTPs as superseded
    EmailVerificationOTP.objects.filter(email=email, is_verified=False).delete()

    # Generate new code
    code = generate_otp_code(6)
    otp_record = EmailVerificationOTP.objects.create(email=email, otp_code=code)

    subject = f"{code} is your QAIP Verification Code"
    plain_message = (
        f"Hello,\n\n"
        f"Your verification code for the Quantum-Assisted AI Interview Platform is:\n\n"
        f"    {code}\n\n"
        f"This code will expire in 10 minutes.\n"
        f"If you did not request this, you can safely ignore this email.\n\n"
        f"— QAIP Team"
    )
    html_message = f"""
    <div style="font-family: Arial, sans-serif; max-width: 520px; margin: 0 auto; padding: 24px; background-color: #0f172a; color: #f8fafc; border-radius: 12px;">
      <h2 style="color: #818cf8; margin-bottom: 8px;">Quantum-Assisted AI Interview Platform</h2>
      <p style="color: #94a3b8; font-size: 14px;">Use the verification code below to complete your account registration:</p>
      <div style="background-color: #1e293b; border: 1px solid #334155; border-radius: 8px; text-align: center; padding: 20px; margin: 24px 0;">
        <span style="font-size: 32px; font-weight: bold; letter-spacing: 8px; color: #38bdf8; font-family: monospace;">{code}</span>
      </div>
      <p style="color: #64748b; font-size: 13px;">This code will expire in 10 minutes. If you did not request this, please ignore this email.</p>
    </div>
    """

    try:
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@qaip.local')
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=from_email,
            recipient_list=[email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info("Sent registration OTP to %s", email)
        return True, "Verification code sent to your email."
    except Exception as exc:
        logger.error("Failed to send OTP email to %s: %s", email, exc)
        # In debug/development mode, if SMTP fails or is not yet configured,
        # print the code prominently in the console so development continues smoothly.
        if settings.DEBUG:
            print(f"\n=======================================================")
            print(f" [DEV EMAIL FALLBACK] OTP for {email}: {code}")
            print(f"=======================================================\n")
            return True, "Verification code sent (view backend console in dev mode)."
        return False, "Failed to send email. Please check email settings or try again."

"""Development settings — DEBUG on, relaxed CORS, verbose logging."""
from .base import *  # noqa: F401, F403
from decouple import config

DEBUG = True

CORS_ALLOW_ALL_ORIGINS = True  # Allow all origins in dev
X_FRAME_OPTIONS = 'SAMEORIGIN'  # Allow iframe preview of resumes on localhost

# ---------------------------------------------------------------------------
# Database: use SQLite when USE_SQLITE=True (for local dev without PostgreSQL)
# Set USE_SQLITE=False and configure DATABASE_* vars to use PostgreSQL.
# ---------------------------------------------------------------------------
USE_SQLITE = config('USE_SQLITE', default=True, cast=bool)

if USE_SQLITE:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',  # noqa: F405
        }
    }

# Show SQL queries in dev
LOGGING['loggers']['django.db.backends'] = {  # noqa: F405
    'handlers': ['console'],
    'level': 'INFO',
    'propagate': False,
}

# If no SMTP credentials are configured, print emails to the terminal in dev mode
if not config('EMAIL_HOST_USER', default=''):
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'


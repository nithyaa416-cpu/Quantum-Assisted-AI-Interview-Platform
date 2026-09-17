"""Root URL configuration for QAIP Django backend."""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Django admin
    path('admin/', admin.site.urls),

    # Authentication endpoints  (register, login, logout, refresh, me)
    path('api/auth/', include('apps.accounts.urls')),

    # Student profile endpoints
    path('api/profile/', include('apps.accounts.profile_urls')),

    # Resume & target role endpoints
    path('api/resumes/', include('apps.resumes.urls')),

    # Interview session endpoints (legacy)
    path('api/sessions/', include('apps.sessions.urls')),

    # AI Interviewer endpoints
    path('api/interview/', include('apps.sessions.interview_urls')),

    # Assessment, skill-gap & coding-submission endpoints
    path('api/assessments/', include('apps.assessments.urls')),

    # Target roles (dedicated top-level route)
    path('api/target-roles/', include('apps.resumes.target_role_urls')),

    # Preparation plan & practice module endpoints
    path('api/preparation/', include('apps.preparation.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

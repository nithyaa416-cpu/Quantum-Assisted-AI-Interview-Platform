"""URL patterns for resumes app → /api/resumes/"""
from django.urls import path
from .views import (
    ResumeUploadView, ResumeListView, ResumeDetailView,
    ResumeStatusView, ResumeReParseView, ResumeSkillsView,
    ActiveResumeSummaryView,
    TargetRoleListCreateView, TargetRoleDetailView,
)

urlpatterns = [
    # Resume CRUD
    path('',                           ResumeListView.as_view(),          name='resume-list'),
    path('upload/',                    ResumeUploadView.as_view(),         name='resume-upload'),
    path('active/summary/',            ActiveResumeSummaryView.as_view(),  name='resume-active-summary'),
    path('<uuid:pk>/',                 ResumeDetailView.as_view(),         name='resume-detail'),
    path('<uuid:pk>/status/',          ResumeStatusView.as_view(),         name='resume-status'),
    path('<uuid:pk>/parse/',           ResumeReParseView.as_view(),        name='resume-parse'),
    path('<uuid:pk>/skills/',          ResumeSkillsView.as_view(),         name='resume-skills'),

    # Target roles
    path('target-roles/',             TargetRoleListCreateView.as_view(), name='targetrole-list'),
    path('target-roles/<uuid:pk>/',   TargetRoleDetailView.as_view(),     name='targetrole-detail'),
]

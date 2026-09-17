"""URL patterns for assessments app → mounted at /api/assessments/"""
from django.urls import path
from .views import AssessmentListView, AssessmentDetailView, SkillGapListView, CodingSubmissionListView

urlpatterns = [
    path('', AssessmentListView.as_view(), name='assessment-list'),
    path('sessions/<uuid:session_id>/', AssessmentDetailView.as_view(), name='assessment-detail'),
    path('skill-gaps/', SkillGapListView.as_view(), name='skill-gap-list'),
    path('coding/', CodingSubmissionListView.as_view(), name='coding-list'),
]

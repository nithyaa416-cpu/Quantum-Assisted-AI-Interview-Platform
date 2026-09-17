"""URL patterns for AI Interviewer → /api/interview/"""
from django.urls import path
from .interview_views import (
    InterviewSessionListCreateView,
    InterviewSessionDetailView,
    NextQuestionView,
    SubmitResponseView,
    EndInterviewView,
    InterviewHistoryView,
)

urlpatterns = [
    path('sessions/',                          InterviewSessionListCreateView.as_view(), name='interview-list'),
    path('sessions/<uuid:pk>/',                InterviewSessionDetailView.as_view(),     name='interview-detail'),
    path('sessions/<uuid:pk>/next/',           NextQuestionView.as_view(),               name='interview-next'),
    path('sessions/<uuid:pk>/respond/',        SubmitResponseView.as_view(),             name='interview-respond'),
    path('sessions/<uuid:pk>/end/',            EndInterviewView.as_view(),               name='interview-end'),
    path('sessions/<uuid:pk>/history/',        InterviewHistoryView.as_view(),           name='interview-history'),
]

"""URL patterns for sessions app → mounted at /api/sessions/"""
from django.urls import path
from .views import (
    InterviewSessionListCreateView,
    InterviewSessionDetailView,
    SessionStartView,
    SessionEndView,
)

urlpatterns = [
    path('', InterviewSessionListCreateView.as_view(), name='session-list'),
    path('<uuid:pk>/', InterviewSessionDetailView.as_view(), name='session-detail'),
    path('<uuid:pk>/start', SessionStartView.as_view(), name='session-start'),
    path('<uuid:pk>/end', SessionEndView.as_view(), name='session-end'),
]

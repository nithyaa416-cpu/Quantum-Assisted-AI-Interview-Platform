"""
URL patterns for preparation app → mounted at /api/preparation/
"""
from django.urls import path
from .views import (
    FeedbackAnalysisView,
    GeneratePlanView,
    PreparationPlanListView,
    ActivePreparationPlanView,
    PreparationPlanDetailView,
    RegeneratePlanView,
    PracticeModuleListView,
    PracticeModuleUpdateView,
    QuantumBenchmarkView,
)

urlpatterns = [
    # Feedback & Skill-gap extraction
    path('feedback-analysis/', FeedbackAnalysisView.as_view(), name='feedback-analysis'),

    # Plan Generation & Regeneration
    path('plans/generate/', GeneratePlanView.as_view(), name='plan-generate'),
    path('plans/', PreparationPlanListView.as_view(), name='plan-list'),
    path('plans/active/', ActivePreparationPlanView.as_view(), name='plan-active'),
    path('plans/<uuid:pk>/', PreparationPlanDetailView.as_view(), name='plan-detail'),
    path('plans/<uuid:pk>/regenerate/', RegeneratePlanView.as_view(), name='plan-regenerate'),

    # Practice Modules
    path('modules/', PracticeModuleListView.as_view(), name='module-list'),
    path('modules/<uuid:pk>/', PracticeModuleUpdateView.as_view(), name='module-update'),

    # Quantum vs Classical Benchmark
    path('benchmark/', QuantumBenchmarkView.as_view(), name='quantum-benchmark'),
]

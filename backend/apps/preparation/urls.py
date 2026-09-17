"""URL patterns for preparation app → mounted at /api/preparation/"""
from django.urls import path
from .views import (
    PreparationPlanListView,
    ActivePreparationPlanView,
    PracticeModuleListView,
    PracticeModuleUpdateView,
)

urlpatterns = [
    path('plans/', PreparationPlanListView.as_view(), name='plan-list'),
    path('plans/active/', ActivePreparationPlanView.as_view(), name='plan-active'),
    path('modules/', PracticeModuleListView.as_view(), name='module-list'),
    path('modules/<uuid:pk>/', PracticeModuleUpdateView.as_view(), name='module-update'),
]

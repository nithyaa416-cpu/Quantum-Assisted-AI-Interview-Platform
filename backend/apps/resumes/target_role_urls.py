"""
Dedicated URL patterns for Target Roles — mounted at /api/target-roles/
These sit separately from /api/resumes/ for a cleaner API surface.
"""
from django.urls import path
from .target_role_views import (
    TargetRoleListCreateView,
    TargetRoleDetailView,
    SetPrimaryRoleView,
    PrimaryRoleView,
    RoleCatalogueView,
    TargetRoleSkillGapView,
)

urlpatterns = [
    path('',                      TargetRoleListCreateView.as_view(), name='tr-list'),
    path('catalogue/',            RoleCatalogueView.as_view(),        name='tr-catalogue'),
    path('primary/',              PrimaryRoleView.as_view(),          name='tr-primary'),
    path('skill-gap/',            TargetRoleSkillGapView.as_view(),   name='tr-skill-gap'),
    path('<uuid:pk>/',            TargetRoleDetailView.as_view(),     name='tr-detail'),
    path('<uuid:pk>/set-primary/', SetPrimaryRoleView.as_view(),      name='tr-set-primary'),
]

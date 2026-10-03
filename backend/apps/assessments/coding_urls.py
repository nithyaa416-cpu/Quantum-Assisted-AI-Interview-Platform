"""URL patterns for the Coding Interview module."""
from django.urls import path
from .coding_views import (
    CodingProblemListView,
    CodingProblemDetailView,
    RunCodeView,
    SubmitCodeView,
    CodingSubmissionHistoryView,
    CodingWeaknessView,
    CodingRecommendationsView,
)

urlpatterns = [
    path('problems/',                    CodingProblemListView.as_view(),       name='coding-problems'),
    path('problems/<uuid:problem_id>/',  CodingProblemDetailView.as_view(),     name='coding-problem-detail'),
    path('run/',                         RunCodeView.as_view(),                 name='coding-run'),
    path('submit/',                      SubmitCodeView.as_view(),              name='coding-submit'),
    path('submissions/',                 CodingSubmissionHistoryView.as_view(), name='coding-submissions'),
    path('weaknesses/',                  CodingWeaknessView.as_view(),          name='coding-weaknesses'),
    path('recommendations/',             CodingRecommendationsView.as_view(),   name='coding-recommendations'),
]

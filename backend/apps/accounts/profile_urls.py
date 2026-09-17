"""Profile URL patterns → mounted at /api/profile/"""
from django.urls import path
from .views import StudentProfileView

urlpatterns = [
    path('me', StudentProfileView.as_view(), name='profile-me'),
]

"""Auth URL patterns → mounted at /api/auth/"""
from django.urls import path
from .views import (
    SendOTPView,
    RegisterView,
    LoginView,
    LogoutView,
    TokenRefreshView,
    CurrentUserView,
)
from .reset_views import ResetPasswordView

urlpatterns = [
    path('send-otp',        SendOTPView.as_view(),       name='auth-send-otp'),
    path('register',        RegisterView.as_view(),      name='auth-register'),

    path('login',           LoginView.as_view(),          name='auth-login'),
    path('logout',          LogoutView.as_view(),         name='auth-logout'),
    path('refresh',         TokenRefreshView.as_view(),   name='auth-refresh'),
    path('me',              CurrentUserView.as_view(),    name='auth-me'),
    path('reset-password/', ResetPasswordView.as_view(),  name='auth-reset-password'),
]

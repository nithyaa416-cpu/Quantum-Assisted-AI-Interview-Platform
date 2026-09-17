"""
Tests for accounts app: registration, login, logout, profile APIs.

Run with: pytest apps/accounts/tests.py -v
"""
import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model

from apps.accounts.models import StudentProfile

User = get_user_model()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def registered_user(db):
    """Create a real user in the test DB and return (user, password)."""
    user = User.objects.create_user(
        email='test@example.com',
        password='SecurePass1',
        full_name='Test Student',
    )
    return user, 'SecurePass1'


@pytest.fixture
def auth_client(client, registered_user):
    """Return an APIClient pre-authenticated with a valid JWT."""
    user, password = registered_user
    response = client.post('/api/auth/login', {
        'email': user.email,
        'password': password,
    }, format='json')
    tokens = response.data['data']['tokens']
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
    return client, tokens


# ---------------------------------------------------------------------------
# Registration tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestRegistration:

    def test_register_valid_data_returns_201_and_tokens(self, client):
        response = client.post('/api/auth/register', {
            'email': 'newuser@example.com',
            'password': 'StrongPass99',
            'confirm_password': 'StrongPass99',
            'full_name': 'New User',
        }, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        data = response.data
        assert data['success'] is True
        assert 'tokens' in data['data']
        assert 'access' in data['data']['tokens']
        assert 'refresh' in data['data']['tokens']
        assert data['data']['user']['email'] == 'newuser@example.com'

    def test_register_auto_creates_student_profile(self, client):
        client.post('/api/auth/register', {
            'email': 'profiletest@example.com',
            'password': 'StrongPass99',
            'confirm_password': 'StrongPass99',
            'full_name': 'Profile Test',
        }, format='json')

        user = User.objects.get(email='profiletest@example.com')
        assert StudentProfile.objects.filter(user=user).exists()

    def test_register_duplicate_email_returns_400(self, client, registered_user):
        response = client.post('/api/auth/register', {
            'email': 'test@example.com',
            'password': 'AnotherPass1',
            'confirm_password': 'AnotherPass1',
            'full_name': 'Duplicate User',
        }, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] is False

    def test_register_mismatched_passwords_returns_400(self, client):
        response = client.post('/api/auth/register', {
            'email': 'mismatch@example.com',
            'password': 'StrongPass99',
            'confirm_password': 'DifferentPass99',
            'full_name': 'Mismatch User',
        }, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] is False

    def test_register_password_without_number_returns_400(self, client):
        response = client.post('/api/auth/register', {
            'email': 'weakpass@example.com',
            'password': 'NoNumbersHere',
            'confirm_password': 'NoNumbersHere',
            'full_name': 'Weak Pass',
        }, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_short_password_returns_400(self, client):
        response = client.post('/api/auth/register', {
            'email': 'short@example.com',
            'password': 'S1x',
            'confirm_password': 'S1x',
            'full_name': 'Short Pass',
        }, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_invalid_email_returns_400(self, client):
        response = client.post('/api/auth/register', {
            'email': 'not-an-email',
            'password': 'StrongPass99',
            'confirm_password': 'StrongPass99',
            'full_name': 'Bad Email',
        }, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_missing_full_name_returns_400(self, client):
        response = client.post('/api/auth/register', {
            'email': 'noname@example.com',
            'password': 'StrongPass99',
            'confirm_password': 'StrongPass99',
        }, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ---------------------------------------------------------------------------
# Login tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestLogin:

    def test_login_correct_credentials_returns_200_and_tokens(self, client, registered_user):
        user, password = registered_user
        response = client.post('/api/auth/login', {
            'email': user.email,
            'password': password,
        }, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert 'access' in response.data['data']['tokens']
        assert 'refresh' in response.data['data']['tokens']

    def test_login_wrong_password_returns_401(self, client, registered_user):
        user, _ = registered_user
        response = client.post('/api/auth/login', {
            'email': user.email,
            'password': 'WrongPassword1',
        }, format='json')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data['success'] is False

    def test_login_nonexistent_email_returns_401(self, client):
        response = client.post('/api/auth/login', {
            'email': 'ghost@example.com',
            'password': 'AnyPass1',
        }, format='json')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_missing_fields_returns_400_or_401(self, client):
        response = client.post('/api/auth/login', {
            'email': 'test@example.com',
        }, format='json')

        assert response.status_code in (
            status.HTTP_400_BAD_REQUEST, status.HTTP_401_UNAUTHORIZED
        )


# ---------------------------------------------------------------------------
# Auth/me tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestCurrentUser:

    def test_me_without_token_returns_401(self, client):
        response = client.get('/api/auth/me')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_me_with_valid_token_returns_200(self, client, registered_user):
        user, password = registered_user
        login = client.post('/api/auth/login', {
            'email': user.email, 'password': password
        }, format='json')
        token = login.data['data']['tokens']['access']
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        response = client.get('/api/auth/me')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['email'] == user.email

    def test_me_with_invalid_token_returns_401(self, client):
        client.credentials(HTTP_AUTHORIZATION='Bearer invalidtoken.bad.signature')
        response = client.get('/api/auth/me')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ---------------------------------------------------------------------------
# Logout tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestLogout:

    def test_logout_blacklists_refresh_token(self, client, registered_user):
        user, password = registered_user
        login = client.post('/api/auth/login', {
            'email': user.email, 'password': password
        }, format='json')
        tokens = login.data['data']['tokens']
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')

        # Logout
        response = client.post('/api/auth/logout', {'refresh': tokens['refresh']}, format='json')
        assert response.status_code == status.HTTP_200_OK

    def test_logout_without_token_returns_401(self, client):
        response = client.post('/api/auth/logout', {'refresh': 'sometoken'}, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_logout_missing_refresh_returns_400(self, auth_client):
        client, _ = auth_client
        response = client.post('/api/auth/logout', {}, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ---------------------------------------------------------------------------
# Token refresh tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestTokenRefresh:

    def test_refresh_valid_token_returns_new_access(self, client, registered_user):
        user, password = registered_user
        login = client.post('/api/auth/login', {
            'email': user.email, 'password': password
        }, format='json')
        refresh_token = login.data['data']['tokens']['refresh']

        response = client.post('/api/auth/refresh', {'refresh': refresh_token}, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data['data']

    def test_refresh_invalid_token_returns_401(self, client):
        response = client.post('/api/auth/refresh', {'refresh': 'bad.token.here'}, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ---------------------------------------------------------------------------
# Student profile tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestStudentProfile:

    def test_get_profile_without_auth_returns_401(self, client):
        response = client.get('/api/profile/me')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_profile_returns_200_with_auth(self, auth_client):
        client, _ = auth_client
        response = client.get('/api/profile/me')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert 'email' in response.data['data']

    def test_patch_profile_updates_college(self, auth_client):
        client, _ = auth_client
        response = client.patch('/api/profile/me', {
            'college': 'MIT',
            'graduation_year': 2025,
        }, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['college'] == 'MIT'
        assert response.data['data']['graduation_year'] == 2025

    def test_patch_profile_updates_skills(self, auth_client):
        client, _ = auth_client
        response = client.patch('/api/profile/me', {
            'skills': ['Python', 'Django', 'PostgreSQL'],
        }, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert 'Python' in response.data['data']['skills']

    def test_patch_profile_invalid_graduation_year_returns_400(self, auth_client):
        client, _ = auth_client
        response = client.patch('/api/profile/me', {
            'graduation_year': 1800,
        }, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_patch_profile_invalid_skills_type_returns_400(self, auth_client):
        client, _ = auth_client
        response = client.patch('/api/profile/me', {
            'skills': 'not-a-list',
        }, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_put_profile_full_update(self, auth_client):
        client, _ = auth_client
        response = client.put('/api/profile/me', {
            'college': 'Stanford',
            'graduation_year': 2026,
            'phone': '9876543210',
            'bio': 'Passionate developer',
            'skills': ['Go', 'Kubernetes'],
            'target_roles': ['DevOps Engineer'],
            'linkedin_url': 'https://linkedin.com/in/test',
            'github_url': 'https://github.com/test',
        }, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['college'] == 'Stanford'
        assert 'Go' in response.data['data']['skills']

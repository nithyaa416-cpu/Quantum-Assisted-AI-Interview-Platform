"""
Tests for Target Role module.
Run: pytest apps/resumes/tests_target_roles.py -v
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status as http_status

from apps.resumes.models import TargetRole
from apps.resumes.role_catalogue import (
    ROLE_CATALOGUE, find_role, get_required_skills, get_interview_topics,
)

User = get_user_model()


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def auth_client(db):
    user = User.objects.create_user(
        email='tr_test@example.com', password='TestPass99', full_name='TR Tester'
    )
    c = APIClient()
    resp = c.post('/api/auth/login', {'email': user.email, 'password': 'TestPass99'}, format='json')
    token = resp.data['data']['tokens']['access']
    c.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    return c, user


@pytest.fixture
def auth_client2(db):
    user = User.objects.create_user(
        email='tr_test2@example.com', password='TestPass99', full_name='TR Tester2'
    )
    c = APIClient()
    resp = c.post('/api/auth/login', {'email': user.email, 'password': 'TestPass99'}, format='json')
    token = resp.data['data']['tokens']['access']
    c.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    return c, user


# ── Catalogue tests ───────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestRoleCatalogue:

    def test_catalogue_returns_all_roles(self, auth_client):
        client, _ = auth_client
        resp = client.get('/api/target-roles/catalogue/')
        assert resp.status_code == http_status.HTTP_200_OK
        assert resp.data['data']['total'] == len(ROLE_CATALOGUE)
        assert len(resp.data['data']['roles']) == len(ROLE_CATALOGUE)

    def test_catalogue_has_required_fields(self, auth_client):
        client, _ = auth_client
        resp = client.get('/api/target-roles/catalogue/')
        role = resp.data['data']['roles'][0]
        for field in ('display_name', 'domain', 'description',
                      'required_skills', 'interview_topics', 'coding_topics'):
            assert field in role

    def test_catalogue_filter_by_domain(self, auth_client):
        client, _ = auth_client
        resp = client.get('/api/target-roles/catalogue/?domain=backend')
        assert resp.status_code == http_status.HTTP_200_OK
        roles = resp.data['data']['roles']
        assert all(r['domain'] == 'backend' for r in roles)

    def test_catalogue_search_by_name(self, auth_client):
        client, _ = auth_client
        resp = client.get('/api/target-roles/catalogue/?q=python')
        assert resp.status_code == http_status.HTTP_200_OK
        assert resp.data['data']['total'] >= 1
        names = [r['display_name'].lower() for r in resp.data['data']['roles']]
        assert any('python' in n for n in names)

    def test_catalogue_search_by_alias(self, auth_client):
        client, _ = auth_client
        resp = client.get('/api/target-roles/catalogue/?q=sde')
        assert resp.status_code == http_status.HTTP_200_OK
        # 'sde' is an alias for Software Developer
        assert resp.data['data']['total'] >= 1

    def test_catalogue_requires_auth(self):
        c = APIClient()
        resp = c.get('/api/target-roles/catalogue/')
        assert resp.status_code == http_status.HTTP_401_UNAUTHORIZED


# ── CRUD tests ────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestTargetRoleCreateList:

    def test_create_role_from_catalogue(self, auth_client):
        client, _ = auth_client
        resp = client.post('/api/target-roles/', {
            'role_name': 'Python Developer',
            'domain': 'backend',
        }, format='json')
        assert resp.status_code == http_status.HTTP_201_CREATED
        data = resp.data['data']
        assert data['role_name'] == 'Python Developer'
        assert data['is_primary'] is True      # first role auto-set as primary
        assert len(data['required_skills']) > 0
        assert len(data['interview_topics']) > 0

    def test_create_custom_role_not_in_catalogue(self, auth_client):
        client, _ = auth_client
        resp = client.post('/api/target-roles/', {
            'role_name': 'Quantum Software Architect',
            'domain': 'software_engineering',
        }, format='json')
        assert resp.status_code == http_status.HTTP_201_CREATED
        assert resp.data['data']['role_name'] == 'Quantum Software Architect'

    def test_create_normalises_catalogue_name(self, auth_client):
        """Alias 'sde' should be normalised to 'Software Developer'."""
        client, _ = auth_client
        resp = client.post('/api/target-roles/', {
            'role_name': 'sde',
            'domain': 'software_engineering',
        }, format='json')
        assert resp.status_code == http_status.HTTP_201_CREATED
        assert resp.data['data']['role_name'] == 'Software Developer'

    def test_create_auto_detects_domain(self, auth_client):
        client, _ = auth_client
        resp = client.post('/api/target-roles/', {
            'role_name': 'Machine Learning Engineer',
        }, format='json')
        assert resp.status_code == http_status.HTTP_201_CREATED
        assert resp.data['data']['domain'] == 'machine_learning'

    def test_second_role_not_primary_by_default(self, auth_client):
        client, _ = auth_client
        client.post('/api/target-roles/', {'role_name': 'Python Developer', 'domain': 'backend'}, format='json')
        resp2 = client.post('/api/target-roles/', {'role_name': 'Data Analyst', 'domain': 'data_science'}, format='json')
        assert resp2.data['data']['is_primary'] is False

    def test_list_roles_returns_only_own(self, auth_client, auth_client2):
        client1, _ = auth_client
        client2, _ = auth_client2
        client1.post('/api/target-roles/', {'role_name': 'Python Developer', 'domain': 'backend'}, format='json')
        client2.post('/api/target-roles/', {'role_name': 'Data Analyst', 'domain': 'data_science'}, format='json')

        resp1 = client1.get('/api/target-roles/')
        resp2 = client2.get('/api/target-roles/')

        assert len(resp1.data['data']) == 1
        assert len(resp2.data['data']) == 1
        assert resp1.data['data'][0]['role_name'] == 'Python Developer'
        assert resp2.data['data'][0]['role_name'] == 'Data Analyst'

    def test_create_role_without_auth_returns_401(self):
        c = APIClient()
        resp = c.post('/api/target-roles/', {'role_name': 'Python Developer', 'domain': 'backend'}, format='json')
        assert resp.status_code == http_status.HTTP_401_UNAUTHORIZED

    def test_create_role_empty_name_returns_400(self, auth_client):
        client, _ = auth_client
        resp = client.post('/api/target-roles/', {'role_name': '', 'domain': 'backend'}, format='json')
        assert resp.status_code == http_status.HTTP_400_BAD_REQUEST

    def test_create_role_syncs_profile_target_roles(self, auth_client):
        client, user = auth_client
        client.post('/api/target-roles/', {'role_name': 'Python Developer', 'domain': 'backend'}, format='json')
        profile = user.student_profile
        profile.refresh_from_db()
        assert 'Python Developer' in profile.target_roles


# ── Detail / Update / Delete ──────────────────────────────────────────────────

@pytest.mark.django_db
class TestTargetRoleDetailUpdateDelete:

    def _create_role(self, client, name='Python Developer', domain='backend'):
        resp = client.post('/api/target-roles/', {'role_name': name, 'domain': domain}, format='json')
        return resp.data['data']['id']

    def test_get_detail_includes_catalogue_metadata(self, auth_client):
        client, _ = auth_client
        rid = self._create_role(client)
        resp = client.get(f'/api/target-roles/{rid}/')
        assert resp.status_code == http_status.HTTP_200_OK
        data = resp.data['data']
        assert len(data['required_skills']) > 0
        assert len(data['interview_topics']) > 0
        assert data['role_description'] != ''

    def test_patch_role_name(self, auth_client):
        client, _ = auth_client
        rid = self._create_role(client, 'Data Analyst', 'data_science')
        resp = client.patch(f'/api/target-roles/{rid}/', {'role_name': 'AI Engineer'}, format='json')
        assert resp.status_code == http_status.HTTP_200_OK
        assert resp.data['data']['role_name'] == 'AI Engineer'
        assert resp.data['data']['domain'] == 'machine_learning'  # auto-detected

    def test_delete_role(self, auth_client):
        client, _ = auth_client
        rid = self._create_role(client)
        resp = client.delete(f'/api/target-roles/{rid}/')
        assert resp.status_code == http_status.HTTP_200_OK
        assert client.get(f'/api/target-roles/{rid}/').status_code == http_status.HTTP_404_NOT_FOUND

    def test_delete_primary_promotes_next(self, auth_client):
        client, _ = auth_client
        rid1 = self._create_role(client, 'Python Developer', 'backend')
        rid2 = self._create_role(client, 'Data Analyst', 'data_science')
        # rid1 is primary; delete it
        client.delete(f'/api/target-roles/{rid1}/')
        resp = client.get(f'/api/target-roles/{rid2}/')
        assert resp.data['data']['is_primary'] is True

    def test_cannot_access_other_users_role(self, auth_client, auth_client2):
        client1, _ = auth_client
        client2, _ = auth_client2
        rid = self._create_role(client1)
        resp = client2.get(f'/api/target-roles/{rid}/')
        assert resp.status_code == http_status.HTTP_404_NOT_FOUND


# ── Set primary ───────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestSetPrimary:

    def test_set_primary_changes_primary_role(self, auth_client):
        client, _ = auth_client
        r1 = client.post('/api/target-roles/', {'role_name': 'Python Developer', 'domain': 'backend'}, format='json').data['data']['id']
        r2 = client.post('/api/target-roles/', {'role_name': 'Data Analyst', 'domain': 'data_science'}, format='json').data['data']['id']

        # r1 is primary; switch to r2
        resp = client.post(f'/api/target-roles/{r2}/set-primary/')
        assert resp.status_code == http_status.HTTP_200_OK
        assert resp.data['data']['is_primary'] is True

        # r1 should no longer be primary
        r1_resp = client.get(f'/api/target-roles/{r1}/')
        assert r1_resp.data['data']['is_primary'] is False

    def test_only_one_primary_exists(self, auth_client):
        client, _ = auth_client
        ids = []
        for name in ['Python Developer', 'Data Analyst', 'AI Engineer']:
            domain = 'backend' if name == 'Python Developer' else 'data_science' if name == 'Data Analyst' else 'machine_learning'
            rid = client.post('/api/target-roles/', {'role_name': name, 'domain': domain}, format='json').data['data']['id']
            ids.append(rid)

        client.post(f'/api/target-roles/{ids[2]}/set-primary/')
        roles = client.get('/api/target-roles/').data['data']
        primary_count = sum(1 for r in roles if r['is_primary'])
        assert primary_count == 1


# ── Primary role endpoint ─────────────────────────────────────────────────────

@pytest.mark.django_db
class TestPrimaryRole:

    def test_get_primary_returns_primary_role(self, auth_client):
        client, _ = auth_client
        client.post('/api/target-roles/', {'role_name': 'Python Developer', 'domain': 'backend'}, format='json')
        resp = client.get('/api/target-roles/primary/')
        assert resp.status_code == http_status.HTTP_200_OK
        assert resp.data['data']['is_primary'] is True

    def test_get_primary_no_role_returns_404(self, auth_client):
        client, _ = auth_client
        resp = client.get('/api/target-roles/primary/')
        assert resp.status_code == http_status.HTTP_404_NOT_FOUND


# ── Skill gap ─────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestSkillGap:

    def test_skill_gap_returns_missing_and_present(self, auth_client):
        client, user = auth_client
        # Create role
        client.post('/api/target-roles/', {'role_name': 'Python Developer', 'domain': 'backend'}, format='json')
        # Give student some skills
        client.patch('/api/profile/me', {'skills': ['Python', 'Django']}, format='json')

        resp = client.get('/api/target-roles/skill-gap/')
        assert resp.status_code == http_status.HTTP_200_OK
        data = resp.data['data']
        assert 'required_skills' in data
        assert 'present_skills' in data
        assert 'missing_skills' in data
        assert 'gap_percentage' in data
        assert 'Python' in data['present_skills']
        assert 0 <= data['gap_percentage'] <= 100

    def test_skill_gap_no_primary_returns_404(self, auth_client):
        client, _ = auth_client
        resp = client.get('/api/target-roles/skill-gap/')
        assert resp.status_code == http_status.HTTP_404_NOT_FOUND

    def test_skill_gap_by_role_id(self, auth_client):
        client, _ = auth_client
        rid = client.post(
            '/api/target-roles/', {'role_name': 'Data Analyst', 'domain': 'data_science'}, format='json'
        ).data['data']['id']

        resp = client.get(f'/api/target-roles/skill-gap/?role_id={rid}')
        assert resp.status_code == http_status.HTTP_200_OK
        assert resp.data['data']['role']['role_name'] == 'Data Analyst'


# ── Catalogue unit tests (no DB) ──────────────────────────────────────────────

class TestRoleCatalogueUnit:

    def test_find_role_by_display_name(self):
        role = find_role('Python Developer')
        assert role is not None
        assert role['display_name'] == 'Python Developer'

    def test_find_role_by_alias(self):
        role = find_role('ml engineer')
        assert role is not None
        assert role['display_name'] == 'Machine Learning Engineer'

    def test_find_role_case_insensitive(self):
        assert find_role('PYTHON DEVELOPER') is not None
        assert find_role('python developer') is not None

    def test_find_role_unknown_returns_none(self):
        assert find_role('Intergalactic Chef') is None

    def test_get_required_skills_known_role(self):
        skills = get_required_skills('Python Developer')
        assert len(skills) > 0
        assert 'Python' in skills

    def test_get_interview_topics_known_role(self):
        topics = get_interview_topics('AI Engineer')
        assert len(topics) > 0

    def test_all_roles_have_required_fields(self):
        for role in ROLE_CATALOGUE:
            assert role['display_name']
            assert role['domain']
            assert len(role['required_skills']) > 0
            assert len(role['interview_topics']) > 0
            assert len(role['coding_topics']) > 0

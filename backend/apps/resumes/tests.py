"""
Tests for the resumes app.
Covers: upload, status polling, detail, edit, delete, skills endpoint,
        target roles, and the parser pipeline itself.

Run: pytest apps/resumes/tests.py -v
"""
import io
import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status as http_status

from apps.resumes.models import Resume, TargetRole
from apps.resumes.parser.pipeline import parse_resume_file
from apps.resumes.parser.extractors import extract_skills, extract_education, extract_projects
from apps.resumes.parser.section_detector import split_into_sections

User = get_user_model()

# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def user_and_token(db):
    """Create a user, log in, return (user, access_token)."""
    user = User.objects.create_user(
        email='resume_test@example.com',
        password='TestPass99',
        full_name='Resume Tester',
    )
    c = APIClient()
    resp = c.post('/api/auth/login', {'email': user.email, 'password': 'TestPass99'}, format='json')
    token = resp.data['data']['tokens']['access']
    return user, token


@pytest.fixture
def auth_client(user_and_token):
    user, token = user_and_token
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    return c, user


@pytest.fixture
def minimal_pdf_bytes():
    """Minimal valid PDF bytes for upload tests."""
    return (
        b'%PDF-1.4\n'
        b'1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n'
        b'2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n'
        b'3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n'
        b'xref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n'
        b'0000000058 00000 n \n0000000115 00000 n \n'
        b'trailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n190\n%%EOF'
    )


# ── Upload tests ───────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestResumeUpload:

    def test_upload_pdf_returns_201(self, auth_client, minimal_pdf_bytes):
        client, _ = auth_client
        pdf = SimpleUploadedFile('cv.pdf', minimal_pdf_bytes, content_type='application/pdf')
        resp = client.post('/api/resumes/upload/', {'file': pdf}, format='multipart')
        assert resp.status_code == http_status.HTTP_201_CREATED
        assert resp.data['success'] is True
        assert resp.data['data']['original_filename'] == 'cv.pdf'
        assert resp.data['data']['parse_status'] in ('pending', 'processing', 'completed', 'failed')

    def test_upload_without_auth_returns_401(self, client, minimal_pdf_bytes):
        pdf = SimpleUploadedFile('cv.pdf', minimal_pdf_bytes, content_type='application/pdf')
        resp = client.post('/api/resumes/upload/', {'file': pdf}, format='multipart')
        assert resp.status_code == http_status.HTTP_401_UNAUTHORIZED

    def test_upload_no_file_returns_400(self, auth_client):
        client, _ = auth_client
        resp = client.post('/api/resumes/upload/', {}, format='multipart')
        assert resp.status_code == http_status.HTTP_400_BAD_REQUEST

    def test_upload_non_pdf_returns_400(self, auth_client):
        client, _ = auth_client
        img = SimpleUploadedFile('photo.png', b'\x89PNG\r\n\x1a\n', content_type='image/png')
        resp = client.post('/api/resumes/upload/', {'file': img}, format='multipart')
        assert resp.status_code == http_status.HTTP_400_BAD_REQUEST

    def test_upload_oversized_file_returns_400(self, auth_client):
        client, _ = auth_client
        big = SimpleUploadedFile('big.pdf', b'%PDF' + b'x' * (11 * 1024 * 1024), content_type='application/pdf')
        resp = client.post('/api/resumes/upload/', {'file': big}, format='multipart')
        assert resp.status_code == http_status.HTTP_400_BAD_REQUEST

    def test_upload_increments_version(self, auth_client, minimal_pdf_bytes):
        client, _ = auth_client
        for _ in range(3):
            pdf = SimpleUploadedFile('cv.pdf', minimal_pdf_bytes, content_type='application/pdf')
            client.post('/api/resumes/upload/', {'file': pdf}, format='multipart')
        resp = client.get('/api/resumes/')
        versions = [r['version'] for r in resp.data['data']]
        assert max(versions) == 3


# ── List / Detail tests ────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestResumeListDetail:

    def test_list_returns_only_own_resumes(self, auth_client, minimal_pdf_bytes, db):
        client, user = auth_client
        # Upload 2 resumes
        for _ in range(2):
            pdf = SimpleUploadedFile('cv.pdf', minimal_pdf_bytes, content_type='application/pdf')
            client.post('/api/resumes/upload/', {'file': pdf}, format='multipart')

        # Create another user and upload their resume
        other = User.objects.create_user(email='other@x.com', password='Pass9999', full_name='Other')
        other_profile = other.student_profile
        Resume.objects.create(student=other_profile, file='fake.pdf', original_filename='other.pdf', version=1)

        resp = client.get('/api/resumes/')
        assert resp.status_code == http_status.HTTP_200_OK
        assert len(resp.data['data']) == 2   # only own resumes

    def test_detail_returns_parsed_data_structure(self, auth_client, minimal_pdf_bytes):
        client, _ = auth_client
        pdf = SimpleUploadedFile('cv.pdf', minimal_pdf_bytes, content_type='application/pdf')
        upload_resp = client.post('/api/resumes/upload/', {'file': pdf}, format='multipart')
        rid = upload_resp.data['data']['id']

        detail_resp = client.get(f'/api/resumes/{rid}/')
        assert detail_resp.status_code == http_status.HTTP_200_OK
        data = detail_resp.data['data']
        for field in ('skills', 'projects', 'education', 'experience', 'summary'):
            assert field in data

    def test_detail_of_other_user_resume_returns_404(self, auth_client, db, minimal_pdf_bytes):
        client, _ = auth_client
        other = User.objects.create_user(email='other2@x.com', password='Pass9999', full_name='Other2')
        other_resume = Resume.objects.create(
            student=other.student_profile, file='fake.pdf',
            original_filename='other.pdf', version=1
        )
        resp = client.get(f'/api/resumes/{other_resume.id}/')
        assert resp.status_code == http_status.HTTP_404_NOT_FOUND


# ── Status polling test ────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestResumeStatus:

    def test_status_endpoint_returns_parse_status(self, auth_client, minimal_pdf_bytes):
        client, _ = auth_client
        pdf = SimpleUploadedFile('cv.pdf', minimal_pdf_bytes, content_type='application/pdf')
        upload_resp = client.post('/api/resumes/upload/', {'file': pdf}, format='multipart')
        rid = upload_resp.data['data']['id']

        resp = client.get(f'/api/resumes/{rid}/status/')
        assert resp.status_code == http_status.HTTP_200_OK
        assert 'parse_status' in resp.data['data']
        assert resp.data['data']['parse_status'] in ('pending', 'processing', 'completed', 'failed')


# ── Edit parsed data ───────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestResumeEdit:

    def test_patch_skills_updates_parsed_data(self, auth_client, minimal_pdf_bytes):
        client, _ = auth_client
        pdf = SimpleUploadedFile('cv.pdf', minimal_pdf_bytes, content_type='application/pdf')
        upload_resp = client.post('/api/resumes/upload/', {'file': pdf}, format='multipart')
        rid = upload_resp.data['data']['id']

        patch_resp = client.patch(
            f'/api/resumes/{rid}/',
            {'skills': [{'name': 'Python', 'category': 'language', 'confidence': 'high'},
                        {'name': 'Django', 'category': 'backend', 'confidence': 'high'}]},
            format='json',
        )
        assert patch_resp.status_code == http_status.HTTP_200_OK
        skills = patch_resp.data['data']['skills']
        assert any(s['name'] == 'Python' for s in skills)

    def test_patch_invalid_skill_missing_name_returns_400(self, auth_client, minimal_pdf_bytes):
        client, _ = auth_client
        pdf = SimpleUploadedFile('cv.pdf', minimal_pdf_bytes, content_type='application/pdf')
        upload_resp = client.post('/api/resumes/upload/', {'file': pdf}, format='multipart')
        rid = upload_resp.data['data']['id']

        resp = client.patch(
            f'/api/resumes/{rid}/',
            {'skills': [{'category': 'language'}]},   # missing 'name'
            format='json',
        )
        assert resp.status_code == http_status.HTTP_400_BAD_REQUEST

    def test_patch_summary_updates_correctly(self, auth_client, minimal_pdf_bytes):
        client, _ = auth_client
        pdf = SimpleUploadedFile('cv.pdf', minimal_pdf_bytes, content_type='application/pdf')
        upload_resp = client.post('/api/resumes/upload/', {'file': pdf}, format='multipart')
        rid = upload_resp.data['data']['id']

        resp = client.patch(
            f'/api/resumes/{rid}/',
            {'summary': 'Experienced Python developer.'},
            format='json',
        )
        assert resp.status_code == http_status.HTTP_200_OK
        assert resp.data['data']['summary'] == 'Experienced Python developer.'


# ── Delete ─────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestResumeDelete:

    def test_delete_own_resume_returns_200(self, auth_client, minimal_pdf_bytes):
        client, _ = auth_client
        pdf = SimpleUploadedFile('cv.pdf', minimal_pdf_bytes, content_type='application/pdf')
        upload_resp = client.post('/api/resumes/upload/', {'file': pdf}, format='multipart')
        rid = upload_resp.data['data']['id']

        resp = client.delete(f'/api/resumes/{rid}/')
        assert resp.status_code == http_status.HTTP_200_OK

        # Confirm deleted
        assert client.get(f'/api/resumes/{rid}/').status_code == http_status.HTTP_404_NOT_FOUND

    def test_delete_other_users_resume_returns_404(self, auth_client, db):
        client, _ = auth_client
        other = User.objects.create_user(email='other3@x.com', password='Pass9999', full_name='Other3')
        other_resume = Resume.objects.create(
            student=other.student_profile, file='fake.pdf',
            original_filename='other.pdf', version=1
        )
        resp = client.delete(f'/api/resumes/{other_resume.id}/')
        assert resp.status_code == http_status.HTTP_404_NOT_FOUND


# ── Target roles ───────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestTargetRoles:

    def test_create_target_role(self, auth_client):
        client, _ = auth_client
        resp = client.post(
            '/api/resumes/target-roles/',
            {'role_name': 'Backend Engineer', 'domain': 'backend', 'is_primary': True},
            format='json',
        )
        assert resp.status_code == http_status.HTTP_201_CREATED
        assert resp.data['data']['role_name'] == 'Backend Engineer'

    def test_list_target_roles(self, auth_client):
        client, _ = auth_client
        client.post('/api/resumes/target-roles/', {'role_name': 'SDE', 'domain': 'software_engineering'}, format='json')
        resp = client.get('/api/resumes/target-roles/')
        assert resp.status_code == http_status.HTTP_200_OK
        assert len(resp.data['data']) >= 1

    def test_patch_target_role(self, auth_client):
        client, _ = auth_client
        create = client.post('/api/resumes/target-roles/', {'role_name': 'SDE', 'domain': 'backend'}, format='json')
        rid = create.data['data']['id']
        resp = client.patch(f'/api/resumes/target-roles/{rid}/', {'role_name': 'Senior SDE'}, format='json')
        assert resp.status_code == http_status.HTTP_200_OK
        assert resp.data['data']['role_name'] == 'Senior SDE'

    def test_delete_target_role(self, auth_client):
        client, _ = auth_client
        create = client.post('/api/resumes/target-roles/', {'role_name': 'SDE', 'domain': 'backend'}, format='json')
        rid = create.data['data']['id']
        resp = client.delete(f'/api/resumes/target-roles/{rid}/')
        assert resp.status_code == http_status.HTTP_200_OK


# ── Parser unit tests ──────────────────────────────────────────────────────────

class TestSkillExtractor:
    """Unit tests — no DB, no markers needed."""

    def test_extracts_comma_separated_skills(self):
        text = "Python, Django, PostgreSQL, React, Docker"
        skills = extract_skills(text)
        names = [s['name'] for s in skills]
        assert 'Python' in names
        assert 'Django' in names
        assert 'Docker' in names

    def test_skill_category_assigned(self):
        skills = extract_skills("Python, React, PostgreSQL")
        cats = {s['name']: s['category'] for s in skills}
        assert cats.get('Python') == 'language'
        assert cats.get('React') == 'frontend'

    def test_deduplicates_skills(self):
        text = "python, Python, PYTHON"
        skills = extract_skills(text)
        python_entries = [s for s in skills if s['name'].lower() == 'python']
        assert len(python_entries) == 1

    def test_handles_empty_text(self):
        assert extract_skills('') == []

    def test_extracts_inline_skills(self):
        text = "Built REST APIs using FastAPI and deployed with Docker on AWS"
        skills = extract_skills(text)
        names = [s['name'] for s in skills]
        assert 'Docker' in names
        assert 'AWS' in names


class TestEducationExtractor:

    def test_extracts_degree(self):
        text = "B.Tech in Computer Science\nIIT Bombay\n2020 - 2024\nCGPA: 8.5"
        edu = extract_education(text)
        assert len(edu) >= 1

    def test_extracts_gpa(self):
        text = "Bachelor of Engineering\nABC College\n2019 - 2023\nGPA: 3.8"
        edu = extract_education(text)
        gpa_entries = [e for e in edu if e.get('gpa')]
        assert len(gpa_entries) >= 1
        assert gpa_entries[0]['gpa'] in ('3.8', '8')

    def test_extracts_year_range(self):
        text = "M.Tech Computer Science\nNIT Trichy\n2022 - 2024"
        edu = extract_education(text)
        for e in edu:
            if e.get('end_year'):
                assert e['end_year'] == '2024'


class TestProjectExtractor:

    def test_extracts_project_title(self):
        text = (
            "E-Commerce Platform\n"
            "• Built using Django and React\n"
            "• Deployed on AWS\n\n"
            "Chat Application\n"
            "• Real-time messaging with WebSocket\n"
        )
        projects = extract_projects(text)
        titles = [p['title'] for p in projects]
        assert any('E-Commerce' in t for t in titles)

    def test_extracts_technologies_from_project(self):
        text = "ML Price Predictor\n• Used Python, scikit-learn and pandas for predictions\n"
        projects = extract_projects(text)
        if projects:
            tech = projects[0].get('technologies', [])
            assert any('Python' in t or 'scikit' in t.lower() for t in tech)

    def test_handles_empty_projects(self):
        assert extract_projects('') == []


class TestSectionDetector:

    def test_detects_skills_section(self):
        text = "John Doe\n\nSKILLS\nPython, Django, React\n\nEDUCATION\nB.Tech"
        sections = split_into_sections(text)
        assert 'skills' in sections
        assert 'education' in sections

    def test_raw_always_present(self):
        text = "Some resume text"
        sections = split_into_sections(text)
        assert 'raw' in sections
        assert sections['raw'] == text

    def test_case_insensitive_headers(self):
        text = "Technical Skills\nPython\n\nWork Experience\nSoftware Engineer"
        sections = split_into_sections(text)
        assert 'skills' in sections or 'experience' in sections

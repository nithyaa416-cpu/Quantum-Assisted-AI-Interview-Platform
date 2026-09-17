# Phase 1 Setup Guide — QAIP Backend

## What was built

| Item | Status |
|---|---|
| 12 Django models across 5 apps | ✅ |
| Migrations (SQLite for dev, PostgreSQL for production) | ✅ |
| JWT auth: register, login, logout, refresh, /me | ✅ |
| Student profile CRUD | ✅ |
| Protected APIs (all non-auth endpoints require Bearer token) | ✅ |
| Consistent JSON response envelope | ✅ |
| 27 automated tests — all passing | ✅ |

---

## 1. Quick Start (Local Development — SQLite)

```bash
cd "d:\7th sem\main_project\backend"

# Install dependencies
pip install -r requirements.txt

# The .env file is already configured with USE_SQLITE=True
# (No PostgreSQL needed for local dev/testing)

# Run migrations
python manage.py migrate

# Create a superuser (optional)
python manage.py createsuperuser

# Start development server
python manage.py runserver
```

---

## 2. Switch to PostgreSQL (Production / Full Setup)

### Step 1: Install PostgreSQL
Download from https://www.postgresql.org/download/windows/

### Step 2: Create the database
```sql
-- In psql or pgAdmin:
CREATE DATABASE qaip_db;
CREATE USER qaip_user WITH PASSWORD 'your_strong_password';
GRANT ALL PRIVILEGES ON DATABASE qaip_db TO qaip_user;
```

### Step 3: Update .env
```
USE_SQLITE=False
DATABASE_NAME=qaip_db
DATABASE_USER=qaip_user
DATABASE_PASSWORD=your_strong_password
DATABASE_HOST=localhost
DATABASE_PORT=5432
```

### Step 4: Run migrations against PostgreSQL
```bash
python manage.py migrate
```

---

## 3. Environment Variables (.env)

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | (set in .env) | Django secret key |
| `DEBUG` | `True` | Debug mode |
| `USE_SQLITE` | `True` | Use SQLite (dev) or PostgreSQL (prod) |
| `DATABASE_NAME` | `qaip_db` | PostgreSQL DB name |
| `DATABASE_USER` | `postgres` | PostgreSQL user |
| `DATABASE_PASSWORD` | — | PostgreSQL password |
| `DATABASE_HOST` | `localhost` | PostgreSQL host |
| `DATABASE_PORT` | `5432` | PostgreSQL port |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis for Celery |
| `JWT_SECRET` | (set in .env) | Shared JWT secret (also used by FastAPI) |
| `CORS_ORIGIN` | `http://localhost:3000` | Frontend origin |

---

## 4. Run Tests

```bash
# All account tests
pytest apps/accounts/tests.py -v

# All tests with coverage
pytest --cov=apps --cov-report=term-missing -v
```

---

## 5. API Reference

### Auth endpoints (no token required)

| Method | URL | Body |
|---|---|---|
| POST | `/api/auth/register` | `{email, password, confirm_password, full_name}` |
| POST | `/api/auth/login` | `{email, password}` |
| POST | `/api/auth/refresh` | `{refresh}` |

### Auth endpoints (token required: `Authorization: Bearer <access_token>`)

| Method | URL | Description |
|---|---|---|
| GET | `/api/auth/me` | Current user info |
| POST | `/api/auth/logout` | Body: `{refresh}` |
| GET | `/api/profile/me` | Student profile |
| PATCH | `/api/profile/me` | Update profile fields |
| PUT | `/api/profile/me` | Full profile update |

---

## 6. Example curl Commands

### Register
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"student@example.com","password":"SecurePass1","confirm_password":"SecurePass1","full_name":"Arjun Kumar"}'
```

### Login
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"student@example.com","password":"SecurePass1"}'
```

### Get profile (use access token from login)
```bash
curl http://localhost:8000/api/profile/me \
  -H "Authorization: Bearer <your_access_token>"
```

### Update profile
```bash
curl -X PATCH http://localhost:8000/api/profile/me \
  -H "Authorization: Bearer <your_access_token>" \
  -H "Content-Type: application/json" \
  -d '{"college":"IIT Bombay","graduation_year":2025,"skills":["Python","Django","SQL"]}'
```

### Logout
```bash
curl -X POST http://localhost:8000/api/auth/logout \
  -H "Authorization: Bearer <your_access_token>" \
  -H "Content-Type: application/json" \
  -d '{"refresh":"<your_refresh_token>"}'
```

---

## 7. Database Models Summary

| Model | App | Table |
|---|---|---|
| CustomUser | accounts | `accounts_user` |
| StudentProfile | accounts | `accounts_student_profile` |
| Resume | resumes | `resumes_resume` |
| TargetRole | resumes | `resumes_target_role` |
| InterviewSession | sessions | `sessions_interview_session` |
| InterviewQuestion | sessions | `sessions_interview_question` |
| StudentResponse | sessions | `sessions_student_response` |
| CodingSubmission | assessments | `assessments_coding_submission` |
| Assessment | assessments | `assessments_assessment` |
| SkillGap | assessments | `assessments_skill_gap` |
| PreparationPlan | preparation | `preparation_plan` |
| PracticeModule | preparation | `preparation_practice_module` |

---

## 8. Notes

- All models use UUID primary keys.
- StudentProfile is auto-created on user registration via a `post_save` signal.
- All performance data is individual — no cross-student queries exist.
- JWT tokens: access token expires in 15 minutes, refresh token in 7 days.
- Refresh tokens are blacklisted on logout (uses `rest_framework_simplejwt.token_blacklist`).
- The `apps.sessions` app uses Django label `interview_sessions` to avoid conflict with `django.contrib.sessions`.

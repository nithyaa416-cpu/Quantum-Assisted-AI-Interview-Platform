@echo off
echo ================================
echo  QAIP - Starting Services
echo ================================

echo.
echo [1/3] Starting Judge0 code execution engine (Docker) ...
cd /d "%~dp0judge0"
docker compose up -d >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [!] Notice: Docker is not running or Judge0 could not start.
    echo     You can still use auth, resume, and interview features.
    echo     Start Docker Desktop if you plan to run coding assessments.
) else (
    echo [*] Judge0 service running on http://localhost:2358
)

echo.
echo [2/3] Starting Django backend on http://localhost:8000 ...
start "QAIP Backend" cmd /k "cd /d "%~dp0backend" && call venv\Scripts\activate.bat && python manage.py runserver"

timeout /t 3 /nobreak >nul

echo [3/3] Starting React frontend on http://localhost:3000 ...
start "QAIP Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"

timeout /t 3 /nobreak >nul

echo.
echo ================================
echo  All services are starting up!
echo  Backend:  http://localhost:8000
echo  Frontend: http://localhost:3000
echo  Judge0:   http://localhost:2358 (if Docker is on)
echo ================================
echo.
echo You can close this window.
pause



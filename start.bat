@echo off
echo ================================
echo  QAIP - Starting both servers
echo ================================

echo.
echo [1/2] Starting Django backend on http://localhost:8000 ...
start "QAIP Backend" cmd /k "cd /d d:\7th sem\main_project\backend && python manage.py runserver"

timeout /t 3 /nobreak >nul

echo [2/2] Starting React frontend on http://localhost:3000 ...
start "QAIP Frontend" cmd /k "cd /d d:\7th sem\main_project\frontend && npm run dev"

timeout /t 4 /nobreak >nul

echo.
echo ================================
echo  Both servers are starting up.
echo  Backend:  http://localhost:8000
echo  Frontend: http://localhost:3000
echo ================================
echo.
echo Open your browser at: http://localhost:3000
echo.
pause

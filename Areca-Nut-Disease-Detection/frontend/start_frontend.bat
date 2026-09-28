@echo off
echo ========================================
echo   Arecanut Agri Assistant - Frontend
echo ========================================
echo.
echo Starting frontend server...
echo Frontend will be available at: http://localhost:3000
echo.
echo Make sure the backend is running at http://localhost:8000
echo.

cd /d "%~dp0"

REM Check if Python HTTP server is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Python not found! Please install Python first.
    pause
    exit /b
)

echo Opening browser...
start http://localhost:3000

echo Starting server on port 3000...
python -m http.server 3000

pause

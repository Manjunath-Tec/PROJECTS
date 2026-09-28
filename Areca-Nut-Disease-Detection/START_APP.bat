@echo off
title Arecanut Agri Assistant - Launcher
color 0A

echo.
echo ========================================
echo   ARECANUT AGRI ASSISTANT
echo   Smart Farming Platform
echo ========================================
echo.

REM ── Check if the Python 3.11 venv exists ─────────────────────────────────
if exist "backend\venv\Scripts\python.exe" (
    echo [OK] Python 3.11 virtual environment found
    set PYTHON=backend\venv\Scripts\python.exe
    set PIP=backend\venv\Scripts\pip.exe
) else (
    echo [WARN] Virtual environment not found. Falling back to system Python.
    where python >nul 2>&1
    if errorlevel 1 (
        py --version >nul 2>&1
        if errorlevel 1 (
            echo [ERROR] Python not found! Install Python from https://python.org
            pause
            exit /b 1
        )
        set PYTHON=py
        set PIP=py -m pip
    ) else (
        set PYTHON=python
        set PIP=python -m pip
    )
)

echo.

REM ── Install backend dependencies if needed ───────────────────────────────
"%PYTHON%" -c "import fastapi" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing backend dependencies...
    "%PIP%" install -r backend\requirements.txt
    echo.
)

echo [OK] Dependencies ready
echo.

echo ========================================
echo   STARTING SERVICES
echo ========================================
echo.
echo   Backend API  : http://localhost:8000
echo   API Docs     : http://localhost:8000/docs
echo   Frontend App : http://localhost:3000
echo.
echo   Press Ctrl+C in each window to stop
echo ========================================
echo.

REM ── Start backend with the venv python ───────────────────────────────────
start "Backend (Port 8000)" cmd /k "cd /d %~dp0backend && venv\Scripts\python.exe -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"

REM ── Wait for backend to initialize ───────────────────────────────────────
timeout /t 5 /nobreak >nul

REM ── Start frontend ────────────────────────────────────────────────────────
start "Frontend (Port 3000)" cmd /k "cd /d %~dp0frontend && python -m http.server 3000"

REM ── Open browser ─────────────────────────────────────────────────────────
timeout /t 2 /nobreak >nul
echo Opening browser...
start http://localhost:3000

echo.
echo [OK] All services started. Close the terminal windows to stop them.
echo.
pause

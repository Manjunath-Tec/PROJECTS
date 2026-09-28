@echo off
echo ========================================
echo   Arecanut Agri Assistant - Backend
echo ========================================
echo.

REM Use venv if it exists (required for TensorFlow / CNN model)
if exist "venv\Scripts\python.exe" (
    echo [OK] Using Python 3.11 virtual environment (TensorFlow enabled)
    set PYTHON=venv\Scripts\python.exe
) else (
    echo [WARN] venv not found. Run setup first or TensorFlow will not be available.
    set PYTHON=python
)

echo.
echo Starting FastAPI server...
echo API available at : http://localhost:8000
echo API Docs         : http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server.
echo.

%PYTHON% -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
pause

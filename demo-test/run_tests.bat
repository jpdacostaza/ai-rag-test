@echo off
echo ================================================
echo 🧪 Backend Demo Test Suite - Windows Launcher
echo ================================================
echo.

rem Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo    Please install Python 3.8+ and try again
    pause
    exit /b 1
)

rem Navigate to the backend directory
cd /d "%~dp0\.."

rem Check if backend is running
echo 🔍 Checking if backend is running...
python -c "import requests; requests.get('http://localhost:8001/health/simple', timeout=5)" >nul 2>&1
if errorlevel 1 (
    echo ❌ Backend is not running on http://localhost:8001
    echo    Please start the backend first:
    echo    uvicorn app:app --host 0.0.0.0 --port 8001
    echo.
    pause
    exit /b 1
)

echo ✅ Backend is running!
echo.

rem Run the interactive test setup
python demo-test/setup_and_run.py

pause

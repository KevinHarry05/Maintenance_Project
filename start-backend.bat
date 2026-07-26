@echo off
REM SBMS Backend Startup Script for Windows
REM This script starts the FastAPI backend server

title SBMS Backend Server
echo.
echo ========================================
echo     SBMS Backend Startup Script
echo ========================================
echo.

REM Check if we're in the backend directory
if not exist "app\main.py" (
    echo.
    echo ERROR: app\main.py not found!
    echo Please run this script from the backend directory:
    echo   cd backend
    echo   start-backend.bat
    echo.
    pause
    exit /b 1
)

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: Python is not installed or not in PATH!
    echo Please install Python 3.10+ from https://www.python.org/
    echo.
    pause
    exit /b 1
)

echo ✓ Python found
python --version

REM Check if venv exists
if not exist "venv" (
    echo.
    echo Creating Python virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo.
        echo ERROR: Failed to create virtual environment!
        echo.
        pause
        exit /b 1
    )
    echo ✓ Virtual environment created
    
    echo.
    echo Installing dependencies (this may take 2-3 minutes)...
    call venv\Scripts\activate.bat
    pip install --upgrade pip >nul 2>&1
    pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo ERROR: Failed to install dependencies!
        echo.
        pause
        exit /b 1
    )
    echo ✓ Dependencies installed
)

REM Activate virtual environment
echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo ✓ Virtual environment activated

REM Check if .env exists
if not exist ".env" (
    echo.
    echo WARNING: .env file not found!
    echo Creating .env from .env.example...
    if exist ".env.example" (
        copy .env.example .env >nul
        echo ✓ .env created (please update with your configuration)
    ) else (
        echo ERROR: .env.example not found!
        echo.
        pause
        exit /b 1
    )
)

REM Check if database URL is configured
findstr /M "DATABASE_URL" .env >nul 2>&1
if errorlevel 1 (
    echo.
    echo WARNING: DATABASE_URL not configured in .env!
    echo Please edit .env and set:
    echo   DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/sbms_db
    echo.
)

REM Start the backend server
echo.
echo ========================================
echo     Starting Backend Server...
echo ========================================
echo.
echo FastAPI will be available at:
echo   http://localhost:8000
echo.
echo API Documentation:
echo   http://localhost:8000/docs
echo   http://localhost:8000/redoc
echo.
echo Press Ctrl+C to stop the server
echo.

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

REM If uvicorn fails
if errorlevel 1 (
    echo.
    echo ERROR: Failed to start backend server!
    echo.
    echo Troubleshooting:
    echo - Check that PostgreSQL is running
    echo - Check that DATABASE_URL in .env is correct
    echo - Check that port 8000 is not in use
    echo.
    pause
    exit /b 1
)
